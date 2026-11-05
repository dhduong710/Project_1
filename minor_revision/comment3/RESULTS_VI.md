# Đọc kết quả thực nghiệm cho Comment 3

Reviewer yêu cầu **định lượng information retention khi chọn cạnh** và **so sánh với các chiến lược chọn subgraph khác**. Bộ bổ sung trả lời cả hai, đồng thời kiểm tra tác động tới encoder và câu trả lời LLM. Các nguồn manuscript/supplementary gốc chưa bị ghi đè.

## 1. Đã kiểm tra những gì?

- Toàn bộ 5 datasets: PrimeKG, PharmKG, Hetionet, DRKG, repoDB.
- 620 bảng con CPU: 62 variants × 5 datasets × valid/test; thêm 60 bảng audit implementation native.
- 140 bảng con GPU: 28 variants × 5 datasets trên toàn bộ test.
- 5 seeds cho random và random + coverage ở budget gốc; 3 seeds cho random trên 5 tỷ lệ budget.
- Coverage, connectivity, exact paths, relation patterns/distributions, incoming context, encoder similarity/L2 và generated-answer metrics.
- Native replay khớp tập cạnh gốc 100% ở cả valid/test; không suy đoán công thức từ manuscript rồi coi đó là implementation gốc.
- Bootstrap theo query cluster; báo riêng seed standard deviation và khoảng tin cậy.
- 20 case minh họa giữ/mất đường đi, chọn theo structural strata sau phân tích; không chọn theo câu trả lời tốt.

Các variants vẫn dùng lại cùng 2.100 valid và 2.100 test rows. 58.800 lượt GPU không có nghĩa là 58.800 test samples độc lập. Cần kiểm tra `cpu_complete.json` và `gpu/gpu_complete.json` trước khi dùng số cho bài.

## 2. Fuzzy giữ coverage nhưng không giữ nguyên mọi kết nối

Tại cùng số unique edges với fuzzy gốc, retention kết nối query–candidate trong tối đa 3 cạnh:

| Dataset | Số rows có source connectivity | Fuzzy | Random, mean 5 seeds | Shortest paths |
|---|---:|---:|---:|---:|
| PrimeKG | 488 | 0.7737 | 0.7760 | 0.9985 |
| PharmKG | 500 | 0.9010 | 0.4423 | 1.0000 |
| Hetionet | 90 | 0.4835 | 0.4848 | 1.0000 |
| DRKG | 386 | 0.8921 | 0.5043 | 1.0000 |
| repoDB | 297 | 0.9546 | 0.5465 | 1.0000 |

Fuzzy bảo toàn incidence coverage của các candidate vốn được source bao phủ trên cả 5 datasets. Tuy nhiên, kết nối query–candidate chỉ tốt hơn random rõ trên PharmKG, DRKG và repoDB. Khoảng tin cậy của chênh lệch random−fuzzy trên PrimeKG/Hetionet chứa 0. Không nên viết fuzzy tốt hơn random trên mọi dataset.

Shortest paths tối ưu trực tiếp việc giữ đường nối nên đạt connectivity cao; đổi lại, candidate incidence coverage giảm xuống 0.8514/0.8199/0.8971 trên Hetionet/DRKG/repoDB, so với 1.0000 của fuzzy. Đây là trade-off cần trình bày, không nên chỉ dùng một metric để xếp hạng mọi selector.

## 3. Path retention cho thấy phần thông tin bị mất

Retention của exact edge-labeled simple paths dài **đúng 3 cạnh**:

| Dataset | Rows có source path | Fuzzy | Random, mean 5 seeds | Shortest paths |
|---|---:|---:|---:|---:|
| PrimeKG | 488 | 0.6543 | 0.6443 | 0.8199 |
| PharmKG | 31 | 0.0000 | 0.1801 | 0.8604 |
| Hetionet | 64 | 0.0000 | 0.1615 | 0.6207 |
| DRKG | 201 | 0.4767 | 0.1629 | 0.6496 |
| repoDB | 219 | 0.5286 | 0.1552 | 0.8322 |

PharmKG chỉ có 31 rows có source path dài 3; không suy rộng giá trị 0 thành “mọi query mất toàn bộ connectivity”. Có thể vẫn còn path ngắn hơn. Paths được duyệt hai chiều nhưng giữ relation/direction signature; chúng là bằng chứng cấu trúc, chưa phải cơ chế điều trị được chuyên gia xác thực.

