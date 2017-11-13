This repository for adding concept terms into OHDSI vocabulary. The concept id for new concept will be negative in range (-7999999, -7000000). The concept id for new vocabulary will be in range (-8999999, -8000000) 

New concepts comes from drug entities in Potential drug drug interaction (PDDI) evidence base and DIDEO ontology (https://github.com/DIDEO/DIDEO)

-----------------------------------------------------------------------------
Directory
-----------------------------------------------------------------------------

(1) cache/

cache-concepts-mapping.psv
save/update identified concepts in pipe separate file: vocabulary|concept_code|concept_id

cache-vocabulary-mapping.psv
save/update identified vocabulary in pipe separate file: vocabulary|concept_name|concept_id

(2) design/

diagrams for relational database schema

(3) inputs/

data sources for generate script that have sql insert statements

(4) outputs/

sql script with insert statements

(5) db-schema

sql statements for create database  with evidence base tables, ohdsi concept tables


-----------------------------------------------------------------------------
Load customized concepts in OMOP vocab 
-----------------------------------------------------------------------------

PostgreSQL execute sql scripts in the following order

Example:
$ psql -U username -d database -a -f sqlfilepath

(1) drop fk constraints

docs/omop-vocab-fk-constraints/add-omop-vocab-constraints.sql

(2) drop negative concepts in omop vocab tables

outputs/clean-new-concepts.sql

(3) load DIDEO concepts

outputs/dideo-concepts-insert.sql

(4) load drug concepts from evidence base 

outputs/drug-concepts-insert.sql

(5) load drug relationships

build-hierarchy/output/sql/load-vocab-concepts.sql
build-hierarchy/output/sql/load-vocab.sql
build-hierarchy/output/sql/load-concepts.sql

build-hierarchy/output/sql/load-relationships.sql
build-hierarchy/output/sql/load-ancestors.sql

(6) recreate fk constraints

docs/omop-vocab-fk-constraints/drop-omop-vocab-constraints.sql

-----------------------------------------------------------------------------
generate sql script for insert dideo terms into OHDSI vocabulary
-----------------------------------------------------------------------------

Input: inputs/4bb83833.csv
Download as csv from dideo terms serach portal
https://owl2tl.com/4bb83833

Run:
$ python generateDideoConceptsInsertSQL.py

Output:
SQL script that can be executed for adding concept to OHDSI vocabulary
outputs/dideo-concepts-insert.sql

Results:
By 09/18/2017
insert 402 new concepts

-----------------------------------------------------------------------------
generate sql script for insert drug concepts into OHDSI vocabulary
-----------------------------------------------------------------------------

Input: inputs/drug-list-mapped.csv (from manually mapping)

Run:
$ python generateDrugConceptsInsertSQL.py

Output:
SQL script that can be executed for adding concept to OHDSI vocabulary
outputs/drug-concepts-insert.sql

Results:
By 07/31/2017
insert 46 new concepts

-----------------------------------------------------------------------------
Notes
-----------------------------------------------------------------------------

Both generateDideoConceptsInsertSQL.py and generateDrugConceptsInsertSQL.py

Create/update local cached concept id mapping for ensuring the same concept always take the same unique concept id
cache/cache-concepts-mapping.txt

This script:
(1) Reads cache file 'cache/cache-concepts-mapping.txt' for existing terms

(2) When generate concept insert sql script, use same negative concept id if exists in mapping file. Otherwise, make one from -8000000 and update mapping in memory

(3) Update local cache file for all newly created terms

-----------------------------------------------------------------------------
query postgreSQL database mpevidence to get distinct list of qualifier names
-----------------------------------------------------------------------------

mpevidence database ER:
https://github.com/dbmi-pitt/ohdsi-concepts-insert/blob/master/design/MP-evidence-ER.jpeg

Run: $ python generateQualifierList.py > outputs/qualifier-list.txt
Output: qualifier name, source URL, text quote


-----------------------------------------------------------------------------
notes
-----------------------------------------------------------------------------
Apply ontologies in data translation

(1) Apply DIDEO ontology 

#1 Load dideo.owl to OWL2TL to produce term lists in dideo ontology

OWL2TL: https://owl2tl.com/
DIDEO OWL: http://purl.obolibrary.org/obo/dideo.owl

#2 Terms been used in Micropublication annotation

Refers to: outputs/customized-uris.txt

Script for inserting dideo concepts: outputs/dideo-concepts-insert.sql

(2) Apply OMOP standard vocabulary Version 5.1 to MP tables 

#1 create concept tables and load data (refers to OHDSI OMOP CDM V5.1)

http://www.ohdsi.org/web/wiki/doku.php?id=documentation:cdm:single-page

#2 Queries for mapping (MeSH to concept_id and RxNorm to concept_id)

SELECT c.concept_id as omopid, c.concept_name, c.vocabulary_id, cc.concept_class_name, c.concept_code
FROM concept c JOIN concept_class cc on c.concept_class_id = cc.concept_class_id
WHERE c.vocabulary_id = 'MeSH' OR c.vocabulary_id = 'RxNorm'
LIMIT 100;