import csv, os
import psycopg2
import datetime

import sys
sys.path.insert(0,'..')
from utils import fileOperation as fop

################################################################################
## METHODS
################################################################################

def connect_postgres(hostname, username, password, database):
    conn = psycopg2.connect(host=hostname, user=username, password=password, dbname=database)    
    print("Postgres connection created")    
    return conn

def getExistingConcept(vocab, code):
    q = '''
    SELECT concept_id
    FROM public.concept
    WHERE vocabulary_id = '%s'
    AND concept_code = '%s'
    ''' % (vocab, code)
    curs.execute(q)
    returnId = curs.fetchall()
    if len(returnId) == 0:
        return None
    else:
        return returnId[0][0]

################################################################################
## GLOBAL VARIABLES
################################################################################

## Postgres Connection
hostname = "localhost"
username = "dikb"
password = "dikb"
# dbname = "laertes_cdm"
dbname = "dikb"

conn = connect_postgres(hostname, username, password, dbname)
curs = conn.cursor()

# concept cache: vocab_id|concept_code|concept_id
# vocabulary cache: vocab_id|concept_name|concept_id
C_CACHE = '../cache/cache-concepts-mapping.psv' 
V_CACHE = '../cache/cache-vocabulary-mapping.psv' 

# dict {'vocabId;conceptName': conceptId}
cacheCptDict = fop.readConceptCache(C_CACHE) # read cached concepts
cacheVocabDict = fop.readConceptCache(V_CACHE) # read cached vocabulary

cacheCptIds = set(cacheCptDict.values()) # get concept ids that are taken
cacheVocabIds = set(cacheVocabDict.values())

# V_CONCEPT_ID_BEGIN, C_CONCEPT_ID_BEGIN = -8999999, -7999999
global global_v_id, global_c_id
global_v_id, global_c_id = -8999999, -7999999

print "[INFO] Read (%s) cached concepts from (%s)" % (len(cacheCptDict), C_CACHE)
print "[INFO] Read (%s) cached vocabulary from (%s)" % (len(cacheVocabDict), V_CACHE)

################################################################################
## BODY
################################################################################

# {'vocab_id;concept_name': concept_id} (changed from {'concept_code': concept_id})
existsNameIdDict = {} 

def initConceptMapFromDB():
    # populate dictionary with id's that are already in the concept table
    with open("output/full-concepts.csv", "rb") as infile_full:
        reader = csv.reader(infile_full) 
        for row in reader:
            vocab, code, name = row[0], row[1], row[2]
            if row != '' and code != '' and name != '':
                exists_concept_id = getExistingConcept(vocab, code)
                if exists_concept_id:
                    existsNameIdDict[vocab+"|"+code] = exists_concept_id

    
# get concept id for the concept
# if concept in ohdsi concepts, then use the existing id. else check in cache
# if concept in cache mapping, then use the existing id
# else generate next available negative id
# input: vocabulary, concept name
def getConceptId(vocab, code):
    global global_c_id    
    key = vocab + "|" + code 

    # use existing concept_id in concept table
    if key in existsNameIdDict:
        return existsNameIdDict[key]
    
    # use existing concept_id in cache
    if key in cacheCptDict:
        return int(cacheCptDict[key])
        
    else: # get next available concept id
        while str(global_c_id) in cacheCptIds:
            global_c_id += 1
            
        cacheCptDict[key] = str(global_c_id) # add to cache dict            
        cacheCptIds.add(str(global_c_id))
        
        return global_c_id

    
# get concept id for the vocabulary
def getVocabConceptId(vocab, name):
    global global_v_id    
    key = vocab + "|" + name 

    # # use existing concept_id in concept table
    # if key in existsNameIdDict:
    #     return existsNameIdDict[key]
    
    # use existing concept_id in cache
    if key in cacheVocabDict:
        return int(cacheVocabDict[key])
        
    else: # get next available concept id
        while str(global_v_id) in cacheVocabIds:
            global_v_id += 1
            
        cacheVocabDict[key] = str(global_v_id) # add to cache dict            
        cacheVocabIds.add(str(global_v_id))
        
        return global_v_id
    
