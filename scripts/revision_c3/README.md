# Reviewer 1, Comment 3 — information retention và subgraph selection

Nguyên văn reviewer: “The authors must provide a quantitative analysis of information retention across edge selection and compare against alternative subgraph selection strategies.”

Bộ thực nghiệm này tách ba câu hỏi: **giữ lại cấu trúc gì**, **so với chiến lược khác ở cùng ngân sách ra sao**, và **thay đổi đó ảnh hưởng encoder/LLM thế nào**. Candidate order luôn cố định theo input của fuzzy gốc; riêng repoDB đó là raw/display-control order. Không dùng candidate MRR bất biến để chứng minh information retention.

Code mới ở `scripts/revision_c3/`; kết quả ở `results/revision_c3/`; bản chèn supplementary/response riêng ở `minor_revision/comment3/`. Không ghi đè checkpoint, dữ liệu, manuscript hoặc kết quả comment 2.

**Đã chạy xong trên RTX 4090 ngày 06/11/2026:** CPU 620 + native audit 60 hàng tổng hợp; GPU đủ 140 hàng/58.800 row–variant evaluations trên cả 5 test splits. Cache có 30.364 model/input predictions khác nhau. 19 unit tests đã pass; `verify_outputs.py` đã pass kiểm tra frozen code/input, budgets, 260.400 CPU row–variant records, đầy đủ GPU predictions, rescoring/aggregates, finite metrics và XLSX. Xem bản diễn giải tiếng Việt ở `minor_revision/comment3/RESULTS_VI.md`, bản supplementary 7 trang ở `minor_revision/comment3/supplementary_preview.pdf` và workbook `results/revision_c3/exports/comment3_results.xlsx`.

## 1. Phạm vi mặc định

| Thành phần | Phạm vi |
|---|---|
| Dataset | PrimeKG, PharmKG, Hetionet, DRKG, repoDB |
| CPU | Toàn bộ valid/test: 2.100 + 2.100 rows |
| So sánh ngân sách gốc | 22 variants, gồm references, deterministic selectors và random controls |
| Budget curves | 20/35/55/75/90% **cạnh duy nhất**, 40 variants |
| Tổng CPU | 62 variants × 5 dataset × 2 split = **620 hàng tổng hợp** |
| Audit implementation native | Replay exact artifact và5 budget ratios: **60 hàng bổ sung**, giữ nguyên reservation passes gốc, ghi mọi budget violation |
| Random tại ngân sách gốc | 5 seeds cho uniform random; 5 seeds cho random + coverage |
| Random trên budget curves | 3 seeds cho mỗi tỷ lệ |
| GPU | 22 variants ngân sách gốc + 6 budget variants = **28 variants/dataset**, **140 hàng tổng hợp** nếu hoàn tất |
| GPU budget variants | Native coverage / PPR terminals / random seed0 tại 35% và75% |
| Biểu diễn | Cosine và relative L2 ở graph-adapter output, so với source raw và source unique |
| Downstream | Exact generated-answer accuracy, invalid, top1-copy, adjusted MRR, prediction agreement |
| Hiệu năng | Timing CPU selection; graph encoder benchmark 32 query groups, 3 repeats |
| Uncertainty | 2.000 paired query-cluster bootstrap; thêm joint query/seed bootstrap cho random means |

620 hàng tổng hợp không phải620 dataset độc lập. Các variants dùng lại cùng source rows. Tương tự, 28 × 2.100 =58.800 lượt đánh giá GPU vẫn chỉ có2.100 test rows. Không gộp các seed thành số lượng test samples lớn hơn.

## 2. Đối chứng và công bằng ngân sách

Trong bảng chính, mỗi query có `B = số cạnh duy nhất trong fuzzy artifact gốc`. Mọi selector cạnh đều chọn đúngB cạnh từ **cùng tập source unique triples**. Không thêm cạnh, không đổi loại quan hệ, không dùng gold để chọn cạnh. Tie-break xác định và reproducible.

