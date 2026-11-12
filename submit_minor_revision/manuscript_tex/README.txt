Main TeX file: sn-article.tex
Requirements: Python 3 and a full TeX Live installation (pdfLaTeX).
Clean PDF:       python3 build.py
Highlighted PDF: python3 build.py --highlighted
Optional output: python3 build.py --output /path/to/output.pdf

Direct compilation: run pdflatex sn-article.tex three times.
For highlighting, define \ShowRevisionHighlights before inputting the main file.
Both modes retain the approved layout and pagination; clean mode uses white
instead of yellow revision backgrounds. Do not set \revisionhighlightfalse
if you want to preserve page references in the response letter.
All figures and tables are bundled; no experiment data or repository is required.

The approved bibliography is bundled as sn-article.bbl, alongside its .bib
and Springer .bst sources. The build script intentionally uses this .bbl;
BibTeX is not needed. If you change references, regenerate and review the
.bbl, including new-reference highlighting, before rebuilding for submission.
Disable automatic BibTeX regeneration when reproducing the approved version.
