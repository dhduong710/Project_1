# Thực nghiệm revision — Reviewer 1, Comment 2

Mục tiêu: kiểm tra mức phụ thuộc vào trọng số thủ công theo dataset, thử hiệu chỉnh tự động/có học, và đo khả năng chuyển **hệ số** sang dataset đích mà không dùng nhãn validation của dataset đích.

Bộ script không ghi đè dữ liệu, checkpoint, prediction hoặc manuscript gốc. Kết quả mặc định ở `results/revision_c2/`. Không cần train lại R-GCN hay Llama để chạy các thí nghiệm này.

**Trạng thái 2026-11-05:** đã hoàn tất CPU và GPU trên đủ 5 dataset, toàn bộ validation/test; 55 hàng E2E, không phải smoke. `verify_outputs.py` đã pass đối chiếu hash, selections và metrics từ prediction. Bộ 19 unit tests đã pass. GPU thực hiện 10.522 lần generation cho input/model khác nhau; cache được tái sử dụng trong tổng 48.300 lượt đánh giá row/variant (25.200 validation + 23.100 test). Đây vẫn là 2.100 hàng validation và 2.100 hàng test, không phải 48.300 mẫu độc lập.

Đọc kết quả: [Excel](../../results/revision_c2/exports/comment2_results.xlsx), [báo cáo đầy đủ](../../results/revision_c2/exports/REPORT.md), [PDF phương pháp/kết quả](../../minor_revision/comment2/supplementary_preview.pdf), [dự thảo trả lời reviewer](../../minor_revision/comment2/response_comment2_draft.md). PDF là bản ghép riêng để duyệt; chưa thay thế manuscript/supplementary gốc.

Kết luận cần giữ: learned/LODO có kết quả candidate khả quan, nhưng không luôn vượt equal weights và không bảo đảm tăng generated-answer accuracy. Edge search có nhiều ties. Toàn bộ kết quả thuận lợi, bất lợi và CI đều được giữ trong exports; không chọn cấu hình theo test.

## 1. Những gì được triển khai

| Thí nghiệm | Câu hỏi trả lời | Thực hiện |
|---|---|---|
| Replay original soft support | Code/feature nhập có khớp kết quả gốc không? | Đòi hỏi thứ tự 20 ứng viên trùng hoàn toàn ở valid/test cả 5 dataset; thất bại thì dừng |
| Native fixed b050 | Dùng chung hệ số ngoài cho công thức native có đủ không? | beta=.5, gamma=.1, mu=0; native E/D/X vẫn khác nhau theo dataset |
| Native validation grid | Có thể thay chọn tay bằng lựa chọn có quy trình không? | 224 cấu hình/dataset; chỉ chọn bằng validation; xuất toàn bộ trace |
| Shared equal weights | Cải thiện có đến từ feature thay vì học trọng số? | 5 feature chung, tất cả hệ số bằng 1 |
| Shared learned weights | Có thể học hệ số từ nhãn không? | Pairwise logistic tuyến tính, hệ số không âm trên feature đã định dấu, L2 chọn bằng grouped CV |
| Unconstrained learned | Ràng buộc dấu có ảnh hưởng không? | Cùng mô hình và CV, bỏ ràng buộc không âm |
| Leave-one-dataset-out (LODO) | Có chuyển hệ số mà không xem nhãn đích được không? | Học từ validation của 4 dataset khác; chọn L2 bằng leave-one-source-dataset-out CV |
| Pairwise dataset transfer | Chuyển từ nguồn cụ thể sang đích ra sao? | 20 cặp có hướng khi chạy đủ 5 dataset |
| Feature ablation | Hệ số học phụ thuộc cue nào? | Bỏ từng feature, fit/chọn L2 lại trên validation |
| Calibration label efficiency | Cần bao nhiêu nhãn để hiệu chỉnh? | 10/25/50/100% query groups, 5 seeds; CV lại bên trong từng subset |
| Coefficient sensitivity | Hệ số có ổn định quanh cấu hình đã chọn không? | Nhiễu log-normal nhân vào hệ số, sigma .05/.1/.25/.5, 5 seeds |
| Fuzzy graph-weight audit | Đổi trọng số cạnh/ngân sách làm graph thay đổi bao nhiêu? | Default/equal/jitter và retain ratio .35/.55/.75; topology metrics, Jaccard |
| Frozen-checkpoint E2E candidate arm | Reranking mới có ảnh hưởng output LLM không? | Giữ graph nguồn, checkpoint và decoding; chỉ thay order |
| Frozen-checkpoint E2E graph arm | Chọn trọng số cạnh tự động có tác dụng không? | Giữ candidate order và budget từng query; validation search 12 vectors; test sau khi freeze |
| Fuzzy edge LODO | Có chọn hệ số cạnh mà không dùng validation đích không? | Chọn vector bằng macro validation score của các dataset nguồn khác |
| Uncertainty | Chênh lệch có ổn định theo query không? | Paired query-cluster bootstrap, 2.000 lần; CI95%; không trộn nhiều gold của cùng query như các quan sát độc lập |