| Tên trong kết quả | Thuật toán |
|---|---|
| `source_raw` | Graph nguồn giữ nguyên cả cạnh lặp; reference không nén |
| `source_unique` | Chỉ loại bản sao của cùng `[head, relation, tail]`; reference tách tác dụng deduplication |
| `original_fuzzy` | Graph đã được chọn bởi pipeline gốc, không tái xây dựng bằng công thức xấp xỉ |
| `empty_graph` | Diagnostic bỏ local graph; global KG embeddings vẫn còn |
| `native_topk` | ChọnB cạnh có native edge score cao nhất, bỏ coverage/reservation passes |
| `native_coverage` | Native score + strict candidate/query coverage rồi fill; control mới, không gọi là native implementation nguyên trạng |
| `degree_topk` | Xếp cạnh theo tổng endpoint degree trong source unique graph |
| `query_bfs` | Ưu tiên cạnh gần query theo khoảng cách BFS vô hướng; tie theo source index |
| `ppr_query` | Personalized PageRank chỉ teleport về query, edge score=sum endpoint PPR |
| `ppr_terminals` | PPR teleport đều về query và các candidate có mặt trong graph; edge score như trên |
| `shortest_paths` | Giữ một shortest path dài≤3 cạnh/query-candidate nếu vừa budget; xét candidate theo fixed order, rồi fill theo native score |
| `relation_diverse` | Round-robin qua relation IDs, trong mỗi relation ưu tiên native score |
| `random_s0..s4` | Uniform random sampling không hoàn lại trên unique edges |
| `random_coverage_s0..s4` | Random ordering + cùng strict coverage pass rồi fill |

PPR dùng graph vô hướng không trọng số, damping=.85, teleport=.15, tối đa200 iterations, dừng khi L1 change<1e-10. Dangling mass được trả về teleport distribution. Các candidate vắng source không được chèn làm graph nodes. Query được giữ trong state space kể cả khi cô lập; với PPR-query trên query cô lập, các cạnh có thể tie và dùng source-index tie-break.

Native scores của PrimeKG tính đúng từ frozen path features/config; các dataset còn lại đọc score rows đã lưu. Source triples, candidate IDs và query/gold alignment được assert. Với cạnh lặp, các score phải khớp nhau. `original_fuzzy` luôn dùng chính artifact gốc, vì native reservation/coverage passes khác nhau giữa dataset.

`source_raw`, `source_unique`, `empty_graph` là references có ngân sách khác, không được trình bày như đối thủ cùng budget. Budget curves dùng `round(ratio * source_unique_edges)`, không áp minimum/cap lịch sử. Vì vậy native_coverage ở55% unique edges có thể khác `original_fuzzy`, đặc biệt PrimeKG.

Audit bổ sung gọi trực tiếp hàm selection trong script native, không gọi `main()` hay ghi lại dữ liệu gốc. Ở budget gốc, tập cạnh khớp artifact100% cả5 dataset/2 split. Khi override budget, audit giữ nguyên coverage/reservation passes và ghi kích thước thực tế: PrimeKG có thể vượt budget vì coverage pass gốc không chặn ngân sách. Những rows này không được coi là strict-budget competitors. Wrapper CPU tự chạy thêm audit này và xuất20 case theo strata mất/giữ path, không chọn case theo accuracy.

## 3. Các phép đo information retention

Các phép đo sau là **định nghĩa vận hành**, không phải mutual information, expert-annotated mechanism preservation hay clinical validation.