## 4. Cạnh lặp và budget cần trình bày đúng

PrimeKG có trung bình 59.932 edge occurrences nhưng chỉ 38.094 unique triples; fuzzy giữ 32.340 unique triples. Trong tổng reduction 27.592 occurrences, có 21.838 do loại bản sao và 5.754 do loại unique triples. Khoảng 79.1% count reduction là deduplication. Không gọi toàn bộ phần giảm này là loại bỏ quan hệ độc lập.

Audit code native cho thấy PrimeKG có thể vượt target khi ép budget xuống thấp: tại 20%, mean requested/actual là 7.576/15.662, 99.8% rows vượt target. Đây là hành vi coverage pass gốc. Budget artifact gốc vẫn hợp lệ trong so sánh chính. Các đường cong strict-budget dùng control riêng và chọn đúng số cạnh yêu cầu.

## 5. Giữ dự đoán không đồng nghĩa giữ thông tin

Fuzzy so với source raw:

| Dataset | Answer agreement | Candidate cosine | Query cosine | Exact accuracy fuzzy |
|---|---:|---:|---:|---:|
| PrimeKG | 78.8% | 0.9453 | 0.8828 | 0/500 = 0.0% |
| PharmKG | 80.0% | 0.9991 | 0.8718 | 1/500 = 0.2% |
| Hetionet | 100% | 1.0000 | 0.9209 | 3/100 = 3.0% |
| DRKG | 100% | 0.9867 | 0.9312 | 7/500 = 1.4% |
| repoDB | 80.8% | 0.9806 | 0.9814 | 2/500 = 0.4% |

Hetionet giữ nguyên candidate embeddings và câu trả lời, nhưng query embeddings thay đổi và source paths dài 3 bị mất. Đây là ví dụ trực tiếp cho thấy cần đo cả topology, encoder và generation.

Không có lợi thế accuracy đồng đều cho fuzzy. Ví dụ repoDB native top-k đạt 11/500, trong khi empty-local-graph đạt 9/500. Empty vẫn dùng global entity embeddings; không phải mô hình “không có tri thức graph”. Không chọn lại default theo các kết quả test này.

Exact accuracy ở đây dùng matching chuẩn hóa chặt với candidate names. Adjusted MRR là metric khác, có thể dương khi không có câu trả lời đúng vì còn credit từ candidate order. PharmKG có 59% fuzzy outputs không khớp candidate theo rule này. Không trình bày adjusted MRR như generation accuracy hoặc suy diễn invalid outputs là đáp án sinh học hợp lệ.

## 6. Phát hiện về precision

FP16 graph encoder sinh nonfinite outputs ở 9 source cases của PrimeKG. FP32 hữu hạn ở toàn bộ 4.200 source/fuzzy cases đã audit, nhưng max projection 130.444,35 vẫn vượt miền FP16 (65.504). Vì vậy run chính dùng **encoder FP32 + LLM BF16**, kiểm tra finite trước/sau cast, không clipping và không loại mẫu.

Không ghép các số E2E này trực tiếp vào bảng FP16 lịch sử hoặc Comment 2. CPU structural/candidate metrics không phụ thuộc lỗi precision này. Nếu dùng lại C2 GPU raw-graph contrasts để kết luận, cần audit/rerun riêng với precision nhất quán.

## 7. Nên đưa vào revision như thế nào?

- **Manuscript:** dùng `manuscript_insert.tex`, một bảng matched-budget chính, và kết luận coverage-oriented compression có trade-off.
- **Supplementary:** dùng methods + structural results + GPU results, 3 hình, eligibility counts, seed/CI tables, native budget audit và case examples. Xem `supplementary_preview.pdf`.
- **Response:** dùng `response_comment3_draft.md`, gắn section/table numbers thật sau tích hợp.
- **Dữ liệu:** workbook `../../results/revision_c3/exports/comment3_results.xlsx`; báo cáo tự sinh `../../results/revision_c3/exports/REPORT.md`.
- **Chạy lại/xuất lại:** hướng dẫn `../../scripts/revision_c3/README.md`.

Không dùng các kết luận “lossless”, “giữ nguyên mọi thông tin”, “bảo toàn cơ chế điều trị” hoặc “tốt hơn mọi baseline”. Kết quả hỗ trợ một phân tích định lượng có trade-off, với cả điểm mạnh và giới hạn được kiểm chứng.
