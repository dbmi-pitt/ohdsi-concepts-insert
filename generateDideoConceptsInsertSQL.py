import os, sys, csv, copy
from utils import dbOperation as dop
from utils import fileOperation as fop

reload(sys)  
sys.setdefaultencoding('utf8')

DIDEO_CSV = 'inputs/4bb83833.csv'
OUTPUT_SQL = 'outputs/dideo-concepts-insert.sql'

# concept cache: vocab_id|concept_code|concept_id
# vocabulary cache: vocab_id|concept_name|concept_id
C_CACHE = 'cache/cache-concepts-mapping.psv'
V_CACHE = 'cache/cache-vocabulary-mapping.psv'

# vocabulary table insert for dideo and term URI namespaces
# return: the next available concept id 
def write_vocabulary_insert_sql(temp_concept_id, f, cacheVocabDict, cacheVocabIds):
    
    cpt_sql = dop.insert_concept_template(-9999000, 'The Potential Drug-drug Interaction and Potential Drug-drug Interaction Evidence Ontology', 'Metadata', 'Vocabulary', 'Vocabulary', 'OMOP generated', cacheVocabDict)
    vcb_sql = dop.insert_vocabulary_template('DIDEO', 'The Potential Drug-drug Interaction and Potential Drug-drug Interaction Evidence Ontology', 'https://github.com/DIDEO/DIDEO', 'release 2016-10-20', -9999000)
    f.write(cpt_sql + '\n')
    f.write(vcb_sql + '\n')

    vocabL = ['OAE', 'NCBITaxon', 'IDO', 'ERO', 'PR', 'CHMO', 'OBI', 'GO', 'DRON', 'APOLLO_SV', 'UBERON', 'CLO', 'CL', 'GO#GO', 'OGMS', 'EFO', 'STATO', 'FMA', 'CHEBI', 'MOP', 'UO', 'INO', 'PDRO.owl#PDRO']

    for vocab in vocabL:
        concept_id = None        
        v_key = 'Vocabulary|'+ vocab # reuse concept_id for vocabulary
        
        if v_key in cacheVocabDict:
            concept_id = int(cacheVocabDict[v_key])
        else:
            while str(temp_concept_id) in cacheVocabIds: # skip used concept id
                temp_concept_id += 1
                
            cacheVocabDict[v_key] = str(temp_concept_id) # cache new vocab 
            cacheVocabIds.add(str(temp_concept_id))
            concept_id = temp_concept_id
        
        cpt_sql1 = dop.insert_concept_template(concept_id, vocab, 'Metadata', 'Vocabulary', 'Vocabulary', 'OMOP generated', cacheVocabDict)
        vcb_sql1 = dop.insert_vocabulary_template(vocab, vocab, '', 'release 2016-10-20', concept_id)
        
        f.write(cpt_sql1 + '\n')
        f.write(vcb_sql1 + '\n')

    return temp_concept_id + 1


# concept table insert for dideo terms
# return: the next available concept id 
def write_concept_insert_sql(temp_concept_id, f, cacheCptDict, cacheCptIds):
    reader = csv.DictReader(fop.utf_8_encoder(open(DIDEO_CSV, 'r')))
    next(reader, None) # skip the header

    domain_id = "Metadata"; concept_class_id = "Domain"
    for row in reader:
        uri = row["uri"].split('/')[-1]
        idx = uri.rfind('_')
        vocabulary_id, concept_code = uri[:idx], uri[idx+1:]
        concept_name, synonyms = row["term"], row["alternative term"]
        concept_id = None

        cpt_key = vocabulary_id + '|' + concept_code
        if cpt_key in cacheCptDict: # concept id defined
            concept_id = int(cacheCptDict[cpt_key])
            
        else:
            while str(temp_concept_id) in cacheCptIds: # skip used concept id
                temp_concept_id += 1
                
            cacheCptDict[cpt_key] = str(temp_concept_id) # add new concept to cache
            cacheCptIds.add(str(temp_concept_id)) # this concept id is taken
            concept_id = temp_concept_id                

        cpt_sql = dop.insert_concept_template(concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, concept_code, cacheCptDict)
        f.write(cpt_sql + '\n')
        
    return temp_concept_id + 1


