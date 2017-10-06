DELETE FROM public.concept WHERE concept_id < 0;
DELETE FROM public.vocabulary WHERE vocabulary_concept_id < 0;
DELETE FROM public.domain WHERE domain_concept_id < 0;
DELETE FROM public.concept_class WHERE concept_class_concept_id < 0;
DELETE FROM public.concept_relationship WHERE (concept_id_1 < 0) OR (concept_id_2 < 0);
DELETE FROM public.concept_ancestor WHERE (ancestor_concept_id < 0) OR (descendant_concept_id < 0);
