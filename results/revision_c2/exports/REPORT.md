# Comment 2 — experiment report

CPU status: **complete**. E2E status: **complete**.

Inference precision: **graph encoder float32; LLM bfloat16**. E2E directory: `/home/anhlq/Documents/2026-dhd/SoftFuse-KGC/results/revision_c2/e2e_stable`.

The corrected run repeats every validation trial and freezes new automatic/LODO selections before test inference. CPU ranking/calibration artifacts are unchanged. Archived FP16 results remain in e2e/ and legacy_fp16_snapshot/ for comparison only.

Stable C3 cached predictions are reusable only when the full model/precision/generation fingerprint and exact prompt/candidate/graph key match. No legacy FP16 cache is imported. Precision deltas change both graph and LLM arithmetic; adaptive graph variants may additionally change inputs after validation reselection.

Candidate MRR is not generated-answer accuracy. Native formula replay was checked against original soft-support ordering.

Shared-equal vs shared-learned isolates coefficient learning on the same five topology features. Comparisons to original-soft ALSO change feature definitions.

Shared-LODO excludes target validation labels. The target KG, its structural retriever, and its prepared subgraphs are still available; this is coefficient transfer, not zero-shot KG completion.

All intervals are paired query-cluster bootstrap intervals vs original_soft (candidate tables); exploratory comparisons, no multiplicity adjustment. Intervals crossing zero do not establish improvement.

These are retrospective checks on previously studied benchmark splits; no new prospective test set was created.

## Candidate results

| dataset | variant | gold_at20 | mrr_at20 | hits1 | hits10 | delta_mrr | ci95_low | ci95_high |
|---|---|---|---|---|---|---|---|---|
| primekg | raw | 0.240000 | 0.064563 | 0.024000 | 0.192000 | -0.060763 | -0.077806 | -0.045526 |
| primekg | original_soft | 0.240000 | 0.125326 | 0.072000 | 0.222000 | 0 | 0 | 0 |
| primekg | native_fixed_b050 | 0.240000 | 0.125326 | 0.072000 | 0.222000 | 0 | 0 | 0 |
| primekg | native_valid_grid | 0.240000 | 0.125326 | 0.072000 | 0.222000 | 0 | 0 | 0 |
| primekg | shared_equal | 0.240000 | 0.125188 | 0.072000 | 0.222000 | -0.000138 | -0.000446 | 0.000132 |
| primekg | shared_learned | 0.240000 | 0.125326 | 0.072000 | 0.222000 | 0 | 0 | 0 |
| pharmkg | raw | 0.092000 | 0.020481 | 0.008000 | 0.046000 | -0.007678 | -0.011991 | -0.003960 |
| pharmkg | original_soft | 0.092000 | 0.028159 | 0.012000 | 0.068000 | 0 | 0 | 0 |
| pharmkg | native_fixed_b050 | 0.092000 | 0.028159 | 0.012000 | 0.068000 | 0 | 0 | 0 |
| pharmkg | native_valid_grid | 0.092000 | 0.028159 | 0.012000 | 0.068000 | 0 | 0 | 0 |
| pharmkg | shared_equal | 0.092000 | 0.031883 | 0.016000 | 0.072000 | 0.003724 | -0.001329 | 0.009456 |
| pharmkg | shared_learned | 0.092000 | 0.031876 | 0.016000 | 0.072000 | 0.003716 | -0.001327 | 0.009477 |
| hetionet | raw | 0.440000 | 0.099445 | 0.040000 | 0.220000 | 0.004007 | -0.026481 | 0.039763 |
| hetionet | original_soft | 0.440000 | 0.095439 | 0.010000 | 0.280000 | 0 | 0 | 0 |
| hetionet | native_fixed_b050 | 0.440000 | 0.095439 | 0.010000 | 0.280000 | 0 | 0 | 0 |
| hetionet | native_valid_grid | 0.440000 | 0.095439 | 0.010000 | 0.280000 | 0 | 0 | 0 |
| hetionet | shared_equal | 0.440000 | 0.101269 | 0.030000 | 0.210000 | 0.005830 | -0.027553 | 0.043339 |
| hetionet | shared_learned | 0.440000 | 0.115284 | 0.040000 | 0.260000 | 0.019845 | -0.011858 | 0.056340 |
| drkg | raw | 0.200000 | 0.043242 | 0.010000 | 0.120000 | -0.003314 | -0.007915 | 0.000201 |
| drkg | original_soft | 0.200000 | 0.046556 | 0.014000 | 0.142000 | 0 | 0 | 0 |
| drkg | native_fixed_b050 | 0.200000 | 0.039818 | 0.016000 | 0.120000 | -0.006738 | -0.017205 | 0.004602 |
| drkg | native_valid_grid | 0.200000 | 0.046516 | 0.014000 | 0.136000 | -0.000040 | -0.001234 | 0.001011 |
| drkg | shared_equal | 0.200000 | 0.061426 | 0.032000 | 0.122000 | 0.014870 | 0.004181 | 0.026357 |
| drkg | shared_learned | 0.200000 | 0.060496 | 0.030000 | 0.136000 | 0.013940 | 0.003056 | 0.025973 |
| repodb | raw | 0.214000 | 0.048140 | 0.018000 | 0.128000 | 0.000033 | 0 | 0.000075 |
| repodb | original_soft | 0.214000 | 0.048107 | 0.018000 | 0.128000 | 0 | 0 | 0 |
| repodb | native_fixed_b050 | 0.214000 | 0.027763 | 0.004000 | 0.114000 | -0.020343 | -0.029339 | -0.012510 |
| repodb | native_valid_grid | 0.214000 | 0.048140 | 0.018000 | 0.128000 | 0.000033 | 0 | 0.000075 |
| repodb | shared_equal | 0.214000 | 0.057366 | 0.014000 | 0.126000 | 0.009259 | 0.000860 | 0.017724 |
| repodb | shared_learned | 0.214000 | 0.064902 | 0.018000 | 0.160000 | 0.016795 | 0.011522 | 0.022452 |
| primekg | shared_lodo | 0.240000 | 0.126104 | 0.074000 | 0.220000 | 0.000778 | -0.001127 | 0.003811 |
| pharmkg | shared_lodo | 0.092000 | 0.031860 | 0.016000 | 0.072000 | 0.003701 | -0.001343 | 0.009463 |
| hetionet | shared_lodo | 0.440000 | 0.113579 | 0.040000 | 0.240000 | 0.018141 | -0.013817 | 0.054942 |
| drkg | shared_lodo | 0.200000 | 0.058612 | 0.028000 | 0.128000 | 0.012056 | 0.000227 | 0.024389 |
| repodb | shared_lodo | 0.214000 | 0.064902 | 0.018000 | 0.160000 | 0.016795 | 0.011522 | 0.022452 |

