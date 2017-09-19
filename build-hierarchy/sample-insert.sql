SELECT * FROM concept WHERE concept_id < 0 AND concept_code = '00000020';
SELECT * FROM concept WHERE concept_id < 0 AND concept_code = '00000008';
SELECT * FROM concept WHERE concept_id < 0 AND concept_code = '0008150';
select * from concept WHERE concept_id IN (-7999628, -7999757, -7999945);

INSERT INTO public.concept_relationship (concept_id_1, concept_id_2, relationship_id, valid_start_date, valid_end_date)
VALUES (-7999628,-7999757,'Is a', '1970-01-01', '2099-12-31');
INSERT INTO public.concept_relationship (concept_id_1, concept_id_2, relationship_id, valid_start_date, valid_end_date)
VALUES (-7999757,-7999628,'Subsumes', '1970-01-01', '2099-12-31');
INSERT INTO public.concept_relationship (concept_id_1, concept_id_2, relationship_id, valid_start_date, valid_end_date)
VALUES (-7999757,-7999945,'Is a', '1970-01-01', '2099-12-31');
INSERT INTO public.concept_relationship (concept_id_1, concept_id_2, relationship_id, valid_start_date, valid_end_date)
VALUES (-7999945,-7999757,'Subsumes', '1970-01-01', '2099-12-31');

INSERT INTO public.concept_ancestor(ancestor_concept_id, descendant_concept_id, min_levels_of_separation, max_levels_of_separation)
VALUES (-7999757, -7999628, 1, 1);
INSERT INTO public.concept_ancestor(ancestor_concept_id, descendant_concept_id, min_levels_of_separation, max_levels_of_separation)
VALUES (-7999945, -7999757, 1, 1);

UPDATE concept SET standard_concept = 'S' WHERE concept_id IN (-7999628, -7999757, -7999945);
UPDATE concept SET invalid_reason = '' WHERE concept_id IN (-7999628, -7999757, -7999945);

/* undo standard concept update */
UPDATE concept SET standard_concept = '' WHERE concept_id IN (-7999628, -7999757, -7999945);

/*DELETE FROM concept WHERE concept_id IN (-7999628, -7999757, -7999945);
DELETE FROM concept_relationship WHERE concept_id_1 IN (-7999628, -7999757, -7999945);
DELETE FROM concept_ancestor WHERE ancestor_concept_id IN (-7999628, -7999757, -7999945);*/