CPU: 5 dataset, 1.120 cấu hình native, 150 hàng metrics (gồm các split/transfer), 100 lượt label-efficiency, 200 lượt coefficient sensitivity, 260 hàng graph audit ở cấu hình mặc định.

GPU mặc định: 12 vector cạnh × toàn bộ validation của 5 dataset; sau đó 6 candidate variants + 5 graph variants × toàn bộ test. Cache tránh generate lại input giống hệt. Không cần GPU cho phần CPU.

## 2. Chạy ngay trên server hiện tại

Đứng trong Git repo:

```bash
cd /home/anhlq/Documents/2026-dhd/SoftFuse-KGC
nvidia-smi
.venv/bin/python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
.venv/bin/python scripts/revision_c2/check_environment.py --gpu
```

Nếu chạy từ môi trường Codex bị sandbox, CUDA có thể báo False dù GPU thật đang hoạt động. Chạy các lệnh GPU trong terminal server có quyền truy cập thiết bị. Không sửa driver chỉ vì sandbox không nhìn thấy GPU.

Trong môi trường đã kiểm tra: RTX 4090 24GB, torch 2.3.1+cu118, DGL 2.4.0+cu118, transformers 4.44.2, PEFT 0.4.0, numpy 2.4.4. Script GPU dùng FP16, batch1 và checkpoint Llama-3.2-3B; không cần bitsandbytes quantization hay optimizer. Không cần cài lại môi trường hiện có.

### A. Kiểm tra logic

```bash
.venv/bin/python -m unittest discover -s scripts/revision_c2 -p 'test_*.py' -v
```

Các test kiểm tra absent-gold, stable ties, query-disjoint CV, known positives, budget, candidate/ID/prompt alignment, exact-match thay vì substring và adjusted-rank thống nhất.

### B. Chạy toàn bộ CPU và tự xuất kết quả

```bash
bash scripts/revision_c2/run.sh cpu
```

Kết quả đã được chạy trên server trong lượt triển khai. Có thể chạy lại cùng lệnh với cùng protocol; nếu đổi seed/grid/code, dùng thư mục kết quả mới thay vì ghi đè một nghiên cứu đã freeze.

### C. Chạy E2E đầy đủ, tiếp tục được khi gián đoạn

Model đã có ở server, không cần download:

```bash
bash scripts/revision_c2/run.sh gpu \
  --offline \
  --model-path /home/anhlq/.cache/huggingface/hub/models--meta-llama--Llama-3.2-3B/snapshots/13afe5124825b4f3751f836b40dafda64c1ed062
```

Lệnh trên giữ terminal cho đến khi xong và tự xuất Excel/CSV/LaTeX/Markdown/HTML sau E2E. Nếu SSH dễ ngắt, chạy trong tmux đã cài hoặc dùng launcher ở terminal server:

```bash
bash scripts/revision_c2/launch_gpu.sh \
  --offline \
  --model-path /home/anhlq/.cache/huggingface/hub/models--meta-llama--Llama-3.2-3B/snapshots/13afe5124825b4f3751f836b40dafda64c1ed062
```

Launcher in PID và tên log; lưu ở `results/revision_c2/gpu.pid` và `gpu_log_path.txt`. Trong một số môi trường công cụ, tiến trình con bị thu hồi khi lệnh kết thúc, kể cả `nohup`; khi đó dùng phiên chạy trực tiếp hoặc terminal/tmux của server. **Có PID không đồng nghĩa đã chạy thành công**: kiểm tra log, protocol và progress.

