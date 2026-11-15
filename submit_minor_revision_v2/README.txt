SoftFuse-KGC — Minor revision submission v2

CONTENTS
manuscript_tex/                         Manuscript LaTeX source and dependencies
supplementary_tex/                      Supplementary LaTeX source and dependencies
Manuscript_highlighted.pdf              Manuscript with yellow revision highlighting
Manuscript_clean.pdf                    Manuscript without yellow highlighting
Supplementary_material_highlighted.pdf  Supplementary with yellow revision highlighting
Supplementary_material_clean.pdf        Supplementary without yellow highlighting
Response_to_Reviewers.docx              Response letter
SHA256SUMS.txt                          Checksums of the other package files

BUILD (Python 3 and a full TeX Live installation with pdfLaTeX)
Run from this folder:
  python3 manuscript_tex/build.py --output Manuscript_clean.pdf
  python3 manuscript_tex/build.py --highlighted --output Manuscript_highlighted.pdf
  python3 supplementary_tex/build.py --output Supplementary_material_clean.pdf
  python3 supplementary_tex/build.py --highlighted --output Supplementary_material_highlighted.pdf

Main files: manuscript_tex/sn-article.tex and supplementary_tex/ESM_1.tex.
For direct compilation, run pdfLaTeX three times on the relevant main file.
Direct compilation defaults to clean; define \ShowRevisionHighlights before
inputting the main file to show yellow highlighting.

Clean mode uses white instead of yellow revision backgrounds, preserving text,
layout, and pagination. Do not disable the revision environments.

The manuscript's finalized sn-article.bbl is bundled alongside the .bib and
Springer .bst/.cls. The build script uses this .bbl without rerunning BibTeX.
If references are edited, regenerate and review the .bbl, including revision
markup, before submission. All figures/tables are included; no experiment
runs, data exports, original repository, or external file paths are required.
