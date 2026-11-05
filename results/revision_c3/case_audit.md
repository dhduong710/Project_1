# Comment 3 — illustrative path audits

Post-hoc descriptive examples: choose two lowest, one median, one highest original-fuzzy length-3 path retention per dataset, with distinct query IDs. Selection uses this declared structural criterion, not generated accuracy or biological plausibility. Ties use original row index. These are not expert-validated mechanisms.

## primekg — row 20 (lowest)

Query: **trichinosis**. Source occurrences/unique: 60/42; matched budget: 33.

Original fuzzy retains 0/22 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

None in this query.

**Lost examples:**

- Undirected walk: trichinosis → Methylprednisolone → autoimmune disease → Triamcinolone. Original directed edges: Methylprednisolone --[indication]→ trichinosis; Triamcinolone --[indication]→ autoimmune disease; autoimmune disease --[indication]→ Methylprednisolone

- Undirected walk: trichinosis → Methylprednisolone → autoimmune disease → Triamcinolone. Original directed edges: Triamcinolone --[indication]→ autoimmune disease; autoimmune disease --[indication]→ Methylprednisolone; trichinosis --[indication]→ Methylprednisolone

- Undirected walk: trichinosis → Methylprednisolone → autoimmune disease → Prednisolone. Original directed edges: Methylprednisolone --[indication]→ trichinosis; autoimmune disease --[indication]→ Methylprednisolone; Prednisolone --[indication]→ autoimmune disease

## primekg — row 30 (second_lowest)

Query: **Addison disease**. Source occurrences/unique: 57/41; matched budget: 31.

Original fuzzy retains 0/12 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

None in this query.

**Lost examples:**

- Undirected walk: Addison disease → Methylprednisolone → seborrheic dermatitis → Fusidic acid. Original directed edges: Methylprednisolone --[indication]→ Addison disease; Fusidic acid --[indication]→ seborrheic dermatitis; seborrheic dermatitis --[indication]→ Methylprednisolone

- Undirected walk: Addison disease → Methylprednisolone → seborrheic dermatitis → Fusidic acid. Original directed edges: Fusidic acid --[indication]→ seborrheic dermatitis; seborrheic dermatitis --[indication]→ Methylprednisolone; Addison disease --[indication]→ Methylprednisolone

- Undirected walk: Addison disease → Methylprednisolone → humoral hypercalcemia of malignancy → Prednisone. Original directed edges: Methylprednisolone --[indication]→ Addison disease; Prednisone --[indication]→ humoral hypercalcemia of malignancy; humoral hypercalcemia of malignancy --[indication]→ Methylprednisolone

## primekg — row 262 (median)

Query: **malaria**. Source occurrences/unique: 59/37; matched budget: 32.

Original fuzzy retains 15/18 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

- Undirected walk: malaria → Chloroquine → rheumatoid arthritis → Cortisone acetate. Original directed edges: rheumatoid arthritis --[indication]→ Chloroquine; Chloroquine --[indication]→ malaria; Cortisone acetate --[indication]→ rheumatoid arthritis

- Undirected walk: malaria → Chloroquine → rheumatoid arthritis → Methylprednisolone. Original directed edges: rheumatoid arthritis --[indication]→ Chloroquine; Chloroquine --[indication]→ malaria; Methylprednisolone --[indication]→ rheumatoid arthritis

- Undirected walk: malaria → Chloroquine → rheumatoid arthritis → Hydrocortisone. Original directed edges: rheumatoid arthritis --[indication]→ Chloroquine; Chloroquine --[indication]→ malaria; Hydrocortisone --[indication]→ rheumatoid arthritis

**Lost examples:**

- Undirected walk: malaria → Sulfisoxazole → urinary tract infection (disease) → Fusidic acid. Original directed edges: Fusidic acid --[indication]→ urinary tract infection (disease); urinary tract infection (disease) --[indication]→ Sulfisoxazole; Sulfisoxazole --[indication]→ malaria

