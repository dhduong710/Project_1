# Comment 3 — information retention and subgraph selection

CPU: **complete**. GPU: **complete**.

All matched-budget selectors receive the same candidate order and unique edge budget per query. Source/raw, source/unique and empty-graph are diagnostic references, not matched-budget competitors.

Coverage means candidate-node incidence. Reachability counts candidates connected to the query within three edges. Path retention counts exact edge-labeled simple paths of length three. These are different quantities; none establishes biomedical mechanism retention.

Paths can traverse edges in either direction; path signatures retain relation labels and traversal signs. The directed two-layer incoming-edge audit is reported separately for the actual encoder. All denominators refer to the retrieved source graph, not the entire KG.

Undefined source denominators are omitted, with eligible counts exported. Do not substitute 1.0 or 0.0 for missing paths. Gold-specific metrics are post-selection diagnostics only.

Random results average all declared seeds; seed standard deviations are not test confidence intervals. Joint query-cluster/seed bootstrap contrasts are exported separately; intervals are exploratory without multiplicity correction.

## Duplicate removal versus unique-edge removal

| dataset | rows | source_occurrences_mean | source_unique_mean | fuzzy_unique_mean | sources_with_duplicates |
|---|---|---|---|---|---|
| primekg | 500 | 59.932000 | 38.094000 | 32.340000 | 500 |
| pharmkg | 500 | 100 | 100 | 55 | 0 |
| hetionet | 100 | 80 | 80 | 44 | 0 |
| drkg | 500 | 100 | 100 | 55 | 0 |
| repodb | 500 | 100 | 100 | 55 | 0 |

## Native implementation replay and budget audit

The optional native audit calls the original selection functions and checks exact edge-set replay at the original budget. At smaller budgets its actual edge count can exceed the requested count (PrimeKG coverage pass); these points are not strict-budget comparisons.

| dataset | budget | requested_budget | selected_unique_edges | budget_violation | reach3_retention |
|---|---|---|---|---|---|
| primekg | native | 32.340000 | 32.340000 | 0 | 0.773690 |
| primekg | 0.200000 | 7.576000 | 15.662000 | 0.998000 | 0.140754 |
| primekg | 0.350000 | 13.336000 | 15.886000 | 0.742000 | 0.143546 |
| primekg | 0.550000 | 20.960000 | 20.964000 | 0.002000 | 0.255226 |
| primekg | 0.750000 | 28.568000 | 28.568000 | 0 | 0.571476 |
| primekg | 0.900000 | 34.320000 | 34.320000 | 0 | 0.894801 |

## Matched-budget test retention

| dataset | method | candidate_coverage_retained | reach3_retention | path3_retention | relation_retention | relation_jsd |
|---|---|---|---|---|---|---|
| primekg | original_fuzzy | 1 | 0.773690 | 0.654268 | 0.937833 | 0.004577 |
| primekg | native_topk | 0.926731 | 0.780525 | 0.732384 | 0.969333 | 0.003228 |
| primekg | ppr_terminals | 0.910087 | 0.911124 | 0.828892 | 0.868500 | 0.009965 |
| primekg | shortest_paths | 0.999251 | 0.998548 | 0.819947 | 0.925000 | 0.005680 |
| primekg | relation_diverse | 0.921542 | 0.769439 | 0.719406 | 1 | 0.001738 |
| primekg | random | 0.897519 | 0.776023 | 0.644298 | 0.965200 | 0.002878 |
| primekg | random_coverage | 1 | 0.781590 | 0.632666 | 0.959267 | 0.003721 |
| pharmkg | original_fuzzy | 1 | 0.901000 | 0 | 0.898403 | 0.137545 |
| pharmkg | native_topk | 0.620600 | 0.560000 | 0 | 0.859534 | 0.124309 |
| pharmkg | ppr_terminals | 0.597300 | 0.597200 | 0.173782 | 0.760978 | 0.149315 |
| pharmkg | shortest_paths | 1 | 1 | 0.860447 | 0.927989 | 0.131224 |
| pharmkg | relation_diverse | 0.853500 | 0.842900 | 0.454855 | 1 | 0.065257 |
| pharmkg | random | 0.560240 | 0.442280 | 0.180125 | 0.861933 | 0.025422 |
| pharmkg | random_coverage | 1 | 0.746460 | 0.235325 | 0.892715 | 0.036575 |
| hetionet | original_fuzzy | 1 | 0.483503 | 0 | 0.837000 | 0.043803 |
| hetionet | native_topk | 0.567616 | 0.145503 | 0 | 0.669167 | 0.048374 |
| hetionet | ppr_terminals | 0.606854 | 0.625111 | 0.041667 | 0.677167 | 0.200008 |
| hetionet | shortest_paths | 0.851443 | 1 | 0.620657 | 0.897833 | 0.042705 |
| hetionet | relation_diverse | 0.804191 | 0.847937 | 0.496862 | 1 | 0.010615 |
| hetionet | random | 0.925287 | 0.484801 | 0.161496 | 0.903867 | 0.009131 |
| hetionet | random_coverage | 1 | 0.606795 | 0.148351 | 0.919433 | 0.008636 |
| drkg | original_fuzzy | 1 | 0.892055 | 0.476657 | 0.656191 | 0.070813 |
| drkg | native_topk | 0.553671 | 0.092218 | 0 | 0.519006 | 0.089823 |
| drkg | ppr_terminals | 0.766270 | 0.730526 | 0.611074 | 0.713325 | 0.095656 |
| drkg | shortest_paths | 0.819902 | 1 | 0.649552 | 0.616989 | 0.076992 |
| drkg | relation_diverse | 0.808292 | 0.697380 | 0.530847 | 1 | 0.039120 |
| drkg | random | 0.896491 | 0.504308 | 0.162936 | 0.776802 | 0.027250 |
| drkg | random_coverage | 1 | 0.712477 | 0.174681 | 0.791968 | 0.026833 |
| repodb | original_fuzzy | 1 | 0.954563 | 0.528578 | 0.858211 | 0.031948 |
| repodb | native_topk | 0.671692 | 0 | 0 | 0.791389 | 0.037228 |
| repodb | ppr_terminals | 0.905660 | 0.911205 | 0.797181 | 0.775689 | 0.059063 |
| repodb | shortest_paths | 0.897132 | 1 | 0.832201 | 0.858211 | 0.031171 |
| repodb | relation_diverse | 0.924805 | 0.939879 | 0.729486 | 1 | 0.034413 |
| repodb | random | 0.920003 | 0.546485 | 0.155186 | 0.900518 | 0.017092 |
| repodb | random_coverage | 1 | 0.770026 | 0.147511 | 0.905624 | 0.017345 |

