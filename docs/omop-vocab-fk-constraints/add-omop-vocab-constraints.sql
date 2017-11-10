ALTER TABLE "public"."vocabulary" ADD CONSTRAINT "xpk_vocabulary" PRIMARY KEY (vocabulary_id);
ALTER TABLE "public"."relationship" ADD CONSTRAINT "xpk_relationship" PRIMARY KEY (relationship_id);
ALTER TABLE "public"."domain" ADD CONSTRAINT "xpk_domain" PRIMARY KEY (domain_id);
ALTER TABLE "public"."concept_relationship" ADD CONSTRAINT "xpk_concept_relationship" PRIMARY KEY (concept_id_1, concept_id_2, relationship_id);
ALTER TABLE "public"."concept_class" ADD CONSTRAINT "xpk_concept_class" PRIMARY KEY (concept_class_id);
ALTER TABLE "public"."concept_ancestor" ADD CONSTRAINT "xpk_concept_ancestor" PRIMARY KEY (ancestor_concept_id, descendant_concept_id);
ALTER TABLE "public"."concept" ADD CONSTRAINT "xpk_concept" PRIMARY KEY (concept_id);
ALTER TABLE "public"."vocabulary" ADD CONSTRAINT "fpk_vocabulary_concept" FOREIGN KEY (vocabulary_concept_id) REFERENCES concept(concept_id);
ALTER TABLE "public"."relationship" ADD CONSTRAINT "fpk_relationship_reverse" FOREIGN KEY (reverse_relationship_id) REFERENCES relationship(relationship_id);
ALTER TABLE "public"."relationship" ADD CONSTRAINT "fpk_relationship_concept" FOREIGN KEY (relationship_concept_id) REFERENCES concept(concept_id);
ALTER TABLE "public"."domain" ADD CONSTRAINT "fpk_domain_concept" FOREIGN KEY (domain_concept_id) REFERENCES concept(concept_id);
ALTER TABLE "public"."concept_relationship" ADD CONSTRAINT "fpk_concept_relationship_id" FOREIGN KEY (relationship_id) REFERENCES relationship(relationship_id);
ALTER TABLE "public"."concept_relationship" ADD CONSTRAINT "fpk_concept_relationship_c_2" FOREIGN KEY (concept_id_2) REFERENCES concept(concept_id);
ALTER TABLE "public"."concept_relationship" ADD CONSTRAINT "fpk_concept_relationship_c_1" FOREIGN KEY (concept_id_1) REFERENCES concept(concept_id);
ALTER TABLE "public"."concept_class" ADD CONSTRAINT "fpk_concept_class_concept" FOREIGN KEY (concept_class_concept_id) REFERENCES concept(concept_id);
ALTER TABLE "public"."concept_ancestor" ADD CONSTRAINT "fpk_concept_ancestor_concept_2" FOREIGN KEY (descendant_concept_id) REFERENCES concept(concept_id);
ALTER TABLE "public"."concept_ancestor" ADD CONSTRAINT "fpk_concept_ancestor_concept_1" FOREIGN KEY (ancestor_concept_id) REFERENCES concept(concept_id);
ALTER TABLE "public"."concept" ADD CONSTRAINT "fpk_concept_vocabulary" FOREIGN KEY (vocabulary_id) REFERENCES vocabulary(vocabulary_id);
ALTER TABLE "public"."concept" ADD CONSTRAINT "fpk_concept_domain" FOREIGN KEY (domain_id) REFERENCES domain(domain_id);
ALTER TABLE "public"."concept" ADD CONSTRAINT "fpk_concept_class" FOREIGN KEY (concept_class_id) REFERENCES concept_class(concept_class_id);
