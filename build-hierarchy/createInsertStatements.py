import csv, os
import psycopg2
import datetime

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
## CACHE
################################################################################
# read local cache concept mapping file
# input: cache file path
# return dict {vocabId;conceptName: conceptId}
def readConceptCache(cache_path):
    cacheDict = {}
    if os.path.isfile(cache_path):
        with open(cache_path) as f:
            lines = f.readlines()
            for line in lines:
                if ';' in line:
                    [vocab_id, concept_name, concept_id] = line.strip().split(';')
                    cacheDict[vocab_id + ';' + concept_name] = concept_id

    return cacheDict


# update local cache concept mapping
# input: cache file path
# input: dict {vocabId;conceptName: conceptId}
def writeConceptCache(cache_path, cacheDict):
    with open(cache_path, 'w') as f:
        for cpt_key, concept_id in sorted(cacheDict.iteritems()):
            f.write(cpt_key+';'+str(concept_id)+'\n')        


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

# cache file, line: vocabId;conceptName;conceptId
CACHE = '../cache/cache-concepts-mapping.txt'

# dict {'vocabId;conceptName': conceptId}
cacheNameIdDict = readConceptCache(CACHE) # read cached concepts
cacheConceptIds = set(cacheNameIdDict.values()) # get concept ids that are taken
global_concept_id = -8000000

################################################################################
## BODY
################################################################################

# {'vocab_id;concept_name': concept_id} (changed from {'concept_code': concept_id})
existsNameIdDict = {} 

# populate dictionary with id's that are already in the concept table
with open("output/full-concepts.csv", "rb") as infile_full:
    reader = csv.reader(infile_full) 
    for row in reader:
        vocab, code, name = row[0], row[1], row[2]
        if row != '' and code != '' and name != '':
            exists_concept_id = getExistingConcept(vocab, code)
            if exists_concept_id:
                existsNameIdDict[vocab+";"+name] = exists_concept_id

    
# get concept id for the term (vocabulary, concept name)
# if concept in ohdsi concepts, then use the existing id. else check in cache
# if concept in cache mapping, then use the existing id
# else generate next available negative id
# input: vocabulary, concept name
def getConceptId(vocab, name, global_concept_id):
    key = vocab + ";" + name 

    # use existing concept_id in concept table
    if key in existsNameIdDict:
        return existsNameIdDict[key]
    
    # use existing concept_id in cache
    if key in cacheNameIdDict:
        return int(cacheNameIdDict[key])
        
    else: # get next available concept id
        while str(global_concept_id) in cacheConceptIds:
            global_concept_id += 1
            
        cacheNameIdDict[key] = str(global_concept_id) # add to cache dict            
        cacheConceptIds.add(str(global_concept_id))
        
        return global_concept_id

    
# add new terms (check concept id in cache, assign next available negative id if not exists)
with open("output/new-concepts.csv", "rb") as infile_concepts, open("output/sql/load-concepts.sql", "wb") as outfile_concepts, open("output/new-vocab.csv", "rb") as infile_vocab, open("output/sql/load-vocab-concepts.sql", "wb") as outfile_vocab_concepts, open("output/sql/load-vocab.sql", "wb") as outfile_vocab:
    reader = csv.reader(infile_concepts)
    
    for row in reader:
        if row[0] != '' and row[1] != '' and row[2] != '':
            vocab, code, name = row[0], row[1], row[2]

            # sql escape character for single quote should be a pair of single quotes
            if "'" in name:
                name = name.replace("'", "''")

            concept_id = getConceptId(vocab, name, global_concept_id)                
            out_string = ("INSERT INTO public.concept (concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, concept_code, valid_start_date, valid_end_date) VALUES (%d, \'%s\', \'Metadata\', \'%s\', \'Domain\', \'%s\', \'2000-01-01\', \'2099-02-22\');\n" % (concept_id, name, vocab, code))
            outfile_concepts.write(out_string)

    # print existsNameIdDict
    reader = csv.reader(infile_vocab)
    for row in reader:
        if row:
            vocab = row[0]
            concept_id = getConceptId(vocab, vocab, global_concept_id)
            
            out_string = ("INSERT INTO public.concept (concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, concept_code, valid_start_date, valid_end_date) VALUES (%d, \'%s\', \'Metadata\', \'Vocabulary\', \'Vocabulary\', \'OMOP generated\', \'2000-01-01\', \'2099-02-22\');\n" % (concept_id, vocab))
            outfile_vocab_concepts.write(out_string)
            out_string = ("INSERT INTO public.vocabulary (vocabulary_id, vocabulary_name, vocabulary_reference, vocabulary_version, vocabulary_concept_id) VALUES (\'%s\', \'TODO: http://www.ontobee.org/ontology/%s under \"Description\"\', \'TODO: http://www.ontobee.org/ontology/%s under \"Home\"\', \'%s\', %d);\n" % (vocab, vocab, vocab, datetime.date.today(), concept_id))
            outfile_vocab.write(out_string)
            # IMPORTANT: go to sql/load_vocab.sql and enter missing data marked with "TODO"


