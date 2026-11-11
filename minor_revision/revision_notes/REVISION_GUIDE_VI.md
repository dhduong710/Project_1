# Manuscript và supplementary đã tích hợp revision

Bản sửa đầu ngày 06-11-2026, tinh gọn ngày 07-11-2026 theo góp ý mới của tác giả, dựa trên các bộ kết quả C2/C3 đã hoàn tất. Không thay đổi runner, checkpoint hoặc kết quả thực nghiệm.

## File để đọc/gửi

- `minor_revision/Manuscript_revised_highlighted.pdf`: manuscript, 25 trang.
- `minor_revision/Supplementary_revised_highlighted.pdf`: supplementary, 28 trang.
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
- RankRAG (NeurIPS 2024), thay G-RAG ở lượt soạn response letter: https://proceedings.neurips.cc/paper_files/paper/2024/hash/db93ccb6cf392f352570dd5af0a223d3-Abstract.html — DOI 10.52202/079017-3850.
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

## Response letter và thay citation 50 — 07-11-2026

- Đã đọc `response letter-phương.docx` để tham khảo bố cục, rồi tạo `minor_revision/Response to Reviewers_revised.docx` từ template `Response to Reviewers.docx`. Giữ nguyên submission metadata và toàn bộ lời reviewer; không sửa hai file Word đầu vào. Không sử dụng các lập luận/kết quả của bài mẫu cho SoftFuse-KGC.
- Thêm 6 ý sau “Overall, our revised manuscript has main changes as follows:” và đủ 6 Author response. Mỗi phản hồi bắt đầu bằng cảm ơn, giải thích/phân tích liên quan, kết quả và vị trí sửa. Tổng khoảng 1.897 từ, bao gồm toàn bộ reviewer comments và bảng số liệu.
- C4 phân biệt fixed-coverage candidate ranking, adjusted E2E MRR và exact-answer accuracy; nêu cả 1/500 source và 0/500 soft/fuzzy PrimeKG. Khai báo 9/500 full-source PrimeKG cases gặp FP16 overflow; sửa bằng FP32 graph/BF16 LLM, giữ checkpoint/split và không loại mẫu, validation reselection trước test. Nói riêng việc thống nhất answer matching/adjusted-rank giữa các collector, không quy mọi số thay đổi cho FP16.
- Table R1 liệt kê toàn bộ 15 giá trị Table3 trước→sau. Cột trước lấy trực tiếp từ source snapshot `ae70903`; cột sau từ stable CSV. Khai báo thêm validation candidate MRR Fig2/S1/S6/S9 được tính lại với absent-gold RR=0. S7 historical model/decoding diagnostics được phân biệt với current standardized comparisons; không nhận đã chạy lại mọi historical model.
- Citation50 G-RAG arXiv được thay bằng RankRAG, NeurIPS37(2024),121156–121184,DOI10.52202/079017-3850. Câu RelatedWork sửa theo đúng phương pháp instruction-tuning cho context ranking và answer generation; không giữ mô tả GNN của G-RAG. Đã xác minh publisher proceedings. Sáu bibliography additions vẫn bôi vàng; thứ tự50 và citations45–46 không đổi.
- Nguồn response chỉnh sửa được: `revision_notes/response_content.json`; script `python3 minor_revision/build_response_letter.py`; bản text rà soát `revision_notes/response_letter_text.txt`; metadata/hashes/bảng correction `revision_notes/response_letter_manifest.json`. Script dùng OOXML chuẩn, giữ styles của template, không cần python-docx.
- Kiểm tra: toàn bộ XML/relationships trong DOCX hợp lệ; Pandoc đọc lại đủ6responses vàTableR1; reviewer comments và template gốc giữ nguyên; exact counts và9FP16cases khớpCSV; PDF verifier và `git diff --check` pass. Không có Word/LibreOffice renderer trên server, nên không xác nhận phân trang Word bằng render; PDF manuscript/supplementary biên dịch thành công25/30trang. Không chạy lại thực nghiệm, không sửa dữ liệu/results.

## Tinh gọn response letter — 08-11-2026

Theo góp ý mới, đã đổi toàn bộ dòng “Revisions:” thành câu văn nêu vị trí sửa; bỏ “published” và câu về conference versions khi nhắc các công trình. Comment3 diễn đạt số reachability kèm từng dataset, không dùng chuỗi nối bằng dấu /. Các đoạn phản hồi và summary mới được căn trái để tránh giãn khoảng trắng; nguyên văn reviewer/template được giữ lại.