## Frozen-model test results

| dataset | method | exact_match | adjusted_rr | prediction_agreement_raw | candidate_cosine_vs_raw |
|---|---|---|---|---|---|
| primekg | source_raw | 0 | 0.074676 | 1 | 1 |
| primekg | source_unique | 0 | 0.074711 | 0.966000 | 0.999307 |
| primekg | original_fuzzy | 0 | 0.074687 | 0.788000 | 0.945338 |
| primekg | empty_graph | 0.004000 | 0.078118 | 0.486000 | 0.658569 |
| primekg | native_topk | 0 | 0.074687 | 0.794000 | 0.930545 |
| primekg | ppr_terminals | 0 | 0.074676 | 0.952000 | 0.972530 |
| primekg | shortest_paths | 0 | 0.074687 | 0.768000 | 0.941709 |
| primekg | relation_diverse | 0 | 0.074687 | 0.794000 | 0.929095 |
| primekg | random | 0.000400 | 0.075003 | 0.885600 | 0.954387 |
| primekg | random_coverage | 0 | 0.074683 | 0.868400 | 0.976544 |
| pharmkg | source_raw | 0 | 0.020700 | 1 | 1 |
| pharmkg | source_unique | 0 | 0.020700 | 1 | 1 |
| pharmkg | original_fuzzy | 0.002000 | 0.020971 | 0.800000 | 0.999051 |
| pharmkg | empty_graph | 0 | 0.018765 | 0.088000 | 0.699950 |
| pharmkg | native_topk | 0 | 0.019015 | 0.586000 | 0.888747 |
| pharmkg | ppr_terminals | 0.002000 | 0.021282 | 0.738000 | 0.871275 |
| pharmkg | shortest_paths | 0.002000 | 0.021290 | 0.808000 | 0.998427 |
| pharmkg | relation_diverse | 0 | 0.019779 | 0.742000 | 0.952879 |
| pharmkg | random | 0.000400 | 0.020014 | 0.658000 | 0.869303 |
| pharmkg | random_coverage | 0.000800 | 0.020844 | 0.830400 | 0.999092 |
| hetionet | source_raw | 0.030000 | 0.100087 | 1 | 1 |
| hetionet | source_unique | 0.030000 | 0.100087 | 1 | 1 |
| hetionet | original_fuzzy | 0.030000 | 0.100087 | 1 | 1 |
| hetionet | empty_graph | 0.010000 | 0.081727 | 0.260000 | 0.783782 |
| hetionet | native_topk | 0.020000 | 0.090760 | 0.140000 | 0.903638 |
| hetionet | ppr_terminals | 0.020000 | 0.091019 | 0.710000 | 0.914290 |
| hetionet | shortest_paths | 0.030000 | 0.100198 | 0.730000 | 0.966753 |
| hetionet | relation_diverse | 0.020000 | 0.090952 | 0.690000 | 0.956575 |
| hetionet | random | 0.030000 | 0.100153 | 0.806000 | 0.982895 |
| hetionet | random_coverage | 0.030000 | 0.100087 | 1 | 1 |
| drkg | source_raw | 0.014000 | 0.046285 | 1 | 1 |
| drkg | source_unique | 0.014000 | 0.046285 | 1 | 1 |
| drkg | original_fuzzy | 0.014000 | 0.046285 | 1 | 0.986748 |
| drkg | empty_graph | 0.012000 | 0.044428 | 0.992000 | 0.693841 |
| drkg | native_topk | 0.012000 | 0.044428 | 0.996000 | 0.868005 |
| drkg | ppr_terminals | 0.012000 | 0.044428 | 0.992000 | 0.915511 |
| drkg | shortest_paths | 0.014000 | 0.046285 | 0.998000 | 0.940096 |
| drkg | relation_diverse | 0.012000 | 0.044428 | 0.992000 | 0.927039 |
| drkg | random | 0.012400 | 0.044799 | 0.993200 | 0.956731 |
| drkg | random_coverage | 0.014000 | 0.046285 | 0.996400 | 0.984988 |
| repodb | source_raw | 0.002000 | 0.036642 | 1 | 1 |
| repodb | source_unique | 0.002000 | 0.036642 | 1 | 1 |
| repodb | original_fuzzy | 0.004000 | 0.037776 | 0.808000 | 0.980607 |
| repodb | empty_graph | 0.018000 | 0.050365 | 0.196000 | 0.794083 |
| repodb | native_topk | 0.022000 | 0.052473 | 0.064000 | 0.922188 |
| repodb | ppr_terminals | 0.004000 | 0.038271 | 0.774000 | 0.964982 |
| repodb | shortest_paths | 0.002000 | 0.036409 | 0.622000 | 0.966845 |
| repodb | relation_diverse | 0.002000 | 0.036456 | 0.778000 | 0.970243 |
| repodb | random | 0.005200 | 0.039200 | 0.661200 | 0.970896 |
| repodb | random_coverage | 0.001600 | 0.036032 | 0.866000 | 0.988436 |