| Nhóm | Định nghĩa |
|---|---|
| Occurrence/unique edges | Báo riêng số dòng cạnh và số unique triples; decomposition thành retained unique / removed unique / duplicates |
| Node retention | Số source nodes còn có cạnh sau chọn / số source nodes |
| Candidate coverage | Candidate có ít nhất một cạnh; báo absolute/20 và retained/source-covered |
| Rank-band coverage | Cùng phép đo cho top5, middle5 và tail10 |
| Query coverage | Query còn hiện diện; conditional retention chỉ tính nếu source đã có query |
| Reachability ≤2/≤3 | Số candidate còn nối được với query trong≤k bước / số candidate source nối được trong≤k bước |
| Exact path retention | Tỷ lệ exact edge-labeled simple path witnesses dài đúng2 hoặc3 còn đủ tất cả cạnh |
| Typed pattern retention | Tỷ lệ chuỗi `(relation ID, traversal direction)` còn ít nhất một path witness |
| Gene-intermediate paths | Paths2/3 mà mọi intermediate node có annotation Gene; chỉ áp dụng khi annotation có sẵn |
| Relation types | Tỷ lệ source relation types còn ít nhất một cạnh |
| Relation JSD | Jensen–Shannon divergence, log base2, giữa source và selected relation-frequency distributions |
| Degree-mass JSD | JSD giữa node incidence/degree mass trên cùng source-node support; không phải histogram degree values |
| Rare-relation edges | Recall của cạnh thuộc relation có source frequency≤median frequency trong query graph |
| Incoming two-hop context | Recall của union cạnh nằm trong2 bước predecessor của query/candidates, theo hướng cạnh mà R-GCN thực sự nhận |
| Direct exposure | Recall và selected share của cạnh trực tiếp query–candidate; không mặc định mọi cạnh trực tiếp đều là leakage |
| Gold diagnostics | Gold-incident recall và gold reachability≤3, chỉ sau selection và khi denominator có nghĩa |
| Encoder retention | Cosine và `||z_selected-z_source||₂ / ||z_source||₂`, riêng query/candidates/gold-present |

Paths được duyệt vô hướng để đo connectivity; mỗi witness vẫn giữ edge identity, relation và dấu hướng duyệt. Không gọi đây là directed biochemical pathway. Incoming-context audit là phép đo riêng theo **hướng** actual graph encoder.

Source denominators bằng0 ⇒ **NA**, không điền1 hoặc0. Bảng đầy đủ có cột `_eligible`; bảng eligibility riêng có số0 cho trường hợp không áp dụng. Mean retention là trung bình theo row đủ điều kiện, không phải ratio của tổng số paths giữa các queries. Số source paths/reachable candidates cũng được xuất để đọc denominator.

Gene annotations lấy từ namespace `Gene::` của DRKG/repoDB và metadata Hetionet ánh xạ display name không mơ hồ. Không đoán loại entity từ tên gene-like ở PrimeKG/PharmKG. Có annotation không có nghĩa source nhất thiết tồn tại gene-intermediate path; khi không có thì metric vẫnNA.

Global frozen embeddings có thể chứa thông tin graph rộng hơn retrieved subgraph. Vì thế `empty_graph` chỉ loại bỏ local message passing. Các phép đo ở đây đều tương đối với **retrieved source graph**, không khẳng định giữ toàn bộ thông tin của KG.

## 4. Lưu ý số học và mô hình

Audit trên2.100 test rows, mỗi row gồm source raw và original fuzzy:

- FP16 graph encoder có9 trường hợp nonfinite trên source raw PrimeKG.
- FP32 graph encoder cho output hữu hạn trong cả4.200 trường hợp đã audit.
- Có projected embedding FP32 lớn hơn65.504, nên chỉ đổi encoder sangFP32 rồi ép vềFP16 chưa đủ.
- Protocol GPU cuối dùng **graph encoder FP32, LLM BF16**, load trực tiếp checkpoint vào precision tương ứng, kiểm tra finite trước và sau cast; không clipping, không bỏ row.
- RTX4090 hỗ trợBF16 và model3B vẫn phù hợp24GB VRAM. Mỗi lần chỉ load một dataset/checkpoint.
- Không trộn prediction FP16 lịch sử/comment2 vào run mới. Fingerprint khác khiến cache cũ không được tái dùng. CPU topology/candidate results không bị vấn đề precision này.