def createInsertStatements():
    # add new terms (check concept id in cache, assign next available negative id if not exists)
    usedId = [] 
    # logging used ID's to address a corner case of concept code BFO_0000040 (concept ID -7993832):
    # this appears in full_concepts.csv as "material_entity" and "material entity"
    
    with open("output/new-concepts.csv", "rb") as infile_concepts, open("output/sql/load-concepts.sql", "wb") as outfile_concepts, open("output/sql/load-concepts-ATLAS.sql", "wb") as outfile_concepts_ATLAS, open("output/new-vocab.csv", "rb") as infile_vocab, open("output/sql/load-vocab-concepts.sql", "wb") as outfile_vocab_concepts, open("output/sql/load-vocab.sql", "wb") as outfile_vocab:
        reader = csv.reader(infile_concepts)

        for row in reader:
            if row[0] != '' and row[1] != '' and row[2] != '':
                vocab, code, name = row[0], row[1], row[2]

                # sql escape character for single quote should be a pair of single quotes
                if "'" in name:
                    name = name.replace("'", "''")

                concept_id = getConceptId(vocab, code)     
                if name != 'None' and concept_id not in usedId:           
                    out_string = ("INSERT INTO public.concept (concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, concept_code, valid_start_date, valid_end_date) VALUES (%d, LEFT(\'%s\',255), \'Metadata\', \'%s\', \'Domain\', \'%s\', \'2000-01-01\', \'2099-02-22\');\n" % (concept_id, name, vocab, code))
                    outfile_concepts.write(out_string)
                    usedId.append(concept_id)
                    out_string_ATLAS = ("INSERT INTO public.concept (concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, concept_code, valid_start_date, valid_end_date) VALUES (%d, LEFT(\'%s\',255), \'Metadata\', \'SNOMED\', \'Clinical Finding\', \'%s\', \'2000-01-01\', \'2099-02-22\');\n" % (concept_id, name, code))
                    outfile_concepts_ATLAS.write(out_string_ATLAS)
                elif name == 'None':
                    print "ATTN: Could not insert concept code %s_%s -- No concept name available" % (vocab, code)
                elif concept_id in usedId:
                    print "ATTN: Could not insert concept code %s_%s -- Concept ID already used" % (vocab, code)

        # print existsNameIdDict
        reader = csv.reader(infile_vocab)
        for row in reader:
            if row:
                vocab = row[0]
                concept_id = getVocabConceptId(vocab, vocab)
            
                out_string = ("INSERT INTO public.concept (concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, concept_code, valid_start_date, valid_end_date) VALUES (%d, LEFT(\'%s\',255), \'Metadata\', \'Vocabulary\', \'Vocabulary\', \'OMOP generated\', \'2000-01-01\', \'2099-02-22\');\n" % (concept_id, vocab))
                outfile_vocab_concepts.write(out_string)
                usedId.append(concept_id)
                out_string = ("INSERT INTO public.vocabulary (vocabulary_id, vocabulary_name, vocabulary_reference, vocabulary_version, vocabulary_concept_id) VALUES (\'%s\', LEFT('TODO: http://www.ontobee.org/ontology/%s under \"Description\"', 255), \'TODO: http://www.ontobee.org/ontology/%s under \"Home\"\', \'%s\', %d);\n" % (vocab, vocab, vocab, datetime.date.today(), concept_id))
                outfile_vocab.write(out_string)
                # IMPORTANT: go to sql/load_vocab.sql and enter missing data marked with "TODO"

    with open("output/URI-relationships.csv", "rb") as infile_relationships, open("output/sql/load-relationships.sql", "wb") as outfile_relationships, open("output/sql/load-ancestors.sql", "wb") as outfile_ancestors:
        reader = csv.reader(infile_relationships)
        next(reader, None)
        for row in reader:
        
            idx1 = row[0].rfind('_')
            vocab1, code1 = row[0][0:idx1], row[0][idx1+1:]        
            id1 = getConceptId(vocab1, code1)
        
            idx2 = row[1].rfind('_')
            vocab2, code2 = row[1][0:idx2], row[1][idx2+1:]
            id2 = getConceptId(vocab2, code2)
        
            if not id1:
                print "NO CONCEPT ID FOUND FOR CODE: %s" % row[0]
            if not id2:
                print "NO CONCEPT ID FOUND FOR CODE: %s" % row[1]
            
            relId = None
            if row[2] == '44818821':
                relId = "Is a"
            elif row[2] == '44818723':
                relId = "Subsumes"
            
            if id1 and id2:
                out_string = ("INSERT INTO public.concept_relationship (concept_id_1, concept_id_2, relationship_id, valid_start_date, valid_end_date) VALUES (%d, %d, \'%s\', '1970-01-01', '2099-12-31');\n" % (id1, id2, relId))
                outfile_relationships.write(out_string)
                # catch id1 and id2 that are not in usedId
                if id1 not in usedId:
                    print "ATTN: concept ID %d has no insert into concept table" % id1
                if id2 not in usedId:
                    print "ATTN: concept ID %d has no insert into concept table" % id2
                if relId == "Subsumes":
                    out_string = ("INSERT INTO public.concept_ancestor(ancestor_concept_id, descendant_concept_id, min_levels_of_separation, max_levels_of_separation) VALUES (%d, %d, 1, 1);\n" % (id1, id2))
                    outfile_ancestors.write(out_string)

def main():

    initConceptMapFromDB()
    
    # write cached concepts and vocabulary
    fop.writeConceptCache(C_CACHE, cacheCptDict) # write cached concepts
    fop.writeConceptCache(V_CACHE, cacheVocabDict) # write cached vocabulary

    createInsertStatements()

if __name__ == '__main__':
    main()

