#!/usr/bin/env python3
"""Fill the supplied response template without changing either source DOCX.

Uses the standard library only. Reviewer wording, submission metadata and the
template's Word styles are retained. Numerical corrections are read from the
submitted-source snapshot and current result CSV, rather than entered by hand.
"""
import copy
import csv
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "minor_revision"
TEMPLATE = BASE / "Response to Reviewers.docx"
CONTENT = BASE / "revision_notes/response_content.json"
OUTPUT = BASE / "Response to Reviewers_revised.docx"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def tag(name):
    return f"{{{W}}}{name}"


def child(parent, name, **attrs):
    return ET.SubElement(parent, tag(name), {tag(k): str(v) for k, v in attrs.items()})


def plain(node):
    return "".join(n.text or "" for n in node.iter(tag("t")))


def paragraph(text, bold=False, size=26, keep=False):
    p = ET.Element(tag("p"))
    props = child(p, "pPr")
    child(props, "spacing", before=0, after=100, line=300, lineRule="auto")
    child(props, "jc", val="both")
    child(props, "widowControl")
    if keep:
        child(props, "keepNext")
    run = child(p, "r")
    rprops = child(run, "rPr")
    child(rprops, "rFonts", ascii="Times New Roman", hAnsi="Times New Roman", cs="Times New Roman")
    if bold:
        child(rprops, "b")
    child(rprops, "sz", val=size)
    child(rprops, "szCs", val=size)
    child(run, "t").text = text
    return p


def correction_table(rows):
    table = ET.Element(tag("tbl"))
    props = child(table, "tblPr")
    child(props, "tblW", w=9360, type="dxa")
    borders = child(props, "tblBorders")
    for edge in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        child(borders, edge, val="single", sz=4, color="B7B7B7")
    child(props, "tblLayout", type="fixed")
    margins = child(props, "tblCellMar")
    for side in ["top", "left", "bottom", "right"]:
        child(margins, side, w=90, type="dxa")
    widths = [1200, 2720, 2720, 2720]
    grid = child(table, "tblGrid")
    for width in widths:
        child(grid, "gridCol", w=width)
    for i, values in enumerate(rows):
        row = child(table, "tr")
        props = child(row, "trPr")
        child(props, "cantSplit")
        if i == 0:
            child(props, "tblHeader")
        for width, value in zip(widths, values):
            cell = child(row, "tc")
            props = child(cell, "tcPr")
            child(props, "tcW", w=width, type="dxa")
            if i == 0:
                child(props, "shd", fill="E8EEF5", val="clear")
            p = paragraph(value, bold=i == 0, size=21, keep=i < len(rows) - 1)
            p.find("w:pPr/w:jc", NS).set(tag("val"), "left")
            p.find("w:pPr/w:spacing", NS).set(tag("line"), "240")
            cell.append(p)
    return table