Đây là frozen-checkpoint input comparison: cùng checkpoint, decoding, candidate order và precision cho mọi selector trong một dataset. Không train lại graph adapter/LoRA riêng theo selector. Nếu thay model, dtype, code hoặc budget protocol, dùng output directory mới.

Encoder hiện tại có rule `len(subgraph)<=10` ⇒ dùng global/global embeddings. Các budget nhỏ có thể đi qua ngưỡng này; cột `encoder_global_fallback` ghi rõ. Graph nhỏ hơn cũng không trực tiếp giảm prompt tokens, vì graph đi qua embedding placeholders. Benchmark encoder không được quảng bá thành tốc độ toàn pipeline LLM.

## 5. Chạy trên server RTX4090 hiện tại

```bash
cd /home/anhlq/Documents/2026-dhd/SoftFuse-KGC
nvidia-smi
.venv/bin/python -c "import torch; print(torch.cuda.is_available(), torch.cuda.is_bf16_supported())"
.venv/bin/python -m unittest discover -s scripts/revision_c3 -p 'test_*.py' -v
```

Nếu Codex sandbox báo CUDA False, chạy GPU ở terminal server có quyền truy cập thiết bị. Không sửa driver vì sandbox không thấy GPU.

Môi trường đã chạy được ghi ở `results/revision_c3/environment.json` (Python 3.12, PyTorch 2.3.1+cu118, DGL 2.4.0+cu118, Transformers 4.44.2, PEFT 0.4.0). Dùng `.venv` hiện có trên server; không cần tải lại model. Model/checkpoint/embedding fingerprint được lưu riêng cho từng dataset.

Nếu muốn tái lập riêng audit FP16/FP32, chạy khi GPU không có job C3 khác:

```bash
.venv/bin/python scripts/revision_c3/audit_precision.py \
  --out results/revision_c3/precision_audit_recheck.json
```

Audit này chỉ chạy graph encoder, không sinh câu trả lời LLM. Bản `precision_audit.json` chính lưu bằng chứng của protocol đã dùng.

CPU đầy đủ, tự xuất bảng sau khi xong:

```bash
bash scripts/revision_c3/run.sh cpu
```

GPU đầy đủ, tự xuất bảng sau khi xong:

```bash
bash scripts/revision_c3/run.sh gpu \
  --offline \
  --model-path /home/anhlq/.cache/huggingface/hub/models--meta-llama--Llama-3.2-3B/snapshots/13afe5124825b4f3751f836b40dafda64c1ed062
```

Chạy cả hai bước với cùng protocol:

```bash
bash scripts/revision_c3/run.sh all \
  --offline \
  --model-path /home/anhlq/.cache/huggingface/hub/models--meta-llama--Llama-3.2-3B/snapshots/13afe5124825b4f3751f836b40dafda64c1ed062
```

Nếu SSH dễ ngắt, chạy trong terminal `tmux` nếu server có cài. Wrapper có `flock` để tránh hai wrapper jobs ghi cùng output. Không khởi động thêm direct Python job vào cùng thư mục trong lúc job khác đang chạy.

GPU flush prediction và representation diagnostics từng input vào cache. Khi gián đoạn, chạy lại đúng lệnh/output/protocol. Những input đã có cache không generate lại; reference embeddings và summary tables được dựng lại. Không xóa protocol để ép trộn các lần chạy khác nhau.

Lượt chạy trên server đã được tiếp tục từ cache sau khi tiến trình đầu dừng với mã 143. `gpu/resume_note.json` ghi nhận việc này. `gpu_complete.json:seconds` đo invocation hoàn tất cuối cùng, **không phải tổng thời gian inference ban đầu cộng resume**; tương tự `new_generations_this_invocation` không phải tổng số predictions đã cache.

Smoke GPU sau khi CPU đã hoàn tất:

```bash
.venv/bin/python scripts/revision_c3/run_gpu.py \
  --datasets primekg hetionet --max-rows 3 --bootstrap 100 \
  --skip-benchmark --offline \
  --model-path /home/anhlq/.cache/huggingface/hub/models--meta-llama--Llama-3.2-3B/snapshots/13afe5124825b4f3751f836b40dafda64c1ed062 \
  --out results/revision_c3/gpu_smoke_new
```

`--max-rows>0` luôn đánh dấu `smoke_only`, không đưa vào bài. Các smoke/failed-FP16 artifacts được giữ riêng và không dùng trong export chính.

Chạy một protocol CPU khác, ví dụ nhiều random seeds hơn:

```bash
RESULTS_DIR="$PWD/results/revision_c3_moreseeds" \
  bash scripts/revision_c3/run.sh cpu --random-seeds 10 --bootstrap 5000

RESULTS_DIR="$PWD/results/revision_c3_moreseeds" \
  bash scripts/revision_c3/run.sh gpu --offline \
  --model-path /home/anhlq/.cache/huggingface/hub/models--meta-llama--Llama-3.2-3B/snapshots/13afe5124825b4f3751f836b40dafda64c1ed062
```

Không chọn seed tốt nhất; báo cáo mọi seed và phân phối. Joint-bootstrap exporter mặc định cố định2.000 lần và ghi số này trong cột bootstrap, độc lập với tham số paired-bootstrap của runner.

## 6. Xuất kết quả

```bash
# Excel/CSV/Markdown/HTML/LaTeX
bash scripts/revision_c3/run.sh export

# Thêm3 hình PDF vector bằng PGFPlots/pdflatex đã có trên server
bash scripts/revision_c3/run.sh export --plots

# Kiểm tra đầy đủ sau khi GPU hoàn tất
.venv/bin/python scripts/revision_c3/verify_outputs.py
```

Exporter không cần matplotlib/openpyxl; workbook theo OOXML. Scientific plots dùng PGFPlots chuẩn và dữ liệu CSV đi kèm. Có thể export khi GPU còn chạy; trạng thái `not_complete` được giữ rõ, không điền metric còn thiếu. Để export một GPU run khác, dùng `--gpu-results` với `export_results.py`.

| File | Nội dung |
|---|---|
| `exports/comment3_results.xlsx` | Workbook mọi bảng, seed summaries, contrasts, distribution, subgroup, precision audit |
| `exports/REPORT.md`, `report.html` | Báo cáo tự sinh, định nghĩa và giới hạn diễn giải |
| `exports/seed_retention_summary.csv` | Mean/std qua seed; deterministic methods có1 seed |
| `exports/seed_e2e_summary.csv` | Mean/std qua seed cho LLM/encoder |
| `exports/random_*_contrasts.csv` | Random mean so original fuzzy, joint query/seed bootstrap |
| `exports/retention_distribution.csv` | p10/median/p90, tỷ lệ mất hoàn toàn ở từng metric có denominator |
| `exports/metric_eligibility.csv` | Số rows hợp lệ cho từng retention metric, kể cả0 |
| `exports/subgroup_analysis.csv` | Source có/không có query; gold có/không trongtop20; diagnostic, không chọn cấu hình |
| `exports/budget_reach3_retention.pdf` | Curve giữ candidate-query connectivity≤3 |
| `exports/budget_path3_retention.pdf` | Curve giữ exact length3 path witnesses |
| `exports/compression_decomposition.pdf` | Tách cạnh lặp và unique edges thực sự bị loại |
| `retention_metrics.csv` | 620 CPU rows mặc định, gồm mean và eligible counts |
| `retention_contrasts.csv` | Paired query-bootstrap từng variant so original fuzzy |
| `selection_timing.csv` | Thời gian gọi select sau xây Context; loại trừ preprocessing/path enumeration/score loading/metric/I/O, có dùng ordering cache; không phải total runtime |
| `input_audit.json` | Alignment, duplicate counts, nguồn graph và annotation eligibility |
| `native_budget_audit/native_budget_metrics.csv` | 60 rows từ implementation gốc: requested/actual budget, violations và retention |
| `native_budget_audit/replay_audit.json` | Exact edge-set replay so artifact, từng dataset/split |
| `case_audit.md`, `case_audit.json` | 20 case thấp/giữa/cao về path retention, ví dụ cạnh/đường đi bị mất và được giữ |
| `per_query/.../*.jsonl.gz` | Retention từng row từng variant, phục vụ audit/bootstrap |
| `gpu/e2e_metrics.csv` | Toàn bộ E2E/representation rows |
| `gpu/e2e_contrasts.csv` | So original fuzzy và source raw; reference ghi ở từng hàng |
| `gpu/encoder_benchmark.csv` | Timing encoder, scope ghi rõ; không phải latency LLM |
| `gpu/predictions/...` | Prediction, scores và representation diagnostics từng row |
| `gpu/cache/` | Cache theo model/input/protocol, tiếp tục được sau gián đoạn |
| `precision_audit.json` | Danh sách từng case FP16 nonfinite và đối chứngFP32 |
| `protocol_cpu.json`, `gpu/protocol_gpu.json` | Protocol frozen trước chạy |
| `cpu_complete.json`, `gpu/gpu_complete.json` | Dấu hoàn tất; không suy ra hoàn tất từ CSV đang ghi dở |