```bash
cat results/revision_c2/gpu.pid
cat results/revision_c2/gpu_log_path.txt
# Dùng đường dẫn log vừa in:
tail -f results/revision_c2/gpu_YYYYMMDD_HHMMSS.log
```

Không chạy thêm job vào cùng thư mục khi job hiện tại đang hoạt động; `run.sh` có lock. Nếu dừng bằng Ctrl+C, chạy lại **đúng lệnh, đúng output và protocol**. Prediction đã generate được cache ngay từng query; một bảng chưa hoàn tất sẽ được tính lại từ cache. Nếu file cache bị ngắt ở dòng cuối, script khôi phục phần hoàn chỉnh.

### D. Chạy ít hơn để kiểm tra môi trường

```bash
.venv/bin/python scripts/revision_c2/run_e2e.py \
  --datasets primekg hetionet \
  --edge-trials 2 --calibration-max-rows 4 --test-max-rows 4 \
  --bootstrap 100 --offline \
  --model-path /home/anhlq/.cache/huggingface/hub/models--meta-llama--Llama-3.2-3B/snapshots/13afe5124825b4f3751f836b40dafda64c1ed062 \
  --out results/revision_c2/e2e_smoke_new
```

`--test-max-rows > 0` luôn đánh dấu **smoke_only**. Không đưa những số này vào bài.

Nếu cần giảm thời gian calibration nhưng vẫn đánh giá toàn bộ test, chọn trước subset validation theo query, không dựa nhãn:

```bash
.venv/bin/python scripts/revision_c2/run_e2e.py \
  --datasets primekg hetionet --edge-trials 6 \
  --calibration-max-rows 64 --offline \
  --model-path /home/anhlq/.cache/huggingface/hub/models--meta-llama--Llama-3.2-3B/snapshots/13afe5124825b4f3751f836b40dafda64c1ed062 \
  --out results/revision_c2/e2e_budget64
```

Không gọi thử nghiệm 2 dataset này là LODO-5 cho cạnh: edge LODO chỉ dùng các dataset trong lệnh. CPU `shared_lodo` vẫn dùng 5 dataset nếu phần CPU đã chạy đủ 5. Tham số `calibration-max-rows` là mục tiêu gần đúng vì giữ nguyên các nhóm query, có thể vượt vài dòng.

### E. Chạy lại một protocol CPU khác

```bash
RESULTS_DIR="$PWD/results/revision_c2_seed2027" \
  bash scripts/revision_c2/run.sh cpu --seed 2027 --repeats 10 --bootstrap 5000
```

E2E tương ứng:

```bash
RESULTS_DIR="$PWD/results/revision_c2_seed2027" \
  bash scripts/revision_c2/run.sh gpu --offline --seed 2027
```

Không chọn seed có test score tốt nhất. Nếu chạy nhiều seed để báo cáo, báo cáo đầy đủ mean/std hoặc phân phối.

## 3. Xuất và đọc file kết quả

Xuất lại bất kỳ lúc nào, kể cả khi GPU còn chạy:

```bash
.venv/bin/python scripts/revision_c2/export_results.py
```

Sau khi cả CPU/GPU hoàn tất, xác minh hash code/input, replay, selections, số hàng test, metrics tính lại từ predictions và cấu trúc file Excel/SVG:

```bash
.venv/bin/python scripts/revision_c2/verify_outputs.py
```

Lệnh kiểm tra này chủ động báo lỗi nếu GPU chưa hoàn tất hoặc chỉ chạy smoke; nó không tạo hay sửa kết quả thực nghiệm.

Xuất một thư mục E2E khác:

```bash
.venv/bin/python scripts/revision_c2/export_results.py \
  --results results/revision_c2 \
  --e2e-results results/revision_c2/e2e_budget64
```