- Undirected walk: malaria → NOS2 → hypertensive disorder → Propranolol. Original directed edges: NOS2 --[associated_with]→ malaria; Propranolol --[indication]→ hypertensive disorder; hypertensive disorder --[associated_with]→ NOS2

- Undirected walk: malaria → CRP → Crohn disease → Desonide. Original directed edges: Desonide --[indication]→ Crohn disease; Crohn disease --[associated_with]→ CRP; CRP --[associated_with]→ malaria

## primekg — row 498 (highest)

Query: **atopic conjunctivitis**. Source occurrences/unique: 52/35; matched budget: 29.

Original fuzzy retains 11/11 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

- Undirected walk: atopic conjunctivitis → Phenyltoloxamine → allergic rhinitis → Triamcinolone. Original directed edges: allergic rhinitis --[indication]→ Phenyltoloxamine; Phenyltoloxamine --[indication]→ atopic conjunctivitis; Triamcinolone --[indication]→ allergic rhinitis

- Undirected walk: atopic conjunctivitis → Phenyltoloxamine → allergic rhinitis → Methylprednisolone. Original directed edges: Methylprednisolone --[indication]→ allergic rhinitis; allergic rhinitis --[indication]→ Phenyltoloxamine; Phenyltoloxamine --[indication]→ atopic conjunctivitis

- Undirected walk: atopic conjunctivitis → Fusidic acid → bronchitis → Tetracycline. Original directed edges: Fusidic acid --[indication]→ atopic conjunctivitis; bronchitis --[indication]→ Fusidic acid; Tetracycline --[indication]→ bronchitis

**Lost examples:**

None in this query.

## pharmkg — row 7 (lowest)

Query: **agoraphobia**. Source occurrences/unique: 100/100; matched budget: 55.

Original fuzzy retains 0/6 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

None in this query.

**Lost examples:**

- Undirected walk: agoraphobia → ketamine → cd4 → iron. Original directed edges: iron --[B]→ cd4; ketamine --[A]→ cd4; ketamine --[Sa]→ agoraphobia

- Undirected walk: agoraphobia → caffeine → metal metabolism inborn errors → prednisone. Original directed edges: caffeine --[T]→ agoraphobia; prednisone --[C]→ metal metabolism inborn errors; caffeine --[T]→ metal metabolism inborn errors

- Undirected walk: agoraphobia → sertraline → nr3c1 → methotrexate. Original directed edges: methotrexate --[A]→ nr3c1; sertraline --[A]→ nr3c1; sertraline --[T]→ agoraphobia

## pharmkg — row 9 (second_lowest)

Query: **alkalosis**. Source occurrences/unique: 100/100; matched budget: 55.

Original fuzzy retains 0/3 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

None in this query.

**Lost examples:**

- Undirected walk: alkalosis → pth → ccl2 → vitamin e. Original directed edges: pth --[P]→ alkalosis; vitamin e --[B]→ ccl2; ccl2 --[E]→ pth

- Undirected walk: alkalosis → nitric oxide → nr3c1 → methotrexate. Original directed edges: nitric oxide --[T]→ alkalosis; methotrexate --[A]→ nr3c1; nitric oxide --[E]→ nr3c1

- Undirected walk: alkalosis → adenosine → gja1 → glutathione. Original directed edges: glutathione --[B]→ gja1; adenosine --[E]→ gja1; adenosine --[Sa]→ alkalosis

## pharmkg — row 312 (median)

Query: **muscular dystrophies**. Source occurrences/unique: 100/100; matched budget: 55.

Original fuzzy retains 0/2 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

None in this query.

**Lost examples:**

- Undirected walk: muscular dystrophies → creatine → ccl2 → vitamin e. Original directed edges: vitamin e --[B]→ ccl2; creatine --[B]→ ccl2; creatine --[T]→ muscular dystrophies

- Undirected walk: muscular dystrophies → oxandrolone → nr3c1 → methotrexate. Original directed edges: oxandrolone --[T]→ muscular dystrophies; methotrexate --[A]→ nr3c1; oxandrolone --[B]→ nr3c1

