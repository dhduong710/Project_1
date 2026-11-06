# Sửa ảnh hưởng FP16 trong thực nghiệm Comment 2 — 06/11/2026

## Phạm vi đã sửa

Đã chạy lại toàn bộ phần GPU của Comment 2 bằng **graph encoder FP32 + LLM BF16**, cùng chính sách ổn định đã dùng ở Comment 3. Graph checkpoint được load trực tiếp FP32; base LLM và PEFT được load trực tiếp BF16. Có kiểm tra dtype và finite trước/sau cast; không clipping, không bỏ mẫu.

- **Giữ nguyên CPU:** native grid, candidate ranks, shared learned coefficients, CV/LODO, transfer matrices, label-efficiency, coefficient sensitivity và graph topology audits. Các file được kiểm tra hash; lỗi FP16 inference không nằm trong các phép tính này.
- **Chạy lại validation GPU:** đủ 12 vectors × 5 datasets = 60 trials; chọn lại auto/edge-LODO theo cùng quy tắc, freeze trước test.
- **Chạy lại test GPU:** đủ 6 candidate variants + 5 graph variants × 5 datasets = 55 summaries, 23.100 lượt đánh giá row–variant.
- **Thêm 10 đối chứng GPU:** giữ auto/LODO coefficients cũ nhưng dùng precision mới, tổng 4.200 lượt đánh giá. Nhờ đó tách được thay đổi precision ở cùng lựa chọn cũ khỏi thay đổi do validation chọn lại coefficients.
- **Audit encoder:** actual graph inputs của cả protocol cũ và mới, gồm validation/test. Tái dùng phép tính chỉ khi query, candidate order và edge multiset trùng nhau.

Đây vẫn là cùng 2.100 validation và 2.100 test rows. Không coi các lượt đánh giá qua variants là những mẫu độc lập mới. Các đối chứng bổ sung không tham gia lựa chọn mô hình.

## Kết quả số học

Audit 10.765 encoder inputs khác nhau tìm thấy 22 calls nonfinite khi chạy FP16, tất cả thuộc PrimeKG; FP32 và phép cast sang BF16 hữu hạn ở toàn bộ inputs.

Trong mỗi biến thể PrimeKG dùng full source graph, có 9 test rows lỗi FP16. Có 7 biến thể như vậy: 6 candidate-order variants và graph/source_graph. Do đó có 63 row–variant evaluations bị ảnh hưởng trong mỗi run; đây không phải 63 test samples khác nhau. Trong 6 rows mỗi biến thể, ngay cả FP32 encoder output cũng overflow nếu cast về FP16. Max FP32 projection là 130.444,35, vượt FP16 max 65.504.

Các validation edge-trial graphs và compressed test graphs đã audit không có nonfinite FP16 outputs. Tuy vậy, outputs hữu hạn vẫn có thể thay đổi khi đổi precision; cần chạy lại đồng nhất cả study, không chỉ vá các rows bị overflow.

## Lựa chọn trọng số thay đổi

Trial IDs bắt đầu từ 0, theo search list cố định ban đầu:

| Dataset | Auto cũ → mới | Edge-LODO cũ → mới | Số vectors đồng hạng tốt nhất cũ → mới |
|---|---|---|---|
| PrimeKG | 1 → 1 | 0 → 2 | 6 → 6 |
| PharmKG | 0 → 3 | 7 → 2 | 12 → 2 |
| Hetionet | 0 → 0 | 7 → 2 | 12 → 12 |
| DRKG | 0 → 0 | 7 → 2 | 12 → 12 |
| repoDB | 0 → 2 | 1 → 3 | 8 → 1 |

Vì vậy phải sửa câu cũ “cả 12 vectors tie trên PharmKG, Hetionet, DRKG”. Sau sửa precision, câu này chỉ còn đúng trên Hetionet và DRKG.

## Predictions và metrics thay đổi

| Dataset | Prediction changes trên test row–variants | Hàng có exact accuracy đổi | Hàng có adjusted MRR đổi |
|---|---:|---:|---:|
| PrimeKG | 248 / 5.500 | 0 | 3 |
| PharmKG | 183 / 5.500 | 0 | 9 |
| Hetionet | 20 / 1.100 | 0 | 1 |
| DRKG | 10 / 5.500 | 0 | 0 |
| repoDB | 218 / 5.500 | 1 | 2 |
| Tổng | **679 / 23.100** | **1 / 55** | **15 / 55** |

Prediction changes dùng cùng normalized-answer rule. Tất cả 63 lượt có encoder FP16 nonfinite đổi prediction; còn 616 lượt đổi prediction có encoder FP16 hữu hạn. Nhóm sau bao gồm cả thay đổi arithmetic và thay graph do reselection, không được quy tất cả cho overflow.

Trên repoDB, edge-LODO mới đạt **1/500 = 0,2%**, so với **2/500 = 0,4%** trước sửa. Đối chứng giữ coefficients cũ tại precision mới vẫn đạt 0,4%: phần giảm exact accuracy này đến từ reselection trong so sánh cùng stable precision. Original fuzzy/shared fixed/shared auto hiện đều đạt 0,4%. Câu cũ “mọi compressed graph variants có exact accuracy giống nhau trên mọi dataset” đã được sửa.

Các kết luận candidate-level giữ nguyên: learned không luôn vượt equal; tăng candidate MRR không đảm bảo tăng generation accuracy. Bảng accuracy candidate-arm vẫn giữ các point estimates đã báo, nhưng một số predictions/invalid rates/adjusted MRR thay đổi. Không lấy sự bất biến accuracy để bỏ qua lỗi số học.

## File hiện hành và file lưu trữ

- Kết quả sửa: `../../results/revision_c2/e2e_stable/`.
- Workbook hiện hành: [comment2_results.xlsx](../../results/revision_c2/exports/comment2_results.xlsx).
- Bản PDF đã cập nhật: [supplementary_preview.pdf](supplementary_preview.pdf).
- Bản trả lời reviewer đã cập nhật: [response_comment2_draft.md](response_comment2_draft.md).
- Mọi khác biệt và phân rã: `../../results/revision_c2/precision_comparison/`.
- Audit số học: `../../results/revision_c2/precision_audit/`.
- Prediction FP16 cũ: `../../results/revision_c2/e2e/`; exports/draft cũ: `../../results/revision_c2/legacy_fp16_snapshot/`. Chỉ dùng để audit, không phải số liệu revision hiện hành.
- Chạy lại, resume, export và verify: [README](../../scripts/revision_c2/README.md).

Stable cache từ C3 chỉ được nhập khi full fingerprint và exact input key khớp. Không nhập cache FP16. Mười C2/C3 anchor checks xác nhận các inputs chung cho cùng prediction; vì có tái dùng cache, đây là kiểm tra tính nhất quán, không phải một lần tái lập inference độc lập.

Các bảng LaTeX GPU trong supplementary được sinh từ kết quả mới. Các đoạn diễn giải là bản chèn riêng để rà soát, chưa thay nguồn manuscript/ESM/response DOCX gốc. Không ghép số historical collectors có metric khác vào bảng mới.