| File | Nội dung |
|---|---|
| `exports/comment2_results.xlsx` | Workbook mở bằng Excel/LibreOffice, nhiều sheet cho tất cả thí nghiệm |
| `exports/REPORT.md` | Báo cáo tự sinh, phân biệt CPU/GPU/partial/smoke |
| `exports/report.html` | Bảng và hình để xem trên browser |
| `exports/candidate_mrr.svg` | Biểu đồ vector độc lập, có thể dùng để dựng hình supplementary |
| `exports/label_efficiency.svg` | Learning curves, mean/std qua calibration-subset seeds |
| `exports/learning_vs_equal.csv` | Bootstrap contrast trên cùng feature để tách tác dụng học trọng số |
| `exports/transfer_matrix.csv` | Ma trận nguồn–đích, đường chéo là within-dataset learned |
| `exports/edge_calibration_selection.csv` | Số vector validation đồng hạng tốt nhất, auto/LODO selections |
| `exports/edge_validation_trials.csv` | Toàn bộ 60 dataset/vector validation trials và các hệ số |
| `exports/e2e_paired_contrasts.csv` | CI của chênh lệch exact accuracy/adjusted MRR: so original, learned so equal, auto-edge so fixed-edge |
| `exports/table_candidate_main.tex` | Khối bảng LaTeX; khi chèn bài cần chỉnh width/caption phù hợp template |
| `exports/table_e2e.tex` | Có khi đã có kết quả E2E; kiểm tra trạng thái complete trước dùng |
| `candidate_metrics.csv` | Gold@20, MRR/Hits, conditional MRR, bootstrap delta vs original soft |
| `candidate_per_query.csv` | Rank/RR từng query từng variant để audit hoặc bootstrap lại |
| `candidate_models.json` | Trọng số, L2, nguồn calibration, các lựa chọn đã freeze |
| `native_validation_grid.csv` | Tất cả 224 cấu hình/dataset; chỉ validation metrics, không chọn theo test |
| `calibration_cv.csv` | CV traces cho hai learned models chính |
| `learned_weights.csv` | Hệ số shared learned và LODO |
| `label_efficiency.csv` | Từng subset/seed, số group, số nhãn recoverable, test metrics |
| `coefficient_sensitivity.csv` | Từng sigma/seed, MRR và tỷ lệ top1 giữ nguyên |
| `graph_weight_audit.csv` | Graph size, coverage, Jaccard, generic two-hop/relation retention |
| `input_audit.json` | Alignment, native replay, số query độc lập và overlap query valid/test |
| `protocol_cpu.json`, `input_hashes.json` | Protocol, phiên bản code, SHA256 inputs |
| `e2e/edge_validation_search.json` | Kết quả validation của từng vector cạnh |
| `e2e/frozen_edge_selection.json` | Trọng số cạnh chọn bằng validation và LODO; được ghi trước test |
| `e2e/e2e_metrics.csv` | Exact match, invalid, top1-copy, adjusted RR; hai experimental arms riêng |
| `e2e/predictions/...` | Output và score từng dòng |
| `e2e/cache/*.jsonl` | Cache theo checkpoint/model/input/graph; tránh lặp generation |
| `cpu_complete.json`, `e2e/e2e_complete.json` | Dấu hoàn tất; không suy ra hoàn tất từ việc chỉ có một CSV |

Script export không cần pandas/openpyxl/Matplotlib: XLSX tạo theo OOXML, hình SVG độc lập. CPU và exporter cần numpy; GPU dùng thư viện đã có trong `.venv`.

## 4. Thiết kế phương pháp và chống lẫn yếu tố

### 4.1 Native outer-weight calibration

Giữ `E,D,X` từ pipeline gốc, tối ưu:

`s = mu * prior + (1-mu) * minmax(E - beta*D - gamma*X)`

Minmax chỉ dùng nếu mu>0; trường hợp constant -> .5. Khi mu=0 giữ evidence score gốc. Grid:

- beta = 0, .1, .25, .5, .75, 1, 2.
- gamma = 0, .1, .2, .5.
- mu = 0, .25, .5, .75, .8, .9, .95, 1.
- Chọn validation MRR, tie ưu tiên mu lớn hơn rồi penalties nhỏ hơn.
- DRKG giữ secondary tie-break bằng evidence score của script gốc.

Đây là **automated search cho outer coefficients**, không làm cho feature E gốc trở thành learned hoặc common. Các hệ số bên trong E vẫn thuộc thiết kế gốc và được nêu rõ.

### 4.2 Shared features và learned linear calibrator