## pharmkg — row 475 (highest)

Query: **tumor lysis syndrome**. Source occurrences/unique: 100/100; matched budget: 55.

Original fuzzy retains 0/3 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

None in this query.

**Lost examples:**

- Undirected walk: tumor lysis syndrome → docetaxel → esr2 → dopamine. Original directed edges: dopamine --[A]→ esr2; esr2 --[I]→ docetaxel; docetaxel --[T]→ tumor lysis syndrome

- Undirected walk: tumor lysis syndrome → nilotinib → dexamethasone → testosterone. Original directed edges: testosterone --[CC]→ dexamethasone; nilotinib --[T]→ tumor lysis syndrome; dexamethasone --[CC]→ nilotinib

- Undirected walk: tumor lysis syndrome → nilotinib → dexamethasone → metformin. Original directed edges: metformin --[CC]→ dexamethasone; nilotinib --[T]→ tumor lysis syndrome; dexamethasone --[CC]→ nilotinib

## hetionet — row 0 (lowest)

Query: **breast cancer**. Source occurrences/unique: 80/80; matched budget: 44.

Original fuzzy retains 0/11 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

None in this query.

**Lost examples:**

- Undirected walk: breast cancer → Dexamethasone → ABCB11 → Doxorubicin. Original directed edges: Dexamethasone --[CpD]→ breast cancer; Doxorubicin --[CbG]→ ABCB11; Dexamethasone --[CbG]→ ABCB11

- Undirected walk: breast cancer → Dexamethasone → CYP2B6 → Doxorubicin. Original directed edges: Dexamethasone --[CpD]→ breast cancer; Doxorubicin --[CbG]→ CYP2B6; Dexamethasone --[CbG]→ CYP2B6

- Undirected walk: breast cancer → Betamethasone → CYP3A4 → Prednisolone. Original directed edges: Betamethasone --[CpD]→ breast cancer; Prednisolone --[CbG]→ CYP3A4; Betamethasone --[CbG]→ CYP3A4

## hetionet — row 1 (second_lowest)

Query: **rheumatoid arthritis**. Source occurrences/unique: 80/80; matched budget: 44.

Original fuzzy retains 0/27 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

None in this query.

**Lost examples:**

- Undirected walk: rheumatoid arthritis → Prednisolone → CYP3A4 → Methylprednisolone. Original directed edges: Prednisolone --[CtD]→ rheumatoid arthritis; Methylprednisolone --[CbG]→ CYP3A4; Prednisolone --[CbG]→ CYP3A4

- Undirected walk: rheumatoid arthritis → Prednisolone → ABCB1 → Methylprednisolone. Original directed edges: Prednisolone --[CtD]→ rheumatoid arthritis; Methylprednisolone --[CbG]→ ABCB1; Prednisolone --[CbG]→ ABCB1

- Undirected walk: rheumatoid arthritis → Triamcinolone → CYP3A4 → Methylprednisolone. Original directed edges: Triamcinolone --[CtD]→ rheumatoid arthritis; Methylprednisolone --[CbG]→ CYP3A4; Triamcinolone --[CbG]→ CYP3A4

## hetionet — row 52 (median)

Query: **atopic dermatitis**. Source occurrences/unique: 80/80; matched budget: 44.

Original fuzzy retains 0/35 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

None in this query.

**Lost examples:**

- Undirected walk: atopic dermatitis → Prednisone → NR3C1 → Methylprednisolone. Original directed edges: Prednisone --[CtD]→ atopic dermatitis; Methylprednisolone --[CbG]→ NR3C1; Prednisone --[CbG]→ NR3C1

- Undirected walk: atopic dermatitis → Prednisone → CYP3A4 → Methylprednisolone. Original directed edges: Prednisone --[CtD]→ atopic dermatitis; Methylprednisolone --[CbG]→ CYP3A4; Prednisone --[CbG]→ CYP3A4

