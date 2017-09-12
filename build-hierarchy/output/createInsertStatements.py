import csv

idDict = {}

with open("new-concepts.csv", "rb") as infile_concepts, open("load-concepts.sql", "wb") as outfile_concepts, open("new-vocab.csv", "rb") as infile_vocab, open("load-vocab.sql", "wb") as outfile_vocab:
    reader = csv.reader(infile_concepts)
    # the current minimum concept ID is 9999000
    newId = -9999001
    for row in reader:
        if row[0] != '' and row[1] != '' and row[2] != '':
            name = row[2]
            if "'" in row[2]:
                name = name.replace("'", "''")
                # sql escape character for single quote should be a pair of single quotes
            out_string = ("INSERT INTO public.concept (concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, concept_code, valid_start_date, valid_end_date) VALUES (%d, \'%s\', \'Metadata\', \'%s\', \'Domain\', %s, \'2000-01-01\', \'2099-02-22\';\n" % (newId, name, row[0], row[1]))
            outfile_concepts.write(out_string)
            idDict[row[1]] = newId
            newId -= 1
    # new vocabularies need to go into both vocabulary and concept table
    # EXAMPLE:
    # INSERT INTO public.vocabulary (vocabulary_id, vocabulary_name, vocabulary_reference, vocabulary_version, vocabulary_concept_id) VALUES ('DIDEO', 'The Potential Drug-drug Interaction and Potential Drug-drug Interaction Evidence Ontology', 'https://github.com/DIDEO/DIDEO', 'release 2016-10-20', -9999000);

with open("URI-ancestors.csv", "rb") as infile_ancestors, open("load-ancestors.sql", "wb") as outfile_ancestors:
    reader = csv.reader(infile_ancestors)
    next(reader, None)
    for row in reader:
        code1 = row[1].split('_')[-1]
        code2 = row[2].split('_')[-1]
        # TODO need to fill out dictionary with terms that already have concept ID
        id1 = idDict.get(code1, 999999999999999)
        id2 = idDict.get(code2, 999999999999999)
        relId = None
        if row[2] == '44818821':
            relId = "Is a"
        elif row[2] == '44818723':
            relId = "Subsumes"
        if id1 and id2:
            out_string = ("INSERT INTO public.concept_relationship (concept_id_1, concept_id_2, relationship_id, valid_start_date, valid_end_date) VALUES (%d, %d, \'%s\', '1970-01-01', '2099-12-31')\n" % (id1, id2, relId))
            outfile_ancestors.write(out_string)

    # EXAMPLE:
    # INSERT INTO public.concept_relationship (concept_id_1, concept_id_2, relationship_id, valid_start_date, valid_end_date)
    # VALUES (-7999628,-7999757,'Is a', '1970-01-01', '2099-12-31');
    # INSERT INTO public.concept_relationship (concept_id_1, concept_id_2, relationship_id, valid_start_date, valid_end_date)
    # VALUES (-7999757,-7999628,'Subsumes', '1970-01-01', '2099-12-31');

    # Then load in ancestor form:
    # EXAMPLE: 
    # INSERT INTO public.concept_ancestor(ancestor_concept_id, descendant_concept_id, min_levels_of_separation, max_levels_of_separation)
    # VALUES (-7999757, -7999628, 1, 1);
    # INSERT INTO public.concept_ancestor(ancestor_concept_id, descendant_concept_id, min_levels_of_separation, max_levels_of_separation)
    # VALUES (-7999945, -7999757, 1, 1);

# with open("URI-descendants.csv", "rb") as infile_descendants, open("load-descendants.sql", "wb") as outfile_descendants:
    # reader = csv.reader(infile_descendants)