## Learning effect with identical shared features

| dataset | variant | reference | delta_mrr | ci95_low | ci95_high |
|---|---|---|---|---|---|
| primekg | shared_learned | shared_equal | 0.000138 | -0.000132 | 0.000446 |
| primekg | shared_lodo | shared_equal | 0.000916 | -0.000988 | 0.003898 |
| pharmkg | shared_learned | shared_equal | -0.000007 | -0.000067 | 0.000044 |
| pharmkg | shared_lodo | shared_equal | -0.000022 | -0.000088 | 0.000031 |
| hetionet | shared_learned | shared_equal | 0.014015 | -0.007576 | 0.043253 |
| hetionet | shared_lodo | shared_equal | 0.012311 | -0.009688 | 0.042107 |
| drkg | shared_learned | shared_equal | -0.000930 | -0.003807 | 0.001440 |
| drkg | shared_lodo | shared_equal | -0.002814 | -0.008688 | 0.001746 |
| repodb | shared_learned | shared_equal | 0.007536 | 0.000402 | 0.015176 |
| repodb | shared_lodo | shared_equal | 0.007536 | 0.000402 | 0.015176 |

## Transfer matrix (diagonal: within-dataset learned; off-diagonal: source-only coefficients)

| source | primekg | pharmkg | hetionet | drkg | repodb |
|---|---|---|---|---|---|
| primekg | 0.125326 | 0.031860 | 0.114632 | 0.058572 | 0.064803 |
| pharmkg | 0.122438 | 0.031876 | 0.108527 | 0.061996 | 0.063235 |
| hetionet | 0.120787 | 0.031860 | 0.115284 | 0.058488 | 0.064902 |
| drkg | 0.125371 | 0.031876 | 0.104670 | 0.060496 | 0.064237 |
| repodb | 0.121458 | 0.031860 | 0.115423 | 0.058656 | 0.064902 |

## E2E results