Mỗi ứng viên có 5 feature, không đọc gold/nhãn khi trích feature:

1. `(20-original_rank+1)/20`.
2. Cờ có cạnh trong source subgraph.
3. `min(1, log(1+source_degree)/log(101))`.
4. `min(1, log(1+number_of_shared_neighbors(candidate,query))/log(21))`.
5. Âm của cờ có cạnh trực tiếp candidate–query.

Degree đếm cạnh có quan hệ; shared neighbors dùng adjacency vô hướng, bỏ loại quan hệ. Đây là feature topology dùng chung, **không phải bằng chứng cơ chế sinh học**. Các hằng chuẩn hóa 101/21 được giữ chung, không tuning từng dataset. Bộ feature mới là một calibration baseline bổ sung, không lặng lẽ thay định nghĩa SoftFuse gốc.

Mô hình `score(c,q)=w^T x(c,q)`. Học bằng loss pairwise:

`mean log(1 + exp(-w^T(x_gold - x_negative))) + (lambda/2)||w||²`.

- Bản chính ép w>=0 vì dấu feature đã định trước; có đối chứng unconstrained.
- Dùng projected gradient descent với step size theo upper bound Hessian, 250 bước.
- L2 = .001/.01/.1/1; chọn bằng 5-fold CV chia theo query ID trên **validation dùng làm calibration pool**; cùng disease không nằm đồng thời train/held fold.
- Rows gold vắng top20 không tạo positive pair, vẫn giữ trong mẫu số khi đánh giá. Số recoverable rows được báo cáo.
- Các candidate là positive khác đã biết của cùng query trong calibration-training subset không bị dùng làm negative. Không dùng nhãn test để lọc negative.
- LODO cân bằng tổng pair weight giữa các dataset nguồn. Chọn L2 bằng held-source-dataset validation, không target validation.
- Equal-weight dùng đúng 5 feature này để tách tác dụng feature engineering khỏi tác dụng học hệ số.

### 4.3 Fuzzy edge calibration

Bộ score chung dùng band, candidate incidence, query incidence, negative direct-contact, density. Không có relation-family priority theo dataset. Band1/.6/.25 và density normalization giữ cố định chung; hệ số ngoài được chọn tự động.

- Bộ search mặc định gồm default, equal, bỏ shortcut penalty, chỉ band, tăng query weight/bỏ density, tăng shortcut penalty và 6 vectors log-normal ngẫu nhiên cố định seed.
- Chấm validation bằng **exact generated-answer accuracy**; tie dùng adjusted MRR rồi ưu tiên vector đứng trước. Nếu nhiều vector hoàn toàn tie, báo cáo sự thiếu tín hiệu, không khẳng định tìm được trọng số tối ưu duy nhất.
- Budget mỗi query bằng kích thước fuzzy graph gốc, source graph giống nhau, candidate order giống nhau: tách tác dụng **edge coefficients** khỏi budget/order.
- Coverage pass rồi fill; budget được áp dụng nghiêm; đo coverage thực tế thay vì mặc định 100%.
- LODO chọn vector theo macro accuracy/adjusted MRR của nguồn, loại toàn bộ validation score đích.
- Điều kiện LODO chỉ áp dụng cho bước hiệu chỉnh hệ số mới. Đặc biệt ở graph arm, candidate order của original fuzzy và ngân sách cạnh gốc được kế thừa từ pipeline lịch sử đã có thiết lập riêng theo dataset. Vì vậy không gọi toàn bộ pipeline là hoàn toàn không dùng calibration của dataset đích.
- Tất cả selections ghi file trước khi bắt đầu vòng test.

### 4.4 Hai E2E arms

Candidate arm: raw, original_soft, native_valid_grid, shared_equal, shared_learned, shared_lodo; giữ full source graph.

Graph arm: source_graph, original_fuzzy, shared_fixed, shared_auto, shared_edge_lodo; giữ order của original fuzzy row. Riêng repoDB order đó là raw/display control theo thiết kế gốc.

Dùng cùng raw-backbone checkpoint cho các variants trong một dataset; riêng PrimeKG và PharmKG dùng primary/main checkpoint tương ứng đã lưu của từng dataset. Không so checkpoint được fine-tune riêng cho từng variant; mục tiêu là frozen-checkpoint input intervention. Prompt được dựng nhất quán từ tên/ID mới; edges được sắp thứ tự nhất quán; truyền attention mask tường minh.