## 7. Cách dùng cho revision

Manuscript nên có một đoạn định nghĩa information-retention proxies, bảng so sánh cùng budget và kết luận trade-off. Supplementary nên chứa thuật toán baseline, denominator/eligible counts, budget curves, random seeds/CI, representation/downstream và precision audit.

Không diễn giải coverage=100% thành giữ100% thông tin; không gọi paths vô hướng là cơ chế điều trị; không gọi generated-answer invariance là semantic equivalence. Nếu shortest-path baseline giữ connectivity tốt hơn fuzzy, cần báo cáo rõ. Nếu exact accuracy không tăng, kết luận nên giới hạn ở evidence packaging và measured structural retention.

Timing CPU chỉ đo lời gọi selection sau khi đã dựng Context và đọc native scores. Adjacency/path enumeration chung nằm ngoài đồng hồ; một số budget variants dùng lại ordering cache. Không dùng bảng này để tuyên bố selector nào nhanh nhất end-to-end. Benchmark GPU cũng loại trừ LLM generation.

Các file supplementary/response là insertion drafts riêng; chưa thay manuscript/ESM/response DOCX gốc. Không ghép trực tiếp các số E2E mới với historical FP16/collector metrics khác protocol.

`export` tự sinh các bảng và hình trong `results/revision_c3/exports/`. Các đoạn diễn giải trong `minor_revision/comment3/` được viết theo run đã hoàn tất này, không tự thay đổi khi bạn tạo protocol mới. Sau khi cập nhật diễn giải cho số liệu mới, có thể compile preview từ thư mục `minor_revision/comment3/` bằng `pdflatex` hai lần (cần export `--plots` trước).

## 8. Troubleshooting

- `Protocol changed`: chọn thư mục output mới; giữ nguyên bản protocol cũ để audit.
- `Native score/source mismatch`: kiểm tra input artifacts; không bỏ assertion để chạy tiếp.
- CUDA/BF16 unavailable: kiểm tra `.venv`, GPU quyền truy cập vàRTX4090; không đổi dtype giữa các variants.
- `FloatingPointError`: script cố ý dừng, không loại row hoặc clipping. Kiểm tra precision/checkpoint và xuất case để audit.
- OOM: kiểm tra GPU job khác; runner chỉ dùng một3B model, batch1. Không train thêm một model trong cùngGPU lúc này.
- `pdflatex` không có trên máy khác: export bảng không dùng `--plots`, hoặc cài TeX Live/PGFPlots rồi compile các `.tex` trong exports.
- `verify_outputs.py` báo chưa complete: chờ/chạy tiếpGPU; smoke không được nâng trạng thái thành complete.