Comment4 rút còn286từ, bỏTableR1 và dùng ví dụ PrimeKGsource.0476→.0477. Giữ khai báo FP16, precisionpolicy, scoringharmonization, không loại mẫu, validationselection trước test, phân biệt adjustedMRR/exactaccuracy và validationmetriccorrection. Full15old/newvalues chỉ còn ở manifest đểaudit, không trongWord. DOCX1730từ tổng,6responses; ZIP/XML/Pandocreadback và alignmentchecks pass. Scriptbuild đã cậpnhật đểrebuild không thêm lại bảng. Chỉ sửaresponseletter, không sửamanuscript/supplementary hoặc chạyexperiments.

## Sửa khoảng trống khi chuyển trang — 08-11-2026

Ngày08-11-2026 sửa tiếp khoảng trống cuối trang response: xác định keepNext chain ở Comment → Author response → first answer. Builder bỏchain, explicit keepNext/keepLines/pageBreakBefore/snapToGrid=0 trênmọiparagraph, giữwidowControl=1, xóa cachedpagebreaks và hardpage/columnbreak nếu có; single-spacing0before/aftergiữnguyên. Nội dung1730từ khôngđổi, XMLchecks vàPandocreadbackpass. BảncanonicalResponse to Reviewers_revised.docx cậpnhật; bảndelivery mớiResponse to Reviewers_layout_fixed.docx đểphânbiệtfileđãmởtrước. BuildergiữhaiWordđồngbộ. KhôngcóconnectedWordsession; khôngrendertrựcquanWord, chỉkiểmtraOOXMLpagination. KhôngsửaPDF/paper/results.

Ngày08-11-2026 tác giả xác nhận đã hết khoảngtrốngcuốitrang nhưngdòngquását. Đã đọcspacing của toàn88paragraph trong response letter-phương.docx: line300auto=1.25dòng,before50/after50=2.5pt. Ápdụngđúngprofile này cho50paragraph response hiện tại; giữkeepNext/keepLines/pageBreakBefore/snapToGrid=0 vàkhôngemptyspacers. HaiWordcanonical/layout_fixed đồngbộ; kiểmtraXMLtừngparagraphkhớpsample, paginationfixgiữnguyên, text1730words khôngđổi. BuilderdùngPARAGRAPH_SPACINGconstant, manifestcậpnhật.


## Hòa trộn manuscript và sửa Fig. 2 — 11-11-2026