| dataset | arm | variant | n | exact_match | invalid | top1_copy | adjusted_rr | exact_delta | exact_ci_low | exact_ci_high |
|---|---|---|---|---|---|---|---|---|---|---|
| primekg | candidate | raw | 500 | 0.002000 | 0.002000 | 0.044000 | 0.047671 | 0 | 0 | 0 |
| primekg | candidate | original_soft | 500 | 0 | 0.002000 | 0.008000 | 0.074676 | -0.002000 | -0.006383 | 0 |
| primekg | candidate | native_valid_grid | 500 | 0 | 0.002000 | 0.008000 | 0.074609 | -0.002000 | -0.006383 | 0 |
| primekg | candidate | shared_equal | 500 | 0 | 0.002000 | 0.012000 | 0.074686 | -0.002000 | -0.006383 | 0 |
| primekg | candidate | shared_learned | 500 | 0 | 0.002000 | 0.008000 | 0.074609 | -0.002000 | -0.006383 | 0 |
| primekg | candidate | shared_lodo | 500 | 0 | 0.002000 | 0.016000 | 0.074775 | -0.002000 | -0.006383 | 0 |
| primekg | graph | source_graph | 500 | 0 | 0.002000 | 0.008000 | 0.074676 | 0 | 0 | 0 |
| primekg | graph | original_fuzzy | 500 | 0 | 0.002000 | 0.010000 | 0.074687 | 0 | 0 | 0 |
| primekg | graph | shared_fixed | 500 | 0 | 0.002000 | 0.010000 | 0.074687 | 0 | 0 | 0 |
| primekg | graph | shared_auto | 500 | 0 | 0.002000 | 0.010000 | 0.074676 | 0 | 0 | 0 |
| primekg | graph | shared_edge_lodo | 500 | 0 | 0.002000 | 0.010000 | 0.074676 | 0 | 0 | 0 |
| pharmkg | candidate | raw | 500 | 0 | 0.478000 | 0.522000 | 0.015575 | 0 | 0 | 0 |
| pharmkg | candidate | original_soft | 500 | 0 | 0.626000 | 0.374000 | 0.020700 | 0 | 0 | 0 |
| pharmkg | candidate | native_valid_grid | 500 | 0 | 0.626000 | 0.374000 | 0.020700 | 0 | 0 | 0 |
| pharmkg | candidate | shared_equal | 500 | 0.002000 | 0.688000 | 0.312000 | 0.022875 | 0.002000 | 0 | 0.006303 |
| pharmkg | candidate | shared_learned | 500 | 0.002000 | 0.692000 | 0.308000 | 0.022872 | 0.002000 | 0 | 0.006303 |
| pharmkg | candidate | shared_lodo | 500 | 0.002000 | 0.696000 | 0.304000 | 0.022859 | 0.002000 | 0 | 0.006303 |
| pharmkg | graph | source_graph | 500 | 0 | 0.626000 | 0.374000 | 0.020700 | 0 | 0 | 0 |
| pharmkg | graph | original_fuzzy | 500 | 0.002000 | 0.590000 | 0.410000 | 0.020971 | 0.002000 | 0 | 0.006356 |
| pharmkg | graph | shared_fixed | 500 | 0.002000 | 0.588000 | 0.412000 | 0.020956 | 0.002000 | 0 | 0.006356 |
| pharmkg | graph | shared_auto | 500 | 0.002000 | 0.584000 | 0.416000 | 0.021317 | 0.002000 | 0 | 0.006356 |
| pharmkg | graph | shared_edge_lodo | 500 | 0.002000 | 0.592000 | 0.408000 | 0.020969 | 0.002000 | 0 | 0.006356 |
| hetionet | candidate | raw | 100 | 0.020000 | 0.020000 | 0.070000 | 0.081921 | 0 | 0 | 0 |
| hetionet | candidate | original_soft | 100 | 0.030000 | 0.020000 | 0 | 0.100087 | 0.010000 | -0.021978 | 0.046302 |
| hetionet | candidate | native_valid_grid | 100 | 0.030000 | 0.020000 | 0 | 0.100087 | 0.010000 | -0.021978 | 0.046302 |
| hetionet | candidate | shared_equal | 100 | 0.010000 | 0.040000 | 0 | 0.078342 | -0.010000 | -0.033616 | 0 |
| hetionet | candidate | shared_learned | 100 | 0.010000 | 0.020000 | 0 | 0.085784 | -0.010000 | -0.033616 | 0 |
| hetionet | candidate | shared_lodo | 100 | 0.020000 | 0.020000 | 0 | 0.091936 | 0 | -0.028044 | 0.029133 |
| hetionet | graph | source_graph | 100 | 0.030000 | 0.020000 | 0 | 0.100087 | 0 | 0 | 0 |
| hetionet | graph | original_fuzzy | 100 | 0.030000 | 0.020000 | 0 | 0.100087 | 0 | 0 | 0 |
| hetionet | graph | shared_fixed | 100 | 0.030000 | 0.020000 | 0 | 0.100087 | 0 | 0 | 0 |
| hetionet | graph | shared_auto | 100 | 0.030000 | 0.020000 | 0 | 0.100087 | 0 | 0 | 0 |
| hetionet | graph | shared_edge_lodo | 100 | 0.030000 | 0.020000 | 0 | 0.100087 | 0 | 0 | 0 |
| drkg | candidate | raw | 500 | 0.010000 | 0 | 0 | 0.040954 | 0 | 0 | 0 |
| drkg | candidate | original_soft | 500 | 0.014000 | 0 | 0 | 0.046285 | 0.004000 | 0 | 0.010246 |
| drkg | candidate | native_valid_grid | 500 | 0.014000 | 0 | 0 | 0.046365 | 0.004000 | 0 | 0.010246 |
| drkg | candidate | shared_equal | 500 | 0.008000 | 0 | 0 | 0.046767 | -0.002000 | -0.006289 | 0 |
| drkg | candidate | shared_learned | 500 | 0.020000 | 0 | 0 | 0.057786 | 0.010000 | -0.001942 | 0.021487 |
| drkg | candidate | shared_lodo | 500 | 0.018000 | 0 | 0 | 0.054981 | 0.008000 | -0.004057 | 0.020330 |
| drkg | graph | source_graph | 500 | 0.014000 | 0 | 0 | 0.046285 | 0 | 0 | 0 |
| drkg | graph | original_fuzzy | 500 | 0.014000 | 0 | 0 | 0.046285 | 0 | 0 | 0 |
| drkg | graph | shared_fixed | 500 | 0.014000 | 0 | 0 | 0.046285 | 0 | 0 | 0 |
| drkg | graph | shared_auto | 500 | 0.014000 | 0 | 0 | 0.046285 | 0 | 0 | 0 |
| drkg | graph | shared_edge_lodo | 500 | 0.014000 | 0 | 0 | 0.046285 | 0 | 0 | 0 |
| repodb | candidate | raw | 500 | 0.002000 | 0 | 0.080000 | 0.036642 | 0 | 0 | 0 |
| repodb | candidate | original_soft | 500 | 0.002000 | 0 | 0.080000 | 0.036623 | 0 | 0 | 0 |
| repodb | candidate | native_valid_grid | 500 | 0.002000 | 0 | 0.080000 | 0.036642 | 0 | 0 | 0 |
| repodb | candidate | shared_equal | 500 | 0.008000 | 0 | 0.016000 | 0.046601 | 0.006000 | -0.002028 | 0.015386 |
| repodb | candidate | shared_learned | 500 | 0 | 0 | 0.080000 | 0.043996 | -0.002000 | -0.006224 | 0 |
| repodb | candidate | shared_lodo | 500 | 0 | 0 | 0.080000 | 0.043996 | -0.002000 | -0.006224 | 0 |
| repodb | graph | source_graph | 500 | 0.002000 | 0 | 0.080000 | 0.036642 | 0 | 0 | 0 |
| repodb | graph | original_fuzzy | 500 | 0.004000 | 0 | 0.036000 | 0.037776 | 0.002000 | 0 | 0.006237 |
| repodb | graph | shared_fixed | 500 | 0.004000 | 0 | 0.036000 | 0.037795 | 0.002000 | 0 | 0.006237 |
| repodb | graph | shared_auto | 500 | 0.004000 | 0 | 0.036000 | 0.038159 | 0.002000 | 0 | 0.006237 |
| repodb | graph | shared_edge_lodo | 500 | 0.002000 | 0 | 0.008000 | 0.036653 | 0 | 0 | 0 |

