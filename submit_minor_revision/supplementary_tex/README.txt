Main TeX file: ESM_1.tex
Requirements: Python 3 and a full TeX Live installation (pdfLaTeX).
Clean PDF:       python3 build.py
Highlighted PDF: python3 build.py --highlighted
Optional output: python3 build.py --output /path/to/output.pdf

Direct compilation: run pdflatex ESM_1.tex three times.
For highlighting, define \ShowRevisionHighlights before inputting the main file.
Both modes retain the approved layout and pagination; clean mode uses white
instead of yellow revision backgrounds. Do not set \revisionhighlightfalse
if you want to preserve page references in the response letter.
All figures and tables are bundled; no experiment data or repository is required.