# domain table insert
# return: the next available concept id 
def write_domain_insert_sql(f, cacheCptDict):
    cpt_sql = dop.insert_concept_template(-9900000, 'Potential drug interactions of natural product drug interactions', 'Metadata', 'Domain', 'Domain', 'OMOP generated', cacheCptDict)
    dm_sql = dop.insert_domain_template('PDDI or NPDI', 'PDDI or NPDI',  -9900000)
    f.write(cpt_sql + '\n')
    f.write(dm_sql + '\n')
    

# concept class insert
def write_concept_class_insert_sql(f, cacheCptDict):
    cpt_sql = dop.insert_concept_template(-9990000, 'PDDI or NPDI Test Class', 'Metadata', 'Concept Class', 'Concept Class', 'OMOP generated', cacheCptDict)    
    class_sql = dop.insert_concept_class_template('PDDI or NPDI Class', 'PDDI or NPDI Test Class', -9990000)
    f.write(cpt_sql + '\n')
    f.write(class_sql + '\n')
    

# MAIN ###############################################################################
def write_insert_script():

    # dict {'vocabId|conceptName': conceptId}
    cacheCptDictBefore = fop.readConceptCache(C_CACHE) # read cached concepts
    cacheCptDictAfter = copy.copy(cacheCptDictBefore) # for validate
    cacheCptIds = set(cacheCptDictAfter.values()) # get concept ids that are taken

    cacheVocabDict = fop.readVocabCache(V_CACHE) # read cached vocabs
    cacheVocabIds = set(cacheVocabDict.values()) # get concept ids that are taken

    print "[INFO] Read (%s) cached concepts from (%s)" % (len(cacheCptDictBefore), C_CACHE)
    print "[INFO] Read (%s) cached vocabulary from (%s)" % (len(cacheVocabDict), V_CACHE)
    
    with open(OUTPUT_SQL, 'w+') as f:
    
        # templated inserting statements
        write_domain_insert_sql(f, cacheCptDictAfter)
        write_concept_class_insert_sql(f, cacheCptDictAfter)

        concept_id = -8000000 # add new terms
        concept_id = write_vocabulary_insert_sql(concept_id, f, cacheVocabDict, cacheVocabIds)
        concept_id = write_concept_insert_sql(concept_id, f, cacheCptDictAfter, cacheCptIds)

    ## VALIDATE ##
    print "[SUMMARY] Added (%s) new concepts, total (%s) concepts are cached" % (len(cacheCptDictAfter)-len(cacheCptDictBefore), len(cacheCptDictAfter))
    print "[VALIDATE] Check if <1> concept id not unique or not negative, <2> any exists term missing"
    for k, v in cacheCptDictBefore.iteritems():            
        if k not in cacheCptDictAfter or cacheCptDictAfter[k] != v:
            print "[ERROR] concept term (%s) inconsistence" % k

    for k, v in cacheCptDictAfter.iteritems():
        if not int(v) < 0:
            print "[ERROR] concept term (%s) is using positive id (%s)" % (k, v)

    if len(cacheCptDictAfter) != len(set(cacheCptDictAfter.values())):
        print "[ERROR] concept ids are not unique, number of concepts (%s) and number of concept ids (%s)" % (len(cacheCptDictAfter), len(set(cacheCptDictAfter.values())))
    
    fop.writeConceptCache(C_CACHE, cacheCptDictAfter) # write cached concepts
    fop.writeConceptCache(V_CACHE, cacheVocabDict) # write cached vocabulary
    print "[INFO] Validation done! insert script is available at (%s)" % OUTPUT_SQL
        
        
def main():    
    write_insert_script()

if __name__ == '__main__':
    main()


