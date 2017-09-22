select * from concept where concept_id in (9999018, 9999019);

INSERT INTO public.concept (concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, concept_code, valid_start_date, valid_end_date) 
VALUES (9999018, 'NAD(P)', 'Metadata', 'CHEBI', 'Domain', '25524', '2000-01-01', '2099-02-22');
INSERT INTO public.concept (concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, concept_code, valid_start_date, valid_end_date) 
VALUES (9999019, 'nicotinamide dinucleotide', 'Metadata', 'CHEBI', 'Domain', '37007', '2000-01-01', '2099-02-22');

INSERT INTO public.concept_relationship (concept_id_1, concept_id_2, relationship_id, valid_start_date, valid_end_date) 
VALUES (9999018, 9999019, 'Is a', '1970-01-01', '2099-12-31');
INSERT INTO public.concept_relationship (concept_id_1, concept_id_2, relationship_id, valid_start_date, valid_end_date) 
VALUES (9999019, 9999018, 'Subsumes', '1970-01-01', '2099-12-31');

INSERT INTO public.concept_ancestor(ancestor_concept_id, descendant_concept_id, min_levels_of_separation, max_levels_of_separation) 
VALUES (9999019, 9999018, 1, 1);

UPDATE concept SET standard_concept = 'S' WHERE concept_id IN (9999019, 9999018);

DELETE FROM concept WHERE concept_id IN (9999018, 9999019);
DELETE FROM concept_relationship WHERE concept_id_1 IN (9999018, 9999019);
DELETE FROM concept_ancestor WHERE ancestor_concept_id IN (9999018, 9999019);