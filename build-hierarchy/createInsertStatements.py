import csv
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
## GLOBAL VARIABLES
################################################################################

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

idDict = {}
# populate dictionary with id's that are already in the concept table
with open("output/full-concepts.csv", "rb") as infile_full:
    reader = csv.reader(infile_full)
    for row in reader:
        if row != '' and row[1] != '' and row[2] != '':
            existingId = getExistingConcept(row[0], row[1])
            # print existingId
            if existingId:
                idDict[row[1]] = existingId
    print idDict

# add new terms
with open("output/new-concepts.csv", "rb") as infile_concepts, open("output/sql/load-concepts.sql", "wb") as outfile_concepts, open("output/new-vocab.csv", "rb") as infile_vocab, open("output/sql/load-vocab-concepts.sql", "wb") as outfile_vocab_concepts, open("output/sql/load-vocab.sql", "wb") as outfile_vocab:
    reader = csv.reader(infile_concepts)
    # the current minimum concept ID is 9999000
    newId = -9999001
    for row in reader:
        if row[0] != '' and row[1] != '' and row[2] != '':
            name = row[2]
            if "'" in row[2]:
                name = name.replace("'", "''")
                # sql escape character for single quote should be a pair of single quotes
            out_string = ("INSERT INTO public.concept (concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, concept_code, valid_start_date, valid_end_date) VALUES (%d, \'%s\', \'Metadata\', \'%s\', \'Domain\', \'%s\', \'2000-01-01\', \'2099-02-22\');\n" % (newId, name, row[0], row[1]))
            outfile_concepts.write(out_string)
            if row[1] not in idDict:
                idDict[row[1]] = newId
            newId -= 1
    print idDict
    reader = csv.reader(infile_vocab)
    for row in reader:
        if row:
            out_string = ("INSERT INTO public.concept (concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, concept_code, valid_start_date, valid_end_date) VALUES (%d, \'%s\', \'Metadata\', \'Vocabulary\', \'Vocabulary\', \'OMOP generated\', \'2000-01-01\', \'2099-02-22\');\n" % (newId, row[0]))
            outfile_vocab_concepts.write(out_string)
            out_string = ("INSERT INTO public.vocabulary (vocabulary_id, vocabulary_name, vocabulary_reference, vocabulary_version, vocabulary_concept_id) VALUES (\'%s\', \'TODO: http://www.ontobee.org/ontology/%s under \"Description\"\', \'TODO: http://www.ontobee.org/ontology/%s under \"Home\"\', \'%s\', %d);\n" % (row[0], row[0], row[0], datetime.date.today(), newId))
            outfile_vocab.write(out_string)
            # IMPORTANT: go to sql/load_vocab.sql and enter missing data marked with "TODO"


with open("output/URI-ancestors.csv", "rb") as infile_ancestors, open("output/sql/load-ancestors-relationships.sql", "wb") as outfile_ancestors, open("output/sql/load-ancestors-hierarchy.sql", "wb") as outfile_a_hierarchy:
    reader = csv.reader(infile_ancestors)
    next(reader, None)
    for row in reader:
        code1 = row[0].split('_')[-1]
        code2 = row[1].split('_')[-1]
        id1 = idDict.get(code1, None)
        id2 = idDict.get(code2, None)
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
        id1 = idDict.get(code1, None)
        id2 = idDict.get(code2, None)
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
