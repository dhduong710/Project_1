# Manuscript và supplementary đã tích hợp revision

Bản sửa ngày 06-11-2026, dựa trên HEAD `ae70903` và các bộ kết quả C2/C3 đã hoàn tất. Không thay đổi runner, checkpoint hoặc kết quả thực nghiệm.

## File để đọc/gửi

- `minor_revision/Manuscript_revised_highlighted.pdf`: manuscript, 26 trang.
- `minor_revision/Supplementary_revised_highlighted.pdf`: supplementary, 29 trang.
- PDF tương ứng cũng nằm cạnh nguồn `sn-article.tex` và `ESM_1.tex` trong hai thư mục gốc.
- Các đoạn/câu, ô số liệu, phần bổ sung và sáu tài liệu tham khảo mới được đánh dấu nền vàng. Với Fig. 2 được tính lại, caption được bôi vàng và file hình mới mang tên `Fig2_revised.pdf`.

## Nội dung đã sửa

| Yêu cầu | Manuscript | Supplementary |
|---|---|---|
| Comment 1 | Related Work bổ sung G-RAG, G-Retriever, GRAG, SubgraphRAG; phân biệt rerank ứng viên, chọn bằng chứng và học biểu diễn graph. Thu hẹp phát biểu đóng góp trong abstract, introduction, discussion, conclusion. | Phân biệt candidate incidence với connectivity/path retention. |
| Hai bài ở Comment 6 | Thảo luận spatial–spectral fusion và FD-MSGL trong Related Work, cùng hướng mở rộng multi-source fusion trong Discussion. Không tuyên bố đã thực nghiệm trực tiếp hai hệ thống này. | Không thêm đối chứng chưa chạy. |
| Comment 2 | Section 4.5 và Table 4: original/equal/learned/LODO trên đủ năm datasets; nêu rõ giới hạn của học trọng số và transfer. | S12, Tables S16–S24: objective, features, native grid, weights, CI, transfer, label efficiency, ablation, perturbation, candidate-generation và edge-calibration. |
| Comment 3 | Section 4.6 và Table 5: matched-budget retention, so sánh random/shortest paths, phân biệt incidence và reachability. | S13, Tables S25–S29, Figs. S4–S6: đầy đủ selector families, path retention, relation/context diagnostics, generation, encoder changes, budget curves. |

Các kết quả hạn chế/không thuận lợi có ý nghĩa khoa học được giữ trong supplementary, gồm learned-vs-equal không thắng đều, repoDB generation, path losses, và selector khác tốt hơn ở một số tiêu chí. Manuscript tóm tắt giới hạn để tránh kết luận vượt dữ liệu. Không đưa lịch sử lỗi FP16 hoặc các bước debug vào nội dung hai tài liệu.

## Đồng bộ số liệu

- Table 3 E2E và phần diễn giải dùng `results/revision_c2/e2e_stable/e2e_metrics.csv`, cùng quy tắc adjusted rank và exact matching với S12/S13. Vì vậy một số giá trị E2E cũ ở abstract/results/discussion đã được sửa; không trộn số cũ và mới trong cùng bảng.
- Các so sánh generator/decoding trước đây ở S7 được giữ thành nhóm diagnostic riêng, có câu dẫn phân biệt với protocol hiện hành. Không tái chạy các larger-model experiments.
- Fig. 2 và các giá trị validation tương ứng ở S1/S6/S9 được tính lại từ candidate IDs với absent-gold RR=0: raw 0.053803; ontology 0.003917; bcap 0.054464; soft 0.097644; encoder probe 0.053707. `validation_metric_check.json` ghi nguồn và hashes. Không thay đổi thứ tự ứng viên.
- Công thức capped support được đồng bộ phép chia cap=2; mô tả invalid output và fixed-order edge-drop được chỉnh để tránh hiểu sai về accuracy/retention.
- `table_sources.json` ghi hashes các nguồn CSV/markers; bảng được xuất bằng script để giảm lỗi chép số.
- Đường dẫn Code availability đổi sang Project_1. Không sửa Response to Reviewers.docx, không commit/push.

## Biên dịch lại

Từ Git repository:

```bash
cd /home/anhlq/Documents/2026-dhd/SoftFuse-KGC
python3 minor_revision/build_revision.py
python3 minor_revision/verify_revision.py
```

Script tự xuất lại bảng, tính lại figure validation, chạy pdflatex/BibTeX trong thư mục tạm, bôi vàng toàn bộ sáu bibliography entries mới, kiểm tra lỗi references/overflow, và xuất hai PDF. Không dùng GPU và không chạy lại thực nghiệm.

Server thiếu `algorithm`/`algorithmic`, nên đã bổ sung bản CTAN nguyên gốc cạnh supplementary cùng source/license trong `latex_vendor/algorithms/`. Các gói LaTeX khác dùng TeX Live hiện có. Nguồn và figure/table inputs đã nằm trong hai folder gốc, không phụ thuộc vào đường dẫn kết quả tương đối khi biên dịch LaTeX thủ công. Tuy nhiên nên dùng script trên để bibliography entries mới cũng được bôi vàng.

Các file nguồn bổ sung chính:

- `Main Manuscript/paper/revision_results.tex`
- `Supplementary Materal/Supplementary Materal/revision_calibration.tex`
- `Supplementary Materal/Supplementary Materal/revision_retention.tex`
- `revision_highlight.tex` trong từng folder điều khiển màu vàng.

## Nguồn học thuật đã xác minh

- Spatial–spectral fusion (2026): https://pubmed.ncbi.nlm.nih.gov/42573507/ — DOI 10.1093/bioinformatics/btag553.
- FD-MSGL (2026, early access): https://pubmed.ncbi.nlm.nih.gov/42048211/ — DOI 10.1109/JBHI.2026.3688381.
- G-RAG (2024, arXiv): https://arxiv.org/abs/2405.18414.
- G-Retriever (NeurIPS 2024): https://proceedings.neurips.cc/paper_files/paper/2024/hash/efaf1c9726648c8ba363a5c927440529-Abstract-Conference.html.
- GRAG (Findings NAACL 2025): https://aclanthology.org/2025.findings-naacl.232/.
- SubgraphRAG (ICLR 2025): https://proceedings.iclr.cc/paper_files/paper/2025/hash/11e1900e680f5fe1893a8e27362dbe2c-Abstract-Conference.html.
