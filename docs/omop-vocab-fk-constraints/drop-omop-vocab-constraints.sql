ALTER TABLE "concept" DROP CONSTRAINT "fpk_concept_class";
ALTER TABLE "concept" DROP CONSTRAINT "fpk_concept_domain";
ALTER TABLE "concept" DROP CONSTRAINT "fpk_concept_vocabulary";
ALTER TABLE "concept_ancestor" DROP CONSTRAINT "fpk_concept_ancestor_concept_1";
ALTER TABLE "concept_ancestor" DROP CONSTRAINT "fpk_concept_ancestor_concept_2";
ALTER TABLE "concept_class" DROP CONSTRAINT "fpk_concept_class_concept";
ALTER TABLE "concept_relationship" DROP CONSTRAINT "fpk_concept_relationship_c_1";
ALTER TABLE "concept_relationship" DROP CONSTRAINT "fpk_concept_relationship_c_2";
ALTER TABLE "concept_relationship" DROP CONSTRAINT "fpk_concept_relationship_id";
ALTER TABLE "domain" DROP CONSTRAINT "fpk_domain_concept";
ALTER TABLE "relationship" DROP CONSTRAINT "fpk_relationship_concept";
ALTER TABLE "relationship" DROP CONSTRAINT "fpk_relationship_reverse";
ALTER TABLE "vocabulary" DROP CONSTRAINT "fpk_vocabulary_concept";
ALTER TABLE "concept" DROP CONSTRAINT "xpk_concept";
ALTER TABLE "concept_ancestor" DROP CONSTRAINT "xpk_concept_ancestor";
ALTER TABLE "concept_class" DROP CONSTRAINT "xpk_concept_class";
ALTER TABLE "concept_relationship" DROP CONSTRAINT "xpk_concept_relationship";
ALTER TABLE "domain" DROP CONSTRAINT "xpk_domain";
ALTER TABLE "relationship" DROP CONSTRAINT "xpk_relationship";
ALTER TABLE "vocabulary" DROP CONSTRAINT "xpk_vocabulary";