with open("output/URI-ancestors.csv", "rb") as infile_ancestors, open("output/sql/load-ancestors-relationships.sql", "wb") as outfile_ancestors, open("output/sql/load-ancestors-hierarchy.sql", "wb") as outfile_a_hierarchy:
    reader = csv.reader(infile_ancestors)
    next(reader, None)
    for row in reader:
        
        idx1 = row[0].rfind('_')
        vocab1, code1 = row[0][0:idx1], row[0][idx1+1:]        
        id1 = getConceptId(vocab1, code1, global_concept_id)
        
        idx2 = row[1].rfind('_')
        vocab2, code2 = row[1][0:idx2], row[1][idx2+1:]
        id2 = getConceptId(vocab2, code2, global_concept_id)
        
        if not id1:
            print("NO CONCEPT ID FOUND FOR CODE: %s" % row[0])
        if not id2:
            print("NO CONCEPT ID FOUND FOR CODE: %s" % row[1])
            
        relId = None
        if row[2] == '44818821':
            relId = "Is a"
        elif row[2] == '44818723':
            relId = "Subsumes"
            
        if id1 and id2:
            out_string = ("INSERT INTO public.concept_relationship (concept_id_1, concept_id_2, relationship_id, valid_start_date, valid_end_date) VALUES (%d, %d, \'%s\', '1970-01-01', '2099-12-31');\n" % (id1, id2, relId))
            outfile_ancestors.write(out_string)
            
            # "subsumes" relationship is a single level of separation for a hierarchical relationship
            if relId == "Subsumes":
                out_string = ("INSERT INTO public.concept_ancestor(ancestor_concept_id, descendant_concept_id, min_levels_of_separation, max_levels_of_separation) VALUES (%d, %d, 1, 1);\n" % (id1, id2))
                outfile_a_hierarchy.write(out_string)

                
with open("output/URI-descendants.csv", "rb") as infile_descendants, open("output/sql/load-descendants.sql", "wb") as outfile_descendants, open("output/sql/load-descendants-hierarchy.sql","wb") as outfile_d_hierarchy:
    reader = csv.reader(infile_descendants)
    next(reader, None)
    for row in reader:
        code1 = row[0].split('_')[-1]
        code2 = row[1].split('_')[-1]
        
        idx1 = row[0].rfind('_')
        vocab1, code1 = row[0][0:idx1], row[0][idx1+1:]
        id1 = getConceptId(vocab1, code1, global_concept_id)
        
        idx2 = row[0].rfind('_')
        vocab2, code2 = row[1][0:idx2], row[1][idx2+1:]
        id2 = getConceptId(vocab2, code2, global_concept_id)
        
        if not id1:
            print("NO CONCEPT ID FOUND FOR CODE: %s" % row[0])
        if not id2:
            print("NO CONCEPT ID FOUND FOR CODE: %s" % row[1])
            
        relId = None
        if row[2] == '44818821':
            relId = "Is a"
        elif row[2] == '44818723':
            relId = "Subsumes"
        if id1 and id2:
            out_string = ("INSERT INTO public.concept_relationship (concept_id_1, concept_id_2, relationship_id, valid_start_date, valid_end_date) VALUES (%d, %d, \'%s\', '1970-01-01', '2099-12-31');\n" % (id1, id2, relId))
            outfile_descendants.write(out_string)
            if relId == "Subsumes":
                out_string = ("INSERT INTO public.concept_ancestor(ancestor_concept_id, descendant_concept_id, min_levels_of_separation, max_levels_of_separation) VALUES (%d, %d, 1, 1);\n" % (id1, id2))
                outfile_d_hierarchy.write(out_string)

# write cached concepts
writeConceptCache(CACHE, cacheNameIdDict) 