## Paired E2E comparisons (explicit references)

Candidate comparisons to shared_equal isolate coefficient learning. Graph comparisons to shared_fixed isolate automatic coefficient selection within the same edge selector. Exact-match deltas are fractions, not percentage points.

| dataset | arm | variant | reference | metric | delta_mean | ci95_low | ci95_high |
|---|---|---|---|---|---|---|---|
| primekg | candidate | native_valid_grid | original_soft | exact_match | 0 | 0 | 0 |
| primekg | candidate | native_valid_grid | original_soft | adjusted_rr | -0.000067 | -0.000204 | 0 |
| primekg | candidate | shared_equal | original_soft | exact_match | 0 | 0 | 0 |
| primekg | candidate | shared_equal | original_soft | adjusted_rr | 0.000011 | -0.000219 | 0.000250 |
| primekg | candidate | shared_learned | original_soft | exact_match | 0 | 0 | 0 |
| primekg | candidate | shared_learned | original_soft | adjusted_rr | -0.000067 | -0.000204 | 0 |
| primekg | candidate | shared_lodo | original_soft | exact_match | 0 | 0 | 0 |
| primekg | candidate | shared_lodo | original_soft | adjusted_rr | 0.000100 | -0.000800 | 0.001317 |
| primekg | candidate | shared_learned | shared_equal | exact_match | 0 | 0 | 0 |
| primekg | candidate | shared_learned | shared_equal | adjusted_rr | -0.000077 | -0.000358 | 0.000187 |
| primekg | candidate | shared_lodo | shared_equal | exact_match | 0 | 0 | 0 |
| primekg | candidate | shared_lodo | shared_equal | adjusted_rr | 0.000089 | -0.000800 | 0.001312 |
| primekg | graph | shared_fixed | original_fuzzy | exact_match | 0 | 0 | 0 |
| primekg | graph | shared_fixed | original_fuzzy | adjusted_rr | 0 | 0 | 0 |
| primekg | graph | shared_auto | original_fuzzy | exact_match | 0 | 0 | 0 |
| primekg | graph | shared_auto | original_fuzzy | adjusted_rr | -0.000011 | -0.000034 | 0 |
| primekg | graph | shared_edge_lodo | original_fuzzy | exact_match | 0 | 0 | 0 |
| primekg | graph | shared_edge_lodo | original_fuzzy | adjusted_rr | -0.000011 | -0.000034 | 0 |
| primekg | graph | shared_auto | shared_fixed | exact_match | 0 | 0 | 0 |
| primekg | graph | shared_auto | shared_fixed | adjusted_rr | -0.000011 | -0.000034 | 0 |
| primekg | graph | shared_edge_lodo | shared_fixed | exact_match | 0 | 0 | 0 |
| primekg | graph | shared_edge_lodo | shared_fixed | adjusted_rr | -0.000011 | -0.000034 | 0 |
| pharmkg | candidate | native_valid_grid | original_soft | exact_match | 0 | 0 | 0 |
| pharmkg | candidate | native_valid_grid | original_soft | adjusted_rr | 0 | 0 | 0 |
| pharmkg | candidate | shared_equal | original_soft | exact_match | 0.002000 | 0 | 0.006303 |
| pharmkg | candidate | shared_equal | original_soft | adjusted_rr | 0.002175 | -0.001441 | 0.005972 |
| pharmkg | candidate | shared_learned | original_soft | exact_match | 0.002000 | 0 | 0.006303 |
| pharmkg | candidate | shared_learned | original_soft | adjusted_rr | 0.002172 | -0.001421 | 0.005954 |
| pharmkg | candidate | shared_lodo | original_soft | exact_match | 0.002000 | 0 | 0.006303 |
| pharmkg | candidate | shared_lodo | original_soft | adjusted_rr | 0.002159 | -0.001449 | 0.005941 |
| pharmkg | candidate | shared_learned | shared_equal | exact_match | 0 | 0 | 0 |
| pharmkg | candidate | shared_learned | shared_equal | adjusted_rr | -0.000003 | -0.000055 | 0.000044 |
| pharmkg | candidate | shared_lodo | shared_equal | exact_match | 0 | 0 | 0 |
| pharmkg | candidate | shared_lodo | shared_equal | adjusted_rr | -0.000016 | -0.000071 | 0.000032 |
| pharmkg | graph | shared_fixed | original_fuzzy | exact_match | 0 | 0 | 0 |
| pharmkg | graph | shared_fixed | original_fuzzy | adjusted_rr | -0.000015 | -0.001000 | 0.001002 |
| pharmkg | graph | shared_auto | original_fuzzy | exact_match | 0 | 0 | 0 |
| pharmkg | graph | shared_auto | original_fuzzy | adjusted_rr | 0.000346 | 0 | 0.001089 |
| pharmkg | graph | shared_edge_lodo | original_fuzzy | exact_match | 0 | 0 | 0 |
| pharmkg | graph | shared_edge_lodo | original_fuzzy | adjusted_rr | -0.000002 | -0.000980 | 0.001012 |
| pharmkg | graph | shared_auto | shared_fixed | exact_match | 0 | 0 | 0 |
| pharmkg | graph | shared_auto | shared_fixed | adjusted_rr | 0.000361 | 0 | 0.001089 |
| pharmkg | graph | shared_edge_lodo | shared_fixed | exact_match | 0 | 0 | 0 |
| pharmkg | graph | shared_edge_lodo | shared_fixed | adjusted_rr | 0.000013 | 0 | 0.000041 |
| hetionet | candidate | native_valid_grid | original_soft | exact_match | 0 | 0 | 0 |
| hetionet | candidate | native_valid_grid | original_soft | adjusted_rr | 0 | 0 | 0 |
| hetionet | candidate | shared_equal | original_soft | exact_match | -0.020000 | -0.051546 | 0 |
| hetionet | candidate | shared_equal | original_soft | adjusted_rr | -0.021746 | -0.049643 | 0.001800 |
| hetionet | candidate | shared_learned | original_soft | exact_match | -0.020000 | -0.051546 | 0 |
| hetionet | candidate | shared_learned | original_soft | adjusted_rr | -0.014303 | -0.042177 | 0.010401 |
| hetionet | candidate | shared_lodo | original_soft | exact_match | -0.010000 | -0.031923 | 0 |
| hetionet | candidate | shared_lodo | original_soft | adjusted_rr | -0.008151 | -0.029030 | 0.014124 |
| hetionet | candidate | shared_learned | shared_equal | exact_match | 0 | 0 | 0 |
| hetionet | candidate | shared_learned | shared_equal | adjusted_rr | 0.007443 | -0.001389 | 0.019169 |
| hetionet | candidate | shared_lodo | shared_equal | exact_match | 0.010000 | 0 | 0.035714 |
| hetionet | candidate | shared_lodo | shared_equal | adjusted_rr | 0.013595 | -0.000805 | 0.035463 |
| hetionet | graph | shared_fixed | original_fuzzy | exact_match | 0 | 0 | 0 |
| hetionet | graph | shared_fixed | original_fuzzy | adjusted_rr | 0 | 0 | 0 |
| hetionet | graph | shared_auto | original_fuzzy | exact_match | 0 | 0 | 0 |
| hetionet | graph | shared_auto | original_fuzzy | adjusted_rr | 0 | 0 | 0 |
| hetionet | graph | shared_edge_lodo | original_fuzzy | exact_match | 0 | 0 | 0 |
| hetionet | graph | shared_edge_lodo | original_fuzzy | adjusted_rr | 0 | 0 | 0 |
| hetionet | graph | shared_auto | shared_fixed | exact_match | 0 | 0 | 0 |
| hetionet | graph | shared_auto | shared_fixed | adjusted_rr | 0 | 0 | 0 |
| hetionet | graph | shared_edge_lodo | shared_fixed | exact_match | 0 | 0 | 0 |
| hetionet | graph | shared_edge_lodo | shared_fixed | adjusted_rr | 0 | 0 | 0 |
| drkg | candidate | native_valid_grid | original_soft | exact_match | 0 | 0 | 0 |
| drkg | candidate | native_valid_grid | original_soft | adjusted_rr | 0.000080 | -0.000577 | 0.000702 |
| drkg | candidate | shared_equal | original_soft | exact_match | -0.006000 | -0.013918 | 0 |
| drkg | candidate | shared_equal | original_soft | adjusted_rr | 0.000482 | -0.007988 | 0.007782 |
| drkg | candidate | shared_learned | original_soft | exact_match | 0.006000 | -0.006424 | 0.019048 |
| drkg | candidate | shared_learned | original_soft | adjusted_rr | 0.011501 | -0.001908 | 0.024954 |
| drkg | candidate | shared_lodo | original_soft | exact_match | 0.004000 | -0.009672 | 0.017751 |
| drkg | candidate | shared_lodo | original_soft | adjusted_rr | 0.008696 | -0.004871 | 0.022523 |
| drkg | candidate | shared_learned | shared_equal | exact_match | 0.012000 | 0 | 0.024693 |
| drkg | candidate | shared_learned | shared_equal | adjusted_rr | 0.011019 | -0.000409 | 0.022803 |
| drkg | candidate | shared_lodo | shared_equal | exact_match | 0.010000 | -0.002071 | 0.023304 |
| drkg | candidate | shared_lodo | shared_equal | adjusted_rr | 0.008213 | -0.003931 | 0.020830 |
| drkg | graph | shared_fixed | original_fuzzy | exact_match | 0 | 0 | 0 |
| drkg | graph | shared_fixed | original_fuzzy | adjusted_rr | 0 | 0 | 0 |
| drkg | graph | shared_auto | original_fuzzy | exact_match | 0 | 0 | 0 |
| drkg | graph | shared_auto | original_fuzzy | adjusted_rr | 0 | 0 | 0 |
| drkg | graph | shared_edge_lodo | original_fuzzy | exact_match | 0 | 0 | 0 |
| drkg | graph | shared_edge_lodo | original_fuzzy | adjusted_rr | 0 | 0 | 0 |
| drkg | graph | shared_auto | shared_fixed | exact_match | 0 | 0 | 0 |
| drkg | graph | shared_auto | shared_fixed | adjusted_rr | 0 | 0 | 0 |
| drkg | graph | shared_edge_lodo | shared_fixed | exact_match | 0 | 0 | 0 |
| drkg | graph | shared_edge_lodo | shared_fixed | adjusted_rr | 0 | 0 | 0 |
| repodb | candidate | native_valid_grid | original_soft | exact_match | 0 | 0 | 0 |
| repodb | candidate | native_valid_grid | original_soft | adjusted_rr | 0.000019 | 0 | 0.000048 |
| repodb | candidate | shared_equal | original_soft | exact_match | 0.006000 | -0.002028 | 0.015386 |
| repodb | candidate | shared_equal | original_soft | adjusted_rr | 0.009978 | 0.002508 | 0.017675 |
| repodb | candidate | shared_learned | original_soft | exact_match | -0.002000 | -0.006224 | 0 |
| repodb | candidate | shared_learned | original_soft | adjusted_rr | 0.007373 | 0.002231 | 0.011602 |
| repodb | candidate | shared_lodo | original_soft | exact_match | -0.002000 | -0.006224 | 0 |
| repodb | candidate | shared_lodo | original_soft | adjusted_rr | 0.007373 | 0.002231 | 0.011602 |
| repodb | candidate | shared_learned | shared_equal | exact_match | -0.008000 | -0.017023 | -0.001897 |
| repodb | candidate | shared_learned | shared_equal | adjusted_rr | -0.002605 | -0.009620 | 0.003276 |
| repodb | candidate | shared_lodo | shared_equal | exact_match | -0.008000 | -0.017023 | -0.001897 |
| repodb | candidate | shared_lodo | shared_equal | adjusted_rr | -0.002605 | -0.009620 | 0.003276 |
| repodb | graph | shared_fixed | original_fuzzy | exact_match | 0 | 0 | 0 |
| repodb | graph | shared_fixed | original_fuzzy | adjusted_rr | 0.000019 | 0 | 0.000050 |
| repodb | graph | shared_auto | original_fuzzy | exact_match | 0 | 0 | 0 |
| repodb | graph | shared_auto | original_fuzzy | adjusted_rr | 0.000383 | 0.000098 | 0.000740 |
| repodb | graph | shared_edge_lodo | original_fuzzy | exact_match | -0.002000 | -0.006237 | 0 |
| repodb | graph | shared_edge_lodo | original_fuzzy | adjusted_rr | -0.001123 | -0.004639 | 0.000798 |
| repodb | graph | shared_auto | shared_fixed | exact_match | 0 | 0 | 0 |
| repodb | graph | shared_auto | shared_fixed | adjusted_rr | 0.000363 | 0.000075 | 0.000725 |
| repodb | graph | shared_edge_lodo | shared_fixed | exact_match | -0.002000 | -0.006237 | 0 |
| repodb | graph | shared_edge_lodo | shared_fixed | adjusted_rr | -0.001142 | -0.004675 | 0.000778 |