### 4.5 Evaluation

- Candidate absent gold: rank21, RR=0. Không dùng MRR thô từ `infer.py`.
- Match câu trả lời sau chuẩn hóa với đúng một candidate name/canonical ID; không substring matching; tên mơ hồ coi invalid.
- Primary generated metric: exact answer accuracy. Báo thêm invalid/top1-copy.
- Adjusted E2E rank: correct ->1; absent gold ->21; wrong candidate phía trên gold ->giữ rank; phía dưới/invalid ->gold rank+1, cap21.
- Invalid output vẫn có thể có adjusted RR khác0 nếu gold present. Điều này được công khai, không gọi adjusted RR là độ chính xác câu trả lời.
- CI bootstrap theo query cluster; candidate delta so original_soft; E2E candidate delta so raw và graph delta so source_graph. Có CI riêng cho exact accuracy.
- File `exports/e2e_paired_contrasts.csv` bổ sung so sánh trực tiếp với original_soft/original_fuzzy, learned/LODO với shared_equal, và auto/LODO-edge với shared_fixed. Mỗi hàng nêu rõ reference và metric; không nhầm delta của các reference khác nhau.
- CI chưa hiệu chỉnh multiple comparisons; dùng như uncertainty cho các phân tích exploratory, không tuyên bố mọi chênh lệch đều statistically significant.

## 5. Cách dùng để trả lời reviewer

Một bộ bằng chứng thuyết phục nên gồm:

1. Bảng chính: native original / fixed / auto-grid / shared equal / learned / LODO trên 5 dataset.
2. Bảng learned coefficients, feature definitions, CV và số calibration positives.
3. Transfer matrix 20 cặp nguồn–đích và LODO.
4. Đồ thị learning curve theo số calibration query và bảng sensitivity hệ số.
5. Bảng E2E tách candidate arm và graph arm, accuracy/invalid cùng adjusted MRR.
6. Bảng edge-weight search và graph stability, nêu rõ trường hợp tie hoặc giảm chất lượng.

Trong manuscript nên bổ sung một đoạn phương pháp automatic calibration và một đoạn kết quả chính; supplementary chứa đầy đủ protocol, bảng, uncertainty và limitations. Không cần dồn toàn bộ hơn trăm hàng kết quả vào manuscript.

**Không cam kết reviewer sẽ hài lòng chỉ nhờ nhiều thí nghiệm.** Để bảo vệ kết luận cần nói đúng: đây là transfer hệ số trên feature chung, không chứng minh zero-shot sang KG/task hoàn toàn mới; benchmark đã được nghiên cứu trước; native fuzzy budgets và rank bands vẫn là lựa chọn thiết kế. Nếu learned không hơn equal hoặc confidence interval chứa0, phải báo cáo như vậy.

## 6. Troubleshooting

- `Protocol changed`: đổi `--out`/`RESULTS_DIR`; không xóa protocol để chạy đè rồi gọi là cùng thí nghiệm.
- `Original soft-support replay failed`: xem input_audit, input version và feature alignment; không bỏ assert để chạy tiếp.
- CUDA unavailable: kiểm tra `nvidia-smi` và Python đúng `.venv`; trong Codex cần quyền ngoài sandbox.
- OOM: kiểm tra tiến trình GPU khác; script vốn batch1/FP16/3B. Không đổi sang 8B hoặc quantization giữa các rows của cùng run.
- HF offline model missing: truyền `--model-path` tới thư mục snapshot thực có config/tokenizer/weights. Không sử dụng Instruct checkpoint thay base model chỉ vì tên gần giống.
- Checkpoint thiếu file: từng dataset cần adapter weights/config, graph_model.bin và đúng entity embeddings. Không tự dùng checkpoint dataset khác.
- Job GPU dừng: chạy lại cùng lệnh; cache đã flush mỗi query. Không tự đánh dấu complete khi chưa có `e2e_complete.json`.
- Khi xem báo cáo giữa lúc chạy, E2E `not_complete` là đúng; exporter không tự điền metric còn thiếu.