with ZipFile(TEMPLATE) as archive:
    original_xml = archive.read("word/document.xml")
    for _, (prefix, uri) in ET.iterparse(io.BytesIO(original_xml), events=["start-ns"]):
        ET.register_namespace(prefix, uri)
    root = ET.fromstring(original_xml)
    old_body = root.find("w:body", NS)
    original_paras = old_body.findall("w:p", NS)
    content = json.loads(CONTENT.read_text())
    body = ET.Element(tag("body"))
    # Preserve the heading, submission metadata and introductory paragraph.
    for p in original_paras[:8]:
        body.append(copy.deepcopy(p))
    for i, line in enumerate(content["summary"], 1):
        body.append(paragraph(f"{i}. {line}"))
    body.append(paragraph("Changes in the revised manuscript and Supplementary Material are highlighted in yellow. Our point-by-point responses and the locations of the revisions are provided below."))
    for p in original_paras[10:13]:
        body.append(copy.deepcopy(p))

    starts = [i for i, p in enumerate(original_paras) if re.match(r"Comment [1-6]\.", plain(p))]
    assert len(starts) == 6
    submitted = subprocess.check_output([
        "git", "show", "ae70903:minor_revision/Main Manuscript/paper/sn-article.tex"
    ], cwd=ROOT, text=True)
    old_metrics = [re.findall(r"(?<!\d)\d\.\d{4}(?!\d)", line)
                   for line in submitted.splitlines() if line.startswith("& E2E MRR@20")]
    assert len(old_metrics) == 3 and all(len(row) == 5 for row in old_metrics)
    metrics_path = ROOT / "results/revision_c2/e2e_stable/e2e_metrics.csv"
    metrics = list(csv.DictReader(metrics_path.open(encoding="utf-8-sig")))
    datasets = [("primekg", "PrimeKG"), ("pharmkg", "PharmKG"), ("hetionet", "Hetionet"), ("drkg", "DRKG"), ("repodb", "repoDB")]
    variants = ["raw", "original_soft", "original_fuzzy"]
    table = [["Dataset", "Source", "Soft support", "Fuzzy retrieval"]]
    for d, (dataset, label) in enumerate(datasets):
        values = []
        for v, variant in enumerate(variants):
            matches = [r for r in metrics if r["dataset"] == dataset and r["variant"] == variant and r["split"] == "test"]
            assert len(matches) == 1
            values.append(f"{old_metrics[v][d]} → {float(matches[0]['adjusted_rr']):.4f}")
        table.append([label, *values])

    comments = []
    for idx, start in enumerate(starts, 1):
        end = starts[idx] if idx < 6 else len(original_paras)
        comment_nodes = []
        for p in original_paras[start:end]:
            if plain(p).startswith("Author response:"):
                break
            if plain(p).strip():
                comment_nodes.append(p)
        comments.append([plain(p) for p in comment_nodes])
        for p in comment_nodes:
            p = copy.deepcopy(p)
            props = p.find("w:pPr", NS)
            if props is None:
                props = ET.Element(tag("pPr")); p.insert(0, props)
            child(props, "keepNext")
            for run in p.findall("w:r", NS):
                for mark in run.findall("w:lastRenderedPageBreak", NS):
                    run.remove(mark)
            body.append(p)
        body.append(paragraph("Author response:", bold=True, keep=True))
        for n, text in enumerate(content["responses"][str(idx)]):
            body.append(paragraph(text))
            if idx == 4 and n == 3:
                body.append(paragraph("Table R1. Adjusted E2E MRR@20 in Table 3 (previous → revised).", bold=True, size=22, keep=True))
                body.append(correction_table(table))
        body.append(paragraph("", size=10))
    body.append(copy.deepcopy(old_body.find("w:sectPr", NS)))

    serialized_body = ET.tostring(body, encoding="unicode")
    # The original document root already declares these namespaces. Keeping it
    # also preserves compatibility attributes and Word-specific declarations.
    serialized_body = re.sub(r' xmlns(?::[A-Za-z0-9_]+)?="[^"]*"', "", serialized_body)
    new_xml = re.sub(r"<w:body>[\s\S]*</w:body>", lambda _: serialized_body, original_xml.decode("utf-8"))
    assert new_xml != original_xml.decode("utf-8")
    ET.fromstring(new_xml)
    with ZipFile(OUTPUT, "w") as target:
        for item in archive.infolist():
            data = new_xml.encode("utf-8") if item.filename == "word/document.xml" else archive.read(item.filename)
            target.writestr(item, data)

# A readable companion is useful for reviewing wording without altering Word.
text_lines = []
for node in body:
    if node.tag == tag("p"):
        text_lines.append(plain(node))
    elif node.tag == tag("tbl"):
        text_lines.extend(" | ".join(plain(c) for c in row.findall("w:tc", NS)) for row in node.findall("w:tr", NS))
review_text = "\n\n".join(text_lines).strip() + "\n"
(BASE / "revision_notes/response_letter_text.txt").write_text(review_text)

with ZipFile(OUTPUT) as archive:
    assert archive.testzip() is None
    for name in archive.namelist():
        if name.endswith((".xml", ".rels")):
            ET.fromstring(archive.read(name))
    parsed = ET.fromstring(archive.read("word/document.xml"))
    output_texts = [plain(p) for p in parsed.findall("w:body/w:p", NS)]
assert output_texts.count("Author response:") == 6
for group in comments:
    for text in group:
        assert text in output_texts, "Reviewer wording changed"
assert all(content["responses"][str(i)][0].startswith("We thank") for i in range(1, 7))
assert "has been uploaded" not in review_text
report = {
    "template_sha256": hashlib.sha256(TEMPLATE.read_bytes()).hexdigest(),
    "content_sha256": hashlib.sha256(CONTENT.read_bytes()).hexdigest(),
    "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
    "output_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    "original_table_source": "ae70903:minor_revision/Main Manuscript/paper/sn-article.tex",
    "comment_count": 6,
    "all_reviewer_comments_preserved": True,
    "word_count": len(review_text.split()),
    "correction_table": table,
    "checks": "DOCX archive and all XML parts parse; six populated responses; original reviewer wording retained; correction table derived from source artifacts",
}
(BASE / "revision_notes/response_letter_manifest.json").write_text(json.dumps(report, indent=2) + "\n")
print(f"Created {OUTPUT}: {report['word_count']} words, six responses, verified numerical correction table.")