- Undirected walk: atopic dermatitis → Prednisone → ABCB1 → Methylprednisolone. Original directed edges: Prednisone --[CtD]→ atopic dermatitis; Methylprednisolone --[CbG]→ ABCB1; Prednisone --[CbG]→ ABCB1

## hetionet — row 99 (highest)

Query: **hematologic cancer**. Source occurrences/unique: 80/80; matched budget: 44.

Original fuzzy retains 0/23 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

None in this query.

**Lost examples:**

- Undirected walk: hematologic cancer → Prednisolone → CYP3A4 → Methylprednisolone. Original directed edges: Prednisolone --[CtD]→ hematologic cancer; Methylprednisolone --[CbG]→ CYP3A4; Prednisolone --[CbG]→ CYP3A4

- Undirected walk: hematologic cancer → Prednisolone → ABCB1 → Methylprednisolone. Original directed edges: Prednisolone --[CtD]→ hematologic cancer; Methylprednisolone --[CbG]→ ABCB1; Prednisolone --[CbG]→ ABCB1

- Undirected walk: hematologic cancer → Dexamethasone → NR3C1 → Methylprednisolone. Original directed edges: Dexamethasone --[CtD]→ hematologic cancer; Methylprednisolone --[CbG]→ NR3C1; Dexamethasone --[CbG]→ NR3C1

## drkg — row 26 (lowest)

Query: **Disease::MESH:D008088**. Source occurrences/unique: 100/100; matched budget: 55.

Original fuzzy retains 0/7 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

None in this query.

**Lost examples:**

- Undirected walk: Disease::MESH:D008088 → Compound::DB00759 → Gene::213 → Compound::DB00635. Original directed edges: Compound::DB00759 --[DRUGBANK::treats::Compound:Disease]→ Disease::MESH:D008088; Compound::DB00635 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::213; Compound::DB00759 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::213

- Undirected walk: Disease::MESH:D008088 → Compound::DB00759 → Gene::1576 → Compound::DB00635. Original directed edges: Compound::DB00759 --[DRUGBANK::treats::Compound:Disease]→ Disease::MESH:D008088; Compound::DB00635 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1576; Compound::DB00759 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1576

- Undirected walk: Disease::MESH:D008088 → Compound::DB00759 → Gene::1576 → Compound::DB00620. Original directed edges: Compound::DB00759 --[DRUGBANK::treats::Compound:Disease]→ Disease::MESH:D008088; Compound::DB00620 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1576; Compound::DB00759 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1576

## drkg — row 57 (second_lowest)

Query: **Disease::MESH:D005199**. Source occurrences/unique: 100/100; matched budget: 55.

Original fuzzy retains 0/101 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

None in this query.

**Lost examples:**

- Undirected walk: Disease::MESH:D005199 → Compound::DB00635 → Gene::2908 → Compound::DB00860. Original directed edges: Compound::DB00635 --[DRUGBANK::treats::Compound:Disease]→ Disease::MESH:D005199; Gene::2908 --[DGIDB::AGONIST::Gene:Compound]→ Compound::DB00860; Compound::DB00635 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::2908

- Undirected walk: Disease::MESH:D005199 → Compound::DB00635 → Gene::7038 → Compound::DB00860. Original directed edges: Compound::DB00635 --[DRUGBANK::treats::Compound:Disease]→ Disease::MESH:D005199; Gene::7038 --[DGIDB::OTHER::Gene:Compound]→ Compound::DB00860; Gene::7038 --[DGIDB::OTHER::Gene:Compound]→ Compound::DB00635

- Undirected walk: Disease::MESH:D005199 → Compound::DB00635 → Gene::2908 → Compound::DB00860. Original directed edges: Compound::DB00635 --[DRUGBANK::treats::Compound:Disease]→ Disease::MESH:D005199; Gene::2908 --[DGIDB::AGONIST::Gene:Compound]→ Compound::DB00860; Gene::2908 --[DGIDB::AGONIST::Gene:Compound]→ Compound::DB00635

## drkg — row 169 (median)

Query: **Disease::MESH:D002771**. Source occurrences/unique: 100/100; matched budget: 55.