## Precision repair: validation selections

| dataset | auto_trial_legacy | auto_trial_stable | auto_trial_changed | lodo_trial_legacy | lodo_trial_stable | lodo_trial_changed | legacy_best_ties | stable_best_ties |
|---|---|---|---|---|---|---|---|---|
| primekg | 1 | 1 | False | 0 | 2 | True | 6 | 6 |
| pharmkg | 0 | 3 | True | 7 | 2 | True | 12 | 2 |
| hetionet | 0 | 0 | False | 7 | 2 | True | 12 | 12 |
| drkg | 0 | 0 | False | 7 | 2 | True | 12 | 12 |
| repodb | 0 | 2 | True | 1 | 3 | True | 8 | 1 |

## Precision repair: test differences versus archived FP16

| dataset | arm | variant | changed_predictions | changed_encoder_inputs | exact_match_legacy | exact_match_stable | adjusted_rr_delta | interpretation |
|---|---|---|---|---|---|---|---|---|
| primekg | candidate | raw | 23 | 0 | 0.002000 | 0.002000 | 0.000036 | same inputs, precision policy changed |
| primekg | candidate | original_soft | 18 | 0 | 0 | 0 | 0 | same inputs, precision policy changed |
| primekg | candidate | native_valid_grid | 22 | 0 | 0 | 0 | 0 | same inputs, precision policy changed |
| primekg | candidate | shared_equal | 20 | 0 | 0 | 0 | 0 | same inputs, precision policy changed |
| primekg | candidate | shared_learned | 12 | 0 | 0 | 0 | 0 | same inputs, precision policy changed |
| primekg | candidate | shared_lodo | 14 | 0 | 0 | 0 | 0 | same inputs, precision policy changed |
| primekg | graph | source_graph | 18 | 0 | 0 | 0 | 0 | same inputs, precision policy changed |
| primekg | graph | original_fuzzy | 4 | 0 | 0 | 0 | 0 | same inputs, precision policy changed |
| primekg | graph | shared_fixed | 4 | 0 | 0 | 0 | 0 | same inputs, precision policy changed |
| primekg | graph | shared_auto | 12 | 0 | 0 | 0 | -0.000067 | same inputs, precision policy changed |
| primekg | graph | shared_edge_lodo | 101 | 272 | 0 | 0 | -0.000011 | precision plus validation reselection |
| pharmkg | candidate | raw | 33 | 0 | 0 | 0 | 0 | same inputs, precision policy changed |
| pharmkg | candidate | original_soft | 27 | 0 | 0 | 0 | 0.000113 | same inputs, precision policy changed |
| pharmkg | candidate | native_valid_grid | 27 | 0 | 0 | 0 | 0.000113 | same inputs, precision policy changed |
| pharmkg | candidate | shared_equal | 9 | 0 | 0.002000 | 0.002000 | 0.000067 | same inputs, precision policy changed |
| pharmkg | candidate | shared_learned | 10 | 0 | 0.002000 | 0.002000 | 0.000067 | same inputs, precision policy changed |
| pharmkg | candidate | shared_lodo | 10 | 0 | 0.002000 | 0.002000 | 0.000067 | same inputs, precision policy changed |
| pharmkg | graph | source_graph | 27 | 0 | 0 | 0 | 0.000113 | same inputs, precision policy changed |
| pharmkg | graph | original_fuzzy | 5 | 0 | 0.002000 | 0.002000 | 0 | same inputs, precision policy changed |
| pharmkg | graph | shared_fixed | 10 | 0 | 0.002000 | 0.002000 | -0.000333 | same inputs, precision policy changed |
| pharmkg | graph | shared_auto | 13 | 351 | 0.002000 | 0.002000 | 0.000028 | precision plus validation reselection |
| pharmkg | graph | shared_edge_lodo | 12 | 15 | 0.002000 | 0.002000 | -0.000321 | precision plus validation reselection |
| hetionet | candidate | raw | 5 | 0 | 0.020000 | 0.020000 | 0.000231 | same inputs, precision policy changed |
| hetionet | candidate | original_soft | 0 | 0 | 0.030000 | 0.030000 | 0 | same inputs, precision policy changed |
| hetionet | candidate | native_valid_grid | 0 | 0 | 0.030000 | 0.030000 | 0 | same inputs, precision policy changed |
| hetionet | candidate | shared_equal | 3 | 0 | 0.010000 | 0.010000 | 0 | same inputs, precision policy changed |
| hetionet | candidate | shared_learned | 1 | 0 | 0.010000 | 0.010000 | 0 | same inputs, precision policy changed |
| hetionet | candidate | shared_lodo | 11 | 0 | 0.020000 | 0.020000 | 0 | same inputs, precision policy changed |
| hetionet | graph | source_graph | 0 | 0 | 0.030000 | 0.030000 | 0 | same inputs, precision policy changed |
| hetionet | graph | original_fuzzy | 0 | 0 | 0.030000 | 0.030000 | 0 | same inputs, precision policy changed |
| hetionet | graph | shared_fixed | 0 | 0 | 0.030000 | 0.030000 | 0 | same inputs, precision policy changed |
| hetionet | graph | shared_auto | 0 | 0 | 0.030000 | 0.030000 | 0 | same inputs, precision policy changed |
| hetionet | graph | shared_edge_lodo | 0 | 4 | 0.030000 | 0.030000 | 0 | precision plus validation reselection |
| drkg | candidate | raw | 1 | 0 | 0.010000 | 0.010000 | 0 | same inputs, precision policy changed |
| drkg | candidate | original_soft | 2 | 0 | 0.014000 | 0.014000 | 0 | same inputs, precision policy changed |
| drkg | candidate | native_valid_grid | 1 | 0 | 0.014000 | 0.014000 | 0 | same inputs, precision policy changed |
| drkg | candidate | shared_equal | 2 | 0 | 0.008000 | 0.008000 | 0 | same inputs, precision policy changed |
| drkg | candidate | shared_learned | 1 | 0 | 0.020000 | 0.020000 | 0 | same inputs, precision policy changed |
| drkg | candidate | shared_lodo | 1 | 0 | 0.018000 | 0.018000 | 0 | same inputs, precision policy changed |
| drkg | graph | source_graph | 2 | 0 | 0.014000 | 0.014000 | 0 | same inputs, precision policy changed |
| drkg | graph | original_fuzzy | 0 | 0 | 0.014000 | 0.014000 | 0 | same inputs, precision policy changed |
| drkg | graph | shared_fixed | 0 | 0 | 0.014000 | 0.014000 | 0 | same inputs, precision policy changed |
| drkg | graph | shared_auto | 0 | 0 | 0.014000 | 0.014000 | 0 | same inputs, precision policy changed |
| drkg | graph | shared_edge_lodo | 0 | 126 | 0.014000 | 0.014000 | 0 | precision plus validation reselection |
| repodb | candidate | raw | 7 | 0 | 0.002000 | 0.002000 | 0 | same inputs, precision policy changed |
| repodb | candidate | original_soft | 7 | 0 | 0.002000 | 0.002000 | 0 | same inputs, precision policy changed |
| repodb | candidate | native_valid_grid | 7 | 0 | 0.002000 | 0.002000 | 0 | same inputs, precision policy changed |
| repodb | candidate | shared_equal | 6 | 0 | 0.008000 | 0.008000 | 0 | same inputs, precision policy changed |
| repodb | candidate | shared_learned | 4 | 0 | 0 | 0 | 0 | same inputs, precision policy changed |
| repodb | candidate | shared_lodo | 4 | 0 | 0 | 0 | 0 | same inputs, precision policy changed |
| repodb | graph | source_graph | 7 | 0 | 0.002000 | 0.002000 | 0 | same inputs, precision policy changed |
| repodb | graph | original_fuzzy | 5 | 0 | 0.004000 | 0.004000 | 0 | same inputs, precision policy changed |
| repodb | graph | shared_fixed | 5 | 0 | 0.004000 | 0.004000 | 0 | same inputs, precision policy changed |
| repodb | graph | shared_auto | 80 | 208 | 0.004000 | 0.004000 | 0.000363 | precision plus validation reselection |
| repodb | graph | shared_edge_lodo | 86 | 500 | 0.004000 | 0.002000 | -0.001391 | precision plus validation reselection |

