import os, sys, csv, copy
from utils import dbOperation as dop
from utils import fileOperation as fop

reload(sys)  
sys.setdefaultencoding('utf8')

DRUG_CSV = 'inputs/drug-list-mapped.csv'
OUTPUT_SQL = 'outputs/drug-concepts-insert.sql'

# concept cache: vocab_id|concept_code|concept_id
C_CACHE = 'cache/cache-concepts-mapping.psv'

# insert for drug concept into concept table
# input: temp concept_id, sql file, cached mapping of concept and id, used set of concept id 
# return: the next available concept id 
def write_concept_insert_sql(temp_concept_id, f, cacheCptDict, cacheCptIds):
    reader = csv.DictReader(fop.utf_8_encoder(open(DRUG_CSV, 'r')))
    next(reader, None) # skip the header
    uniqConcepts = set() # keep unique concepts by concept name and vocabulary id

    domain_id = "Metadata"; concept_class_id = "Domain"
    for row in reader:
        drug_name, concept_name = row["name"].strip(), row["concept name"].strip()
        if drug_name == "" or concept_name == "":
            continue

        # use rxnorm if it's available, RxNorm concept id: 44819104
        if row["RxNorm"].strip() != "":
            vocabulary_id = "RxNorm"
            concept_code = row["RxNorm"].strip()

        # use ndf-rt code when don't have rxnorm, NDFRT: 44819103
        elif row["NDFRT"].strip() != "":
            vocabulary_id = "NDFRT"
            concept_code = row["NDFRT"].strip()

        # use mesh code when don't have rxnorm and ndf-rt, MESH: 44819136
        elif row["MESH"].strip() != "":
            vocabulary_id = "MESH"
            concept_code = row["MESH"].strip()

        cpt_key = vocabulary_id + '|' + concept_code
        
        if cpt_key not in uniqConcepts and row["conceptId"].strip() == "": # concept not in vocab and not duplication, add new
            concept_id = None
            if cpt_key in cacheCptDict: # concept id defined
                concept_id = int(cacheCptDict[cpt_key])
                    
            else: # get next temp concept id
                while str(temp_concept_id) in cacheCptIds: # skip used concept id
                    temp_concept_id += 1

                cacheCptDict[cpt_key] = str(temp_concept_id) # add new concept to cache
                cacheCptIds.add(str(temp_concept_id))

            if not concept_id:
                concept_id = temp_concept_id
                    
            cpt_sql = dop.insert_concept_template(concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, concept_code)
            f.write(cpt_sql + '\n')            
            uniqConcepts.add(cpt_key)
            
    return temp_concept_id + 1


# MAIN ###############################################################################
def write_insert_script():

    # dict {'vocabId|conceptName': conceptId}
    cacheCptDictBefore = fop.readConceptCache(C_CACHE) # read cached concepts
    cacheCptDictAfter = copy.copy(cacheCptDictBefore) # for validate
    cacheCptIds = set(cacheCptDictAfter.values()) # get concept ids that are taken

    print "[INFO] Read (%s) cached concepts from (%s)" % (len(cacheCptDictBefore), C_CACHE)
    
    with open(OUTPUT_SQL, 'w+') as f:
        concept_id = write_concept_insert_sql(-7999999, f, cacheCptDictAfter, cacheCptIds)

    ## VALIDATE ##
    print "[SUMMARY] Added (%s) new concepts, total (%s) concepts are cached" % (len(cacheCptDictAfter)-len(cacheCptDictBefore), len(cacheCptDictAfter))
    print "[VALIDATE] Check if (1) concept id not unique or not negative, (2) any existing term miss in cache file"
    for k, v in cacheCptDictBefore.iteritems():            
        if k not in cacheCptDictAfter or cacheCptDictAfter[k] != v:
            print "[ERROR] concept term (%s) inconsistence" % k

    for k, v in cacheCptDictAfter.iteritems():
        if not int(v) < 0:
            print "[ERROR] concept term (%s) is using positive id (%s)" % (k, v)

    if len(cacheCptDictAfter) != len(set(cacheCptDictAfter.values())):
        print "[ERROR] concept ids are not unique, number of concepts (%s) and number of concept ids (%s)" % (len(cacheCptDictAfter), len(set(cacheCptDictAfter.values())))
    
    fop.writeConceptCache(C_CACHE, cacheCptDictAfter) # write cached concepts
    print "[INFO] Validation done! insert script is available at (%s)" % OUTPUT_SQL
        
def main():    
    write_insert_script()

if __name__ == '__main__':
    main()


