# Reviewer 1 — Comment 2: response draft

This is an insertion draft, not an update of the original response DOCX. Insert the final supplementary section/table numbers after integrating the accompanying methods and result tables. The claims below refer to the new standardized experiment, not a replacement of historical manuscript numbers.

**Proposed response**

We thank the reviewer for identifying the dependence on dataset-specific manual coefficients. We agree that evaluation on several datasets alone does not establish that these coefficients generalize. We therefore conducted a dedicated calibration and transfer study across PrimeKG, PharmKG, Hetionet, DRKG, and repoDB.

First, we evaluated a declared validation-only search over 224 configurations per dataset for the outer coefficients of the original support formula. This automates coefficient selection while retaining the original dataset-specific evidence definitions. Second, we introduced a complementary linear calibration baseline with five shared structural features. Its coefficients are fitted using a pairwise logistic objective, with regularization selected by query-group cross-validation within the validation split. We included an equal-weight baseline with exactly the same features, an unconstrained model, and feature ablations to distinguish the contribution of coefficient learning from that of the feature definitions.

Third, we evaluated leave-one-dataset-out coefficient transfer, excluding target validation labels from fitting and hyperparameter selection, together with all 20 directed source-to-target transfers. Calibration-label learning curves and coefficient perturbations assess dependence on the available calibration data and the chosen coefficient values. Candidate membership is fixed in every comparison, and missing gold candidates receive zero reciprocal rank.

Fourth, we evaluated automatic edge-coefficient selection using 12 predefined coefficient vectors per dataset, selected by validation generated-answer accuracy with adjusted MRR as a secondary criterion. Candidate order and each query's edge budget are held fixed. A corresponding source-only selection is also evaluated. Frozen-checkpoint inference separates candidate-order interventions from graph-selection interventions and reports generated-answer accuracy, invalid outputs, and adjusted MRR separately.

The results support automatic calibration as an alternative to manual coefficient specification, but do not show uniform superiority of learning. For example, test candidate MRR on repoDB increases from 0.057366 with equal shared-feature weights to 0.064902 with learned weights; the paired query-cluster bootstrap interval for the difference is [0.000402, 0.015176]. On DRKG, equal shared-feature weights achieve a slightly higher candidate MRR than learned weights (0.061426 versus 0.060496). Consequently, we do not attribute all improvements over the original method to coefficient learning. Improvements in candidate ranking also do not consistently translate into improved generated-answer accuracy.

The edge-weight study has a further limitation: all 12 tested vectors tie on the validation selection metrics for Hetionet and DRKG. Under the corrected precision policy, the numbers tied at the best validation score are 6, 2, 12, 12, and 1 on PrimeKG, PharmKG, Hetionet, DRKG, and repoDB, respectively. These observations do not identify a uniquely optimal edge weighting or establish equivalence outside the tested settings. We explicitly retain such null results and report the selected vectors and full search traces.

During the information-retention analysis we detected nonfinite FP16 graph outputs. We consequently repeated the complete Comment 2 GPU protocol with graph weights loaded directly in FP32 and LLM weights in BF16, including every validation trial and the subsequent automatic/source-only selections before test inference. The CPU candidate-calibration artifacts are unchanged. Archived FP16 outputs are retained only for audit, and the updated tables consistently use the stable precision policy. Additional fixed-old-coefficient diagnostics distinguish the effect of changing precision from the effect of validation reselection; we do not attribute all changed answers solely to FP16 overflow.

The corrected validation search changes automatic edge selections on PharmKG and repoDB and source-only edge selections on all five datasets. On repoDB, the newly selected edge-LODO vector yields 0.2% exact accuracy, compared with 0.4% for original fuzzy, shared fixed, and shared auto. This supersedes the earlier statement that all four compressed variants have identical exact accuracy on every dataset and reinforces the need to report transfer limitations.

Finally, this study assesses transfer of calibration coefficients within the existing benchmark pipelines. The target structural retriever and graph remain available, and the edge-transfer experiment inherits the original fuzzy candidate order and budgets. It is therefore not evidence of zero-shot completion on an unseen KG or of a pipeline entirely free from historical target-dataset calibration. The new analyses narrow the generalization claim and provide a reproducible calibration procedure; joint end-to-end learning of the graph selector remains a separate extension.

**Integration checklist**

- Insert `supplementary_methods.tex` and `supplementary_results.tex` into the supplementary source with final table labels.
- Add a concise automatic-calibration paragraph and the main candidate/transfer result to the manuscript; retain the exact-answer limitations.
- Refer to `../../results/revision_c2/exports/REPORT.md` for complete metrics and `../../scripts/revision_c2/README.md` for reproducibility.
- Reconcile the existing manuscript's metric definitions with the newly standardized evaluation before replacing any historical E2E number.
- Use `e2e_stable/` and the regenerated exports; `e2e/` and `legacy_fp16_snapshot/` preserve superseded FP16 results, not current revision evidence.
- The intervals are exploratory, not corrected for multiple comparisons. Do not turn this response into a claim of universal or statistically proven improvement.