Original fuzzy retains 1/2 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

- Undirected walk: Disease::MESH:D002771 → Compound::DB00759 → Gene::213 → Compound::DB00635. Original directed edges: Compound::DB00759 --[GNBR::T::Compound:Disease]→ Disease::MESH:D002771; Compound::DB00635 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::213; Compound::DB00759 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::213

**Lost examples:**

- Undirected walk: Disease::MESH:D002771 → Compound::DB00759 → Gene::213 → Compound::DB00635. Original directed edges: Compound::DB00759 --[DRUGBANK::treats::Compound:Disease]→ Disease::MESH:D002771; Compound::DB00635 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::213; Compound::DB00759 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::213

## drkg — row 490 (highest)

Query: **Disease::MESH:D011704**. Source occurrences/unique: 100/100; matched budget: 55.

Original fuzzy retains 1/1 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

- Undirected walk: Disease::MESH:D011704 → Compound::DB00759 → Gene::213 → Compound::DB00635. Original directed edges: Compound::DB00759 --[GNBR::T::Compound:Disease]→ Disease::MESH:D011704; Compound::DB00635 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::213; Compound::DB00759 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::213

**Lost examples:**

None in this query.

## repodb — row 0 (lowest)

Query: **Disease::UMLS:C0038013**. Source occurrences/unique: 100/100; matched budget: 55.

Original fuzzy retains 14/119 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

- Undirected walk: Disease::UMLS:C0038013 → Compound::DB01234 → Gene::1244 → Compound::DB02703. Original directed edges: Compound::DB01234 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0038013; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1244; Compound::DB02703 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1244

- Undirected walk: Disease::UMLS:C0038013 → Compound::DB01234 → Gene::1244 → Compound::DB02703. Original directed edges: Compound::DB01234 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0038013; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1244; Compound::DB02703 --[Hetionet::CbG::Compound:Gene]→ Gene::1244

- Undirected walk: Disease::UMLS:C0038013 → Compound::DB01234 → Gene::301 → Compound::DB00860. Original directed edges: Compound::DB01234 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0038013; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::301; Gene::301 --[DGIDB::OTHER::Gene:Compound]→ Compound::DB00860

**Lost examples:**

- Undirected walk: Disease::UMLS:C0038013 → Compound::DB00860 → Gene::301 → Compound::DB01234. Original directed edges: Compound::DB00860 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0038013; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::301; Gene::301 --[DGIDB::OTHER::Gene:Compound]→ Compound::DB00860

- Undirected walk: Disease::UMLS:C0038013 → Compound::DB00860 → Gene::2908 → Compound::DB01234. Original directed edges: Compound::DB00860 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0038013; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::2908; Gene::2908 --[DGIDB::AGONIST::Gene:Compound]→ Compound::DB00860

- Undirected walk: Disease::UMLS:C0038013 → Compound::DB00860 → Gene::2908 → Compound::DB01234. Original directed edges: Compound::DB00860 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0038013; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::2908; Gene::2908 --[DGIDB::OTHER::Gene:Compound]→ Compound::DB00860

## repodb — row 380 (second_lowest)

Query: **Disease::UMLS:C0004096**. Source occurrences/unique: 100/100; matched budget: 55.

Original fuzzy retains 14/119 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

- Undirected walk: Disease::UMLS:C0004096 → Compound::DB01234 → Gene::1244 → Compound::DB02703. Original directed edges: Compound::DB01234 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0004096; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1244; Compound::DB02703 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1244

- Undirected walk: Disease::UMLS:C0004096 → Compound::DB01234 → Gene::1244 → Compound::DB02703. Original directed edges: Compound::DB01234 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0004096; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1244; Compound::DB02703 --[Hetionet::CbG::Compound:Gene]→ Gene::1244

- Undirected walk: Disease::UMLS:C0004096 → Compound::DB01234 → Gene::301 → Compound::DB00860. Original directed edges: Compound::DB01234 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0004096; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::301; Gene::301 --[DGIDB::OTHER::Gene:Compound]→ Compound::DB00860

