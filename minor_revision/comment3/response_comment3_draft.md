# Reviewer 1 — Comment 3: response draft

Insertion draft only. Final section/table numbers must be assigned when integrating the supplied methods, results, and figures into the original manuscript/supplementary. This file does not edit the response DOCX.

**Comment:** “The authors must provide a quantitative analysis of information retention across edge selection and compare against alternative subgraph selection strategies.”

**Proposed response**

We thank the reviewer for this request. We agree that a smaller subgraph and unchanged candidate ranking do not establish information preservation. The additional study therefore separates candidate incidence coverage, graph connectivity/path retention, graph-encoder representation changes, and generated-answer behavior.

The structural study compares the archived fuzzy subgraph with uniform random selection, random selection with coverage, native-score top-k selection, strict native-score coverage selection, degree-based selection, query-centered BFS, two personalized PageRank variants, shortest-path preservation, and relation-stratified selection. Each compressed alternative uses the same source edge set, candidate order, and per-query unique-edge budget. Uncompressed multiset, deduplicated-source, and empty-graph references are reported separately. We evaluate all five datasets, five random seeds at the matched budget, and five additional budget ratios. We also call the original implementation functions to verify exact replay and audit their behavior at smaller budgets.

The quantitative measures include candidate/query coverage, reachability within two/three edges, exact edge-labeled path retention, relation/sign-pattern retention, relation-type retention, relation-frequency and node-incidence Jensen–Shannon divergence, and directed incoming-context retention. Source denominators and eligible counts are explicit; queries without the relevant source information are not credited with perfect retention. Gold-specific quantities are computed only after selection. The paths are structural witnesses rather than expert-validated therapeutic mechanisms.

The results reveal a trade-off rather than uniform superiority. Although original fuzzy retrieval preserves relative candidate coverage on all five datasets, its three-hop reachability retention is 0.7737, 0.9010, 0.4835, 0.8921, and 0.9546 on PrimeKG, PharmKG, Hetionet, DRKG, and repoDB, respectively. It exceeds random selection clearly on PharmKG, DRKG, and repoDB, but not consistently on PrimeKG or Hetionet. The shortest-path baseline retains nearly all originally reachable candidates at the same edge budget, while losing incidence coverage for some other candidates. Original fuzzy retrieval also loses all length-three witnesses in the eligible PharmKG and Hetionet rows, demonstrating why incidence coverage cannot substitute for path retention.

We additionally separate duplicate removal from unique-edge removal. In PrimeKG, the mean source graph has 59.932 edge occurrences but 38.094 unique triples; the fuzzy graph retains 32.340 unique triples. Reporting only the occurrence reduction would overstate the amount of unique graph structure removed. Since repeated edges can still affect message passing, deduplicated-source inference is included as a separate reference.

The frozen-model protocol compares encoder-output cosine/L2 changes and generated-answer accuracy alongside adjusted MRR. A precision audit identified nonfinite FP16 graph outputs, so the final evaluation uniformly uses FP32 graph encoding and BF16 LLM inference, checks finiteness, and excludes no examples. These results must be reported separately from historical FP16 evaluations. Unchanged answers alone are not interpreted as evidence that removed edges were semantically irrelevant.

The full-test GPU comparison covers 28 variants on each of the five datasets. Fuzzy/source answer agreement is 78.8%, 80.0%, 100%, 100%, and 80.8% on PrimeKG, PharmKG, Hetionet, DRKG, and repoDB. Hetionet is instructive: candidate embeddings and generated answers are unchanged, while query embeddings change and the eligible length-three path witnesses are lost. Fuzzy exact generated-answer accuracy is 0.0%, 0.2%, 3.0%, 1.4%, and 0.4%, respectively, under the standardized matching rule. Alternative selectors do not yield a uniform ordering: on repoDB, native-score top-k reaches 2.2%, and the empty-local-graph reference reaches 1.8%, while retaining global entity embeddings. We report these outcomes, the low correct-answer counts, and the uncertainty estimates explicitly rather than claiming a universal downstream advantage.

The revision should therefore describe fuzzy retrieval as a coverage-oriented evidence-packaging policy with measured structural trade-offs, rather than claiming lossless or universally superior information preservation. Full configuration traces, random-seed results, bootstrap comparisons, budget audits, encoder diagnostics, and illustrative retained/lost paths accompany the new experiments.

**Before submission**

- Integrate `manuscript_insert.tex`, `supplementary_methods.tex`, `supplementary_results.tex`, and `supplementary_gpu_results.tex` with final section/table references.
- Keep native budget-excess diagnostics distinct from strict matched-budget comparisons.
- Reconcile historical metric/dtype descriptions before replacing existing manuscript E2E tables.
- Do not strengthen the response to “lossless information retention,” “clinical mechanism preservation,” or “better than every alternative”; the experiment does not support those claims.