## Encoder precision audit

The workbook contains every legacy/repaired validation and test variant. FP32-to-FP16 overflow is reported separately from encoder FP16 overflow. All rows remain in evaluation denominators.

| dataset | n | fp16_nonfinite | fp32_nonfinite | fp32_to_fp16_nonfinite | fp32_to_bf16_nonfinite | fp32_max_abs |
|---|---|---|---|---|---|---|
| primekg | 500 | 9 | 0 | 6 | 0 | 130444.351562 |
| pharmkg | 500 | 0 | 0 | 0 | 0 | 3.586100 |
| hetionet | 100 | 0 | 0 | 0 | 0 | 4.169904 |
| drkg | 500 | 0 | 0 | 0 | 0 | 19.677286 |
| repodb | 500 | 0 | 0 | 0 | 0 | 7.339898 |

## Adaptive arms: fixed-old-choice precision versus reselection

An additional stable inference diagnostic holds the old selected coefficients fixed. Total metric change is decomposed into the precision-policy change at that fixed choice and the effect of validation reselection under stable precision. Neither term isolates graph arithmetic from LLM arithmetic.

| dataset | variant | metric | legacy_fp16 | legacy_choice_stable | new_choice_stable | precision_at_old_choice | reselection_at_stable_precision | total_change |
|---|---|---|---|---|---|---|---|---|
| primekg | shared_auto | exact_match | 0 | 0 | 0 | 0 | 0 | 0 |
| primekg | shared_auto | adjusted_rr | 0.074742 | 0.074676 | 0.074676 | -0.000067 | 0 | -0.000067 |
| primekg | shared_auto | invalid | 0.002000 | 0.002000 | 0.002000 | 0 | 0 | 0 |
| primekg | shared_edge_lodo | exact_match | 0 | 0 | 0 | 0 | 0 | 0 |
| primekg | shared_edge_lodo | adjusted_rr | 0.074687 | 0.074687 | 0.074676 | 0 | -0.000011 | -0.000011 |
| primekg | shared_edge_lodo | invalid | 0.002000 | 0.002000 | 0.002000 | 0 | 0 | 0 |
| pharmkg | shared_auto | exact_match | 0.002000 | 0.002000 | 0.002000 | 0 | 0 | 0 |
| pharmkg | shared_auto | adjusted_rr | 0.021290 | 0.020956 | 0.021317 | -0.000333 | 0.000361 | 0.000028 |
| pharmkg | shared_auto | invalid | 0.574000 | 0.588000 | 0.584000 | 0.014000 | -0.004000 | 0.010000 |
| pharmkg | shared_edge_lodo | exact_match | 0.002000 | 0.002000 | 0.002000 | 0 | 0 | 0 |
| pharmkg | shared_edge_lodo | adjusted_rr | 0.021290 | 0.020956 | 0.020969 | -0.000333 | 0.000013 | -0.000321 |
| pharmkg | shared_edge_lodo | invalid | 0.578000 | 0.592000 | 0.592000 | 0.014000 | 0 | 0.014000 |
| hetionet | shared_auto | exact_match | 0.030000 | 0.030000 | 0.030000 | 0 | 0 | 0 |
| hetionet | shared_auto | adjusted_rr | 0.100087 | 0.100087 | 0.100087 | 0 | 0 | 0 |
| hetionet | shared_auto | invalid | 0.020000 | 0.020000 | 0.020000 | 0 | 0 | 0 |
| hetionet | shared_edge_lodo | exact_match | 0.030000 | 0.030000 | 0.030000 | 0 | 0 | 0 |
| hetionet | shared_edge_lodo | adjusted_rr | 0.100087 | 0.100087 | 0.100087 | 0 | 0 | 0 |
| hetionet | shared_edge_lodo | invalid | 0.020000 | 0.020000 | 0.020000 | 0 | 0 | 0 |
| drkg | shared_auto | exact_match | 0.014000 | 0.014000 | 0.014000 | 0 | 0 | 0 |
| drkg | shared_auto | adjusted_rr | 0.046285 | 0.046285 | 0.046285 | 0 | 0 | 0 |
| drkg | shared_auto | invalid | 0 | 0 | 0 | 0 | 0 | 0 |
| drkg | shared_edge_lodo | exact_match | 0.014000 | 0.014000 | 0.014000 | 0 | 0 | 0 |
| drkg | shared_edge_lodo | adjusted_rr | 0.046285 | 0.046285 | 0.046285 | 0 | 0 | 0 |
| drkg | shared_edge_lodo | invalid | 0 | 0 | 0 | 0 | 0 | 0 |
| repodb | shared_auto | exact_match | 0.004000 | 0.004000 | 0.004000 | 0 | 0 | 0 |
| repodb | shared_auto | adjusted_rr | 0.037795 | 0.037795 | 0.038159 | 0 | 0.000363 | 0.000363 |
| repodb | shared_auto | invalid | 0 | 0 | 0 | 0 | 0 | 0 |
| repodb | shared_edge_lodo | exact_match | 0.004000 | 0.004000 | 0.002000 | 0 | -0.002000 | -0.002000 |
| repodb | shared_edge_lodo | adjusted_rr | 0.038045 | 0.038159 | 0.036653 | 0.000114 | -0.001506 | -0.001391 |
| repodb | shared_edge_lodo | invalid | 0 | 0 | 0 | 0 | 0 | 0 |

## Interpretation constraints

- Frozen checkpoints isolate input calibration; they do not compare separately retrained end-to-end systems.

- Topology-based two-hop retention ignores relation semantics/direction and is NOT mechanistic or clinical information retention.

- Native fuzzy graph sizes provide per-query budgets. Shared edge scoring has no dataset-specific relation-family weights.

- Edge LODO excludes target validation scores only in the new coefficient-selection step; its inherited fuzzy candidate order and budgets retain historical dataset-specific choices.

- E2E uses one consistent promote-to-front rule and exact candidate matching, including invalid outputs. Historical collectors used differing rules; do not splice their numbers into this table.

- Coefficient jitter keeps zeros zero and is different from independent score noise; the original noise limitation is not negated.

- Unchanged candidate metrics under graph perturbation do not establish E2E robustness.

- Counts of independent query groups, calibration positives, learned weights and CV traces are exported for audit.
