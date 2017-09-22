DELETE FROM public.concept WHERE concept_id BETWEEN -9999999 AND -7000000;
DELETE FROM public.vocabulary WHERE vocabulary_concept_id BETWEEN -9999999 AND -7000000;
DELETE FROM public.domain WHERE domain_concept_id BETWEEN -9999999 AND -7000000;
DELETE FROM public.concept_class WHERE concept_class_concept_id BETWEEN -9999999 AND -7000000;
DELETE FROM public.concept_relationship WHERE (concept_id_1 BETWEEN -9999999 AND -7000000) AND (concept_id_2 BETWEEN -9999999 AND -7000000);
DELETE FROM public.concept_ancestor WHERE (ancestor_concept_id BETWEEN -9999999 AND -7000000) AND (descendant_concept_id BETWEEN -9999999 AND -7000000);