**Lost examples:**

- Undirected walk: Disease::UMLS:C0004096 → Compound::DB00860 → Gene::301 → Compound::DB01234. Original directed edges: Compound::DB00860 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0004096; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::301; Gene::301 --[DGIDB::OTHER::Gene:Compound]→ Compound::DB00860

- Undirected walk: Disease::UMLS:C0004096 → Compound::DB00860 → Gene::2908 → Compound::DB01234. Original directed edges: Compound::DB00860 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0004096; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::2908; Gene::2908 --[DGIDB::AGONIST::Gene:Compound]→ Compound::DB00860

- Undirected walk: Disease::UMLS:C0004096 → Compound::DB00860 → Gene::2908 → Compound::DB01234. Original directed edges: Compound::DB00860 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0004096; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::2908; Gene::2908 --[DGIDB::OTHER::Gene:Compound]→ Compound::DB00860

## repodb — row 221 (median)

Query: **Disease::UMLS:C0549398**. Source occurrences/unique: 100/100; matched budget: 55.

Original fuzzy retains 18/30 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

- Undirected walk: Disease::UMLS:C0549398 → Compound::DB00860 → Gene::301 → Compound::DB01234. Original directed edges: Compound::DB00860 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0549398; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::301; Gene::301 --[DGIDB::OTHER::Gene:Compound]→ Compound::DB00860

- Undirected walk: Disease::UMLS:C0549398 → Compound::DB00860 → Gene::2908 → Compound::DB01234. Original directed edges: Compound::DB00860 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0549398; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::2908; Gene::2908 --[DGIDB::AGONIST::Gene:Compound]→ Compound::DB00860

- Undirected walk: Disease::UMLS:C0549398 → Compound::DB00860 → Gene::2908 → Compound::DB01234. Original directed edges: Compound::DB00860 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0549398; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::2908; Gene::2908 --[DGIDB::OTHER::Gene:Compound]→ Compound::DB00860

**Lost examples:**

- Undirected walk: Disease::UMLS:C0549398 → Compound::DB02703 → Gene::1565 → Compound::DB01234. Original directed edges: Compound::DB02703 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0549398; Compound::DB02703 --[DRUGBANK::enzyme::Compound:Gene]→ Gene::1565; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1565

- Undirected walk: Disease::UMLS:C0549398 → Compound::DB02703 → Gene::1244 → Compound::DB01234. Original directed edges: Compound::DB02703 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0549398; Compound::DB02703 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1244; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1244

- Undirected walk: Disease::UMLS:C0549398 → Compound::DB02703 → Gene::1244 → Compound::DB01234. Original directed edges: Compound::DB02703 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C0549398; Compound::DB02703 --[Hetionet::CbG::Compound:Gene]→ Gene::1244; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1244

## repodb — row 268 (highest)

Query: **Disease::UMLS:C1112209**. Source occurrences/unique: 100/100; matched budget: 55.

Original fuzzy retains 5/5 exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.

**Retained examples:**

- Undirected walk: Disease::UMLS:C1112209 → Compound::DB02703 → Gene::1244 → Compound::DB01234. Original directed edges: Compound::DB02703 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C1112209; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1244; Compound::DB02703 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1244

- Undirected walk: Disease::UMLS:C1112209 → Compound::DB02703 → Gene::1565 → Compound::DB01234. Original directed edges: Compound::DB02703 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C1112209; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1565; Compound::DB02703 --[DRUGBANK::enzyme::Compound:Gene]→ Gene::1565

- Undirected walk: Disease::UMLS:C1112209 → Compound::DB02703 → Gene::1244 → Compound::DB01234. Original directed edges: Compound::DB02703 --[repoDB::approved_indication::Compound:Disease]→ Disease::UMLS:C1112209; Compound::DB01234 --[bioarx::DrugHumGen:Compound:Gene]→ Gene::1244; Compound::DB02703 --[Hetionet::CbG::Compound:Gene]→ Gene::1244

**Lost examples:**

None in this query.
