import re, string
import codecs
from SPARQLWrapper import SPARQLWrapper, JSON
import pickle
import sys, os
import fileinput
import glob
import csv
import psycopg2

################################################################################
## METHODS
################################################################################

def connect_postgres(hostname, username, password, database):
    conn = psycopg2.connect(host=hostname, user=username, password=password, dbname=database)    
    print("Postgres connection created")    
    return conn

# when querying ancestors / descendants sometimes the concept name is not returned
def getName(uri, sparql):
    fullUri = 'http://purl.obolibrary.org/obo/' + uri
    q = '''
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?s ?label WHERE {
        ?s rdfs:label ?label
        FILTER (?s = <%s>)
    }
    ''' % (fullUri)
    if DEBUG:
        print q
    sparql.setQuery(q)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for r in results['results']['bindings']:
        if r.has_key('s') and r.has_key('label'):
            return unicode(r['label']['value'])
        else:
            if DEBUG: 
                print "ATTN: no name found for label: %s\n" % fullUri
            return None

def getAncestors(vocab, uri, name, sparql):
    vocabUri = 'http://purl.obolibrary.org/obo/merged/' + vocab
    fullUri = 'http://purl.obolibrary.org/obo/' + uri
    q = '''
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?path ?label ?link FROM <%s> WHERE {
        {
            SELECT ?s ?o ?label WHERE {
                {
                    ?s rdfs:subClassOf ?o .
                    FILTER (isIRI(?o)).
                    OPTIONAL {?o rdfs:label ?label}
                } UNION {
                    ?s owl:equivalentClass ?s1 .
                    ?s1 owl:intersectionOf ?s2 .
                    ?s2 rdf:first ?o  .
                    FILTER (isIRI(?o))
                    OPTIONAL {?o rdfs:label ?label}
                }
                FILTER ( ?s != ?o )
            }
        }
        OPTION (TRANSITIVE, t_in(?s), t_out(?o), t_step (?s) as ?link, t_step ('path_id') as ?path).
        FILTER (isIRI(?o)).
        FILTER (?s= <%s>)
    } ORDER BY DESC (?path)
    ''' % (vocabUri, fullUri)
    if DEBUG:
        print q
    sparql.setQuery(q)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    if len(results['results']['bindings']) == 0:
        print "ATTN: no ANCESTOR query results for label: %s\n" % name
        return {}

    ancestors = {}

    n = 1
    maxPath = 0
    for r in results['results']['bindings']:
        if r.has_key('path') and int(r['path']['value']) >= maxPath:
            maxPath = int(r['path']['value'])
            if r.has_key('link'):
                ancestors[n] = {}
                ancestors[n]['uri'] = unicode(r['link']['value']).split('/')[-1]
                # corner case is ERO_0001213_ where it has a trailing underscore
                if ancestors[n]['uri'][-1] == '_':
                    ancestors[n]['uri'] = ancestors[n]['uri'][:-1]
                if r.has_key('label'):
                    ancestors[n]['name'] = unicode(r['label']['value'])
                else:
                    ancestors[n]['name'] = getName(uri, sparql)
                    if DEBUG:
                        print "Ancestor query gave no name for uri %s. Queried for name then returned %s." % (uri, ancestors[n]['name'])
                n += 1

    if DEBUG:
        print "ANCESTORS OF %s\n" % name
        print ancestors
        print "\n"
    return ancestors

def getDescendants(vocab, uri, name, sparql):
    vocabUri = 'http://purl.obolibrary.org/obo/merged/' + vocab
    fullUri = 'http://purl.obolibrary.org/obo/' + uri
    q = '''
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?label ?term FROM <%s> WHERE {
        {
            ?term rdfs:subClassOf ?s .
            FILTER (?s = <%s>)
            FILTER (isIRI(?term)).
            OPTIONAL {?term rdfs:label ?label} .
            OPTIONAL {?subTerm rdfs:subClassOf ?term}
        }
    }
    ''' % (vocabUri, fullUri)
    if DEBUG:
        print q
    sparql.setQuery(q)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    if len(results['results']['bindings']) == 0:
        print "ATTN: no DESCENDANT query results for label: %s\n" % name
        return {}

    descendants = {}

    n = 1
    for r in results['results']['bindings']:
        if r.has_key('term'):
            descendants[n] = {} 
            descendants[n]['uri'] = unicode(r['term']['value']).split('/')[-1]
            # corner case is ERO_0001213_ where it has a trailing underscore
            if descendants[n]['uri'][-1] == '_':
                descendants[n]['uri'] = descendants[n]['uri'][:-1]
            if r.has_key('label'):
                descendants[n]['name'] = unicode(r['label']['value'])
            # if DEBUG:
            #     print(unicode(r['label']["value"]))
            n += 1

    if DEBUG:
        print "\nDESCENDANTS OF %s\n" % name
        print descendants
        print "\n"
    return descendants

def findNewConcepts(uri, conceptList):
    code = uri.get('uri').split('_')[-1]
    v = u'_'.join(uri.get('uri').split('_')[:-1]) 
    name = uri.get('name')
    q = '''
    SELECT concept_code, vocabulary_id
    FROM public.concept
    WHERE vocabulary_id = '%s'
    AND concept_code = '%s'
    ''' % (v, code)
    curs.execute(q)
    s = '%s,%s,\"%s\"' % (v, code, name)
    # concept not already in database. Return True
    if len(curs.fetchall()) == 0 and s not in conceptList:
        conceptList.append(s)
        return conceptList
    else:
        return conceptList