- Abstract, contributions và conclusion ưu tiên soft support và confidence-aware fuzzy retrieval. Abstract chỉ dùng hai câu cho phân tích calibration/retention bổ sung; conclusion chỉ một câu. Bỏ “adjusted” trong abstract và các đoạn đối chiếu với exact generation/exact-answer accuracy khỏi manuscript; giữ định nghĩa rank update tại Section 4.2 và nội dung đánh giá chi tiết trong supplementary.
- Section 2.1 nối hai nghiên cứu spatial–spectral và FD-MSGL với nhóm phương pháp học từ nhiều biological networks. Related Work vẫn không nhắc SoftFuse-KGC. Rút gọn các đoạn bổ sung trong Results/Discussion, giữ giới hạn của equal-weight controls, transfer và connectivity.
- Sections 4.5/4.6 giới thiệu bảng bằng câu hoàn chỉnh dùng macro Table như phần còn lại của bài. Tables 4–5 vẫn liền nhau trong cùng float. Không thay số liệu, checkpoint, runner hoặc kết quả thực nghiệm.
- Fig. 2a/b đặt legends dưới trục, tách khỏi dữ liệu và tick labels; cập nhật cả generator để rebuild giữ bố cục mới. Giá trị đồ thị không đổi. Đã kiểm tra hình riêng và hình trong PDF.
- Bỏ câu về UMLS-to-DRKG crosswalk trong main; giữ mô tả exact DrugBank join và liên kết S11.1. Supplementary Information liệt kê S1–S11 rồi S12–S13, Tables S1–S15 rồi S16–S29, cuối cùng Figs. S1–S3 và S4–S6.
- Kiểm tra lại sáu tài liệu bổ sung theo nguồn học thuật bên trên: tác giả, tiêu đề, venue, năm, DOI/URL. Spatial–spectral dùng article identifier btag553 trong trường eid/note vì Springer style loại chữ khi xử lý trường pages (tránh in sai thành trang 553). G-Retriever bổ sung pp. 132876–132907 theo publisher proceedings (https://www.proceedings.com/079017-4224.html). FD-MSGL giữ Early access do nguồn hiện có chưa cung cấp tập/số/trang cuối. Bibliography dùng cùng Springer style và bôi vàng sáu entries bổ sung.
- Lượt này chỉ xuất lại manuscript, giữ nguyên supplementary PDF và response DOCX. Có thể rebuild riêng bằng `python3 minor_revision/build_revision.py --manuscript-only`, rồi `python3 minor_revision/verify_revision.py`. Bản main vẫn 25 trang; các từ/câu sửa trong đoạn cũ bôi riêng, đoạn viết lại hoặc thêm mới bôi toàn đoạn.


## Rà soát câu văn, abstract, limitations và legend — 11-11-2026

- Đọc trực tiếp `minor_revision/Main Manuscript.pdf` bằng trích xuất PDF text, đối chiếu abstract/limitations với nguồn nộp gốc. Abstract khôi phục chi tiết đầu vào của fuzzy retrieval, kết quả PharmKG và tổng hợp ba datasets còn lại; dùng số liệu hiện hành, không phục hồi số E2E cũ. Hai câu về thực nghiệm bổ sung vẫn ngắn và theo sau kết quả hai module chính.
- Rà toàn bộ phần thêm/sửa từ contributions, Related Work, coverage/budget, repoDB preprocessing, metrics, Results 4.4–4.6 đến Discussion/Conclusion. Viết rõ quan hệ giữa câu: mục đích → thiết kế → kết quả → ý nghĩa/giới hạn; thay các cụm khó đọc như native budgets, source-covered candidate incidence và input setting. Phân biệt hai case trình bày chi tiết với bộ case thuộc ba diagnostic categories.
- Limitations mở rộng thành hai đoạn: giới hạn top-20/retriever tương thích, features và budgets còn định trước, retriever chưa được học end-to-end và phạm vi coefficient transfer; tiếp đến là semantics/alignment, path interpretation, qualitative cases và retrospective/exploratory evaluation. Không quay lại nhận định cũ rằng toàn bộ coefficients chỉ được gán tay.
- Fig. 2a/b legends chuyển lên trên axes, dưới panel titles; generator được sửa cùng figure nguồn. Caption viết lại để nối rõ hai panel với các metrics. Kiểm tra hình riêng và page8 PDF: không chồng legend/title/data/ticklabels. Tables4–5 vẫn liền nhau ở page15.
- Sửa cả ba `caculated` thành `calculated`, câu dẫn E2E reciprocal rank, và `Project administration..` thành một dấu chấm; chỉ highlight từ/dấu sửa. Ngăn heading AI declaration đứng một mình cuối trang.
- PDF chính 25 trang, bôi vàng theo thay đổi so với bản nộp gốc; nội dung khôi phục nguyên văn từ bản gốc không bôi vàng thừa. Rebuild bằng `--manuscript-only`; supplementary, response, experiments và số liệu không đổi. Verifier/reference/layout/metric-hash checks và `git diff --check` pass; kiểm tra trực quan abstract, Fig2, Results/table pair, limitations, conclusion và declarations.


## Tinh gọn limitations và supplementary — 12-11-2026

- Manuscript: gộp hai đoạn limitations thành một đoạn 95 từ, giữ giới hạn top-20, feature/budget định trước, phạm vi transfer, khác biệt semantics/alignment, path/case interpretation và retrospective evaluation. Main vẫn 25 trang.
- Supplementary S7: bỏ đúng câu “The current standardized module ... earlier model-selection diagnostics.” theo yêu cầu tác giả.
- S11.1: viết thành quy trình đã thực hiện (normalization → entity alignment → evidence graph → split/leakage control), không diễn đạt như báo cáo kiểm tra code. Giữ số liệu audit đã xác minh và phạm vi exact-ID alignment; không nhận đã thực hiện ontology mapping hoặc semantic leakage removal.
- S12: mở đầu trực tiếp bằng thiết kế calibration, không nói chung chung supplements main-text. Chỗ cần đối chiếu chỉ rõ manuscript Table 4 hoặc Section 4.2. Văn bản giảm khoảng28%, S13 giảm khoảng44% (không tính table/figure blocks); giữ công thức, protocol chính, uncertainty và kết quả bất lợi trực tiếp liên quan.
- Toàn bộ14bảng S16–S29 và3hình S4–S6, gồm caption và dữ liệu, giữ nguyên. Thêm khoảng cách0.8baselineskip trước mỗi block để tách đoạn văn với bảng/hình, bỏ clearpage trướcS13 để các sections chảy tiếp. Supplementary giảm30→28trang.
- Rebuild cảhaiPDF bằng build_revision.py. So sánh table/figure bodies với HEAD trước lượt sửa khớp tuyệt đối; kiểm tra source/deliveryPDF, hash và sốliệu bằng verifier; kiểm tra trực quan S7/S11.1/S12/S13, bảng/hình và mainlimitations. Bôi vàng vẫn theo bản nộp gốc. Không sửaresponseletter, kết quảthực nghiệm hoặc Gitremote; khôngcommit/push.