## Numerical precision audit

| dataset | dtype | encoder_cases | nonfinite_cases | max_abs_finite_output |
|---|---|---|---|---|
| primekg | float16 | 1000 | 9 | 26496 |
| primekg | float32 | 1000 | 0 | 130444.351562 |
| pharmkg | float16 | 1000 | 0 | 3.585938 |
| pharmkg | float32 | 1000 | 0 | 3.586100 |
| hetionet | float16 | 200 | 0 | 4.167969 |
| hetionet | float32 | 200 | 0 | 4.169904 |
| drkg | float16 | 1000 | 0 | 19.671875 |
| drkg | float32 | 1000 | 0 | 19.677286 |
| repodb | float16 | 1000 | 0 | 7.339844 |
| repodb | float32 | 1000 | 0 | 7.339898 |

The final C3 run uses FP32 graph encoding and BF16 LLM inference, with finite checks before/after the cast. The FP16 graph audit found nonfinite outputs; FP32 outputs can also exceed the FP16 exponent range. No clipping or sample exclusion is used. C2/legacy FP16 cached predictions are not reused under this new fingerprint.

## Interpretation limits

- A graph with at most 10 edge occurrences triggers the existing global-embedding fallback. Empty graph disables local graph messages, not pretrained/global KG knowledge.

- The GNN consumes directed triples. Undirected path preservation can change without changing the embeddings of the query/candidates; inspect encoder cosine and L2 as well as topology.

- Identical generated answers are not evidence that discarded edges were semantically irrelevant or that methods are equivalent.

- Native-score coverage and top-k controls reuse the archived native scores. The strict coverage implementation is explicitly a new control, not claimed to reproduce all native reservation passes.

- Gene-intermediate paths use explicit DRKG/repoDB namespaces and unambiguous Hetionet metadata. PrimeKG/PharmKG types are not guessed; annotation eligibility is reported.

- Graph-encoder timings exclude LLM generation and cannot be presented as end-to-end speedups. Graphs enter the LLM through embeddings; fewer edges do not directly reduce prompt token count.

- CPU selection timings start after Context construction and archived-score loading. They exclude common adjacency/path preprocessing and may reuse per-source ordering caches; they are descriptive selection-call timings, not a total-runtime ranking of selectors.

- Budgets and methods were declared before the run. No test-winning method or ratio is selected as a new default. Historical benchmark reuse makes this a retrospective analysis.