def findNewVocab(uri, vocabList):
    v = u'_'.join(uri.split('_')[:-1]) 
    q = '''
    SELECT vocabulary_id 
    FROM public.concept 
    WHERE vocabulary_id = '%s'
    ''' % v
    curs.execute(q)
    # vocab not already in database. Return True
    if len(curs.fetchall()) == 0 and v not in vocabList:
        vocabList.append(v)
        return vocabList
    else:
        return vocabList

def writeRelationships(i, di, rfile, relationshipsAdded, newVocab, newConcepts, fullVocab, fullConcepts):
    if i == 1:
        s1 = uri
        s2 = di.get(i).get('uri')
    elif di == descendants:
        s1 = di.get(i).get('uri')
        s2 = uri
    else:
        s1 = di.get(i-1).get('uri')
        s2 = di.get(i).get('uri')
    if '_' in s1 and '_' in s2:
    # if statement should remove corner cases of 'owl#thing' 'oboInOwl#ObsoleteClass' lines
        STRING_1 = u"%s,%s,44818821\n" % (s1, s2)
        STRING_2 = u"%s,%s,44818723\n" % (s2, s1)
        if STRING_1 not in relationshipsAdded:
            relationshipsAdded.append(STRING_1)
            rfile.write(STRING_1)
        if STRING_2 not in relationshipsAdded:
            relationshipsAdded.append(STRING_2)
            rfile.write(STRING_2)
        newVocab = findNewVocab(di.get(i).get('uri'), newVocab)
        newConcepts = findNewConcepts(di.get(i), newConcepts)
        v = u'_'.join(di.get(i).get('uri').split('_')[:-1])
        code = di.get(i).get('uri').split('_')[-1]
        s = '%s,%s,\"%s\"' % (v, code, di.get(i).get('name'))
        if v not in fullVocab:
            fullVocab.append(v)
        if s not in fullConcepts:
            fullConcepts.append(s)

################################################################################
## GLOBAL VARIABLES
################################################################################

DEBUG = True

SPARQL = SPARQLWrapper("http://sparql.hegroup.org/sparql/")

## Postgres Connection
hostname = "localhost"
username = "dikb"
password = "dikb"
dbname = "laertes_cdm"

conn = connect_postgres(hostname, username, password, dbname)
curs = conn.cursor()

################################################################################
## BODY
################################################################################

with open('URI-list.csv', 'rb') as infile, open('output/URI-relationships.csv', 'wb') as rfile, open('output/new-vocab.csv', 'wb') as vfile, open('output/full-vocab.csv','wb') as fvfile, open('output/new-concepts.csv','wb') as cfile, open('output/full-concepts.csv', 'wb') as fcfile, open('output/empty-queries.txt', 'wb') as logfile:
    reader = csv.reader(infile)
    rfile.write("URI_1,URI_2,relationship_id\n")
    newVocab = []
    newConcepts = []
    fullVocab = []
    fullConcepts = []
    relationshipsAdded = []
    for row in reader:
        name = row[0]
        vocab = row[1]
        uri = row[2]
        if DEBUG:
            print "############################################################"
            print uri
        if '#' in vocab:
            vocab = row[1].split('#')[1]
        if '#' in uri:
            uri = row[2].split('#')[1]

        descendants = getDescendants(vocab, uri, name, SPARQL)
        if not descendants:
            logfile.write("no DESCENDANT query results for label: %s | %s\n" % (name,uri))
        ancestors = getAncestors(vocab, uri, name, SPARQL)
        if not ancestors:
            logfile.write("no ANCESTOR query results for label: %s | %s\n" % (name,uri))
        if not descendants and not ancestors:
            logfile.write("ALERT: no queries returned output for label: %s | %s\n" % (name,uri))

        # WRITE WITH RELATIONSHIP_ID
        # ancestors "subsume" descendants = relationship id 44818723
        # descendant "is a" ancestor = relationship id 44818821
        if ancestors:
            if ancestors.get(1) is not None:
                writeRelationships(1, ancestors, rfile, relationshipsAdded, newVocab, newConcepts, fullVocab, fullConcepts)
            if ancestors.get(2) is not None:
                writeRelationships(2, ancestors, rfile, relationshipsAdded, newVocab, newConcepts, fullVocab, fullConcepts)
            if ancestors.get(3) is not None:
                writeRelationships(3, ancestors, rfile, relationshipsAdded, newVocab, newConcepts, fullVocab, fullConcepts)
            if ancestors.get(4) is not None:
                writeRelationships(4, ancestors, rfile, relationshipsAdded, newVocab, newConcepts, fullVocab, fullConcepts)
            if ancestors.get(5) is not None:
                writeRelationships(5, ancestors, rfile, relationshipsAdded, newVocab, newConcepts, fullVocab, fullConcepts)

        if descendants:
            # since descendants do not seem to have a clear hierarchy, assume that all are equally subsumed by ancestor. Print all, rather than just one.
            for k,v in descendants.iteritems():
                writeRelationships(k, descendants, rfile, relationshipsAdded, newVocab, newConcepts, fullVocab, fullConcepts)

    vfile.write('\n'.join(newVocab))
    cfile.write('\n'.join(newConcepts))
    fvfile.write('\n'.join(fullVocab))
    fcfile.write('\n'.join(fullConcepts))