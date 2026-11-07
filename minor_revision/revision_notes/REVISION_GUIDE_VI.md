# Manuscript và supplementary đã tích hợp revision

Bản sửa đầu ngày 06-11-2026, tinh gọn ngày 07-11-2026 theo góp ý mới của tác giả, dựa trên các bộ kết quả C2/C3 đã hoàn tất. Không thay đổi runner, checkpoint hoặc kết quả thực nghiệm.

## File để đọc/gửi

- `minor_revision/Manuscript_revised_highlighted.pdf`: manuscript, 25 trang.
- `minor_revision/Supplementary_revised_highlighted.pdf`: supplementary, 30 trang.
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
- Code availability dùng `https://github.com/dhduong710/SoftFuse-KGC`, là repo tác giả đã dọn để publish. Không đổi Git remote của bản làm việc. Không sửa Response to Reviewers.docx, không commit/push.

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

## Tinh gọn ngày 07-11-2026

- Bôi vàng theo bản nộp gốc: câu/từ/ô số liệu sửa được đánh dấu riêng; đoạn thêm mới hoặc viết lại toàn bộ giữ nền vàng. Các câu mở đầu abstract/discussion và các ô E2E không đổi được trả về nền trắng.
- Related Work chủ yếu mô tả các công trình liên quan; so sánh trực tiếp với SoftFuse-KGC còn hai câu.
- Rút gọn 4.5/4.6, giữ thiết kế, kết quả chính, đối chứng equal weights và giới hạn diễn giải cần thiết. Table 5 đặt ngay dưới Table 4 trên cùng trang.
- Supplementary lược diễn giải phụ về gene-annotation, case audit và output-format. Giữ nguyên toàn bộ bảng đối chứng, kết quả mất path, exact generation và các giới hạn trực tiếp liên quan đến comment 2/3. Các artifacts thực nghiệm không bị xoá hay sửa.
- Kiểm tra lại số liệu từng cột sau thay đổi markup, dẫn chiếu, citation, vị trí hai bảng và PDF.

## Hoàn thiện comment 4–6 và dàn trang ngày 07-11-2026

- Đã bỏ toàn bộ phần nhắc trực tiếp SoftFuse-KGC trong Related Work. Hai công trình reviewer yêu cầu ở comment 6 đã có đủ citation; Discussion bổ sung cách học biểu diễn/trọng số theo từng nguồn, kết hợp mục tiêu ranking với ngân sách graph và giữ đường dẫn bằng chứng. Đây là hướng mở rộng, không phải thực nghiệm đã thực hiện.
- Comment 4: thêm đoạn ngắn ở Section 4.2 phân biệt cải thiện thứ hạng trong danh sách cố định, độ bao phủ truy hồi và đánh giá generated answers. Response letter để lượt sau theo yêu cầu tác giả.
- Comment 5: Section 4.1 làm rõ join theo ID DrugBank và dẫn tới S11.1 mới. Supplementary mô tả chuẩn hóa ID, nhãn và deduplication; xử lý 21 cặp mâu thuẫn; mapping compound 1.130/1.571 và approved compound 1.106/1.519; không thực hiện crosswalk UMLS–DRKG; giữ entity không match; xây graph/caps; chia tập và exact leakage checks. Table S15 phân biệt local graph-ID coverage với cross-resource alignment.
- Đã đọc code `scripts/week28/02_normalize_freeze_repodb_task.py`, `03_build_repodb_splits_graph.py`, `05_build_repodb_fograg_ready.py`, `06c_make_repodb_rgcn_raw_display_control.py`. Audit tái dùng các hàm normalize/split/build trong bộ nhớ và xác nhận khớp artifacts, gồm toàn bộ 90.804 cạnh; không chạy main() của các script preparation và không ghi lại dataset.
- Audit và hashes: `revision_notes/comment5_alignment_audit.json`. Có thể chạy lại bằng `.venv/bin/python minor_revision/audit_repodb_alignment.py` từ repo root. Verifier kiểm tra hashes của code và dữ liệu nguồn audit.
- Manuscript dùng một float cho Table 4–5 để phần văn bản tiếp tục lấp trang 14, hai bảng vẫn liền nhau ở trang 15. Dùng `tableorg` của class Springer để tránh wrapper `threeparttable` làm sai độ rộng caption khi có hai bảng trong cùng float.
- Supplementary bỏ ngắt trang cưỡng bức sau S1.2; Table S1 chuyển sang `longtable` có header tiếp nối trên trang 4–5. Bỏ ngắt trang trước S12 để nội dung chảy tiếp sau S11.1. Nội dung/số liệu Table S1 giữ nguyên.
- Bản xuất cuối: manuscript 25 trang, supplementary 30 trang. Đã kiểm tra trực quan các trang sửa, build không có undefined reference hoặc overfull box, verifier pass, `git diff --check` pass. Bôi vàng tiếp tục theo bản nộp gốc: câu/từ sửa riêng, đoạn mới toàn bộ. Public URL vẫn SoftFuse-KGC; không sửa kết quả C2/C3, response DOCX, remote hoặc commit/push.
