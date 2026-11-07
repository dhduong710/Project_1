#!/usr/bin/env python3
"""Fill the supplied response template without changing either source DOCX.

Uses the standard library only. Reviewer wording, submission metadata and the
template's Word styles are retained. Numerical corrections are checked against
the submitted-source snapshot and current result CSV and recorded in the audit
manifest; the letter itself uses a concise example rather than a table.
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


def paragraph(text, bold=False, size=26):
    p = ET.Element(tag("p"))
    props = child(p, "pPr")
    child(props, "spacing", before=0, after=0, line=240, lineRule="auto")
    # Ragged-right prose avoids stretched spaces around numerical expressions.
    child(props, "jc", val="left")
    child(props, "widowControl")
    run = child(p, "r")
    rprops = child(run, "rPr")
    child(rprops, "rFonts", ascii="Times New Roman", hAnsi="Times New Roman", cs="Times New Roman")
    if bold:
        child(rprops, "b")
    child(rprops, "sz", val=size)
    child(rprops, "szCs", val=size)
    child(run, "t").text = text
    return p


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
            for run in p.findall("w:r", NS):
                for mark in run.findall("w:lastRenderedPageBreak", NS):
                    run.remove(mark)
            body.append(p)
        body.append(paragraph("Author response:", bold=True))
        for text in content["responses"][str(idx)]:
            body.append(paragraph(text))
    body.append(copy.deepcopy(old_body.find("w:sectPr", NS)))

    # Apply single spacing to copied template paragraphs as well as responses.
    # Paragraph breaks supply the separation; no empty spacer paragraphs.
    for p in list(body.findall("w:p", NS)):
        if not plain(p).strip():
            body.remove(p)
            continue
        props = p.find("w:pPr", NS)
        if props is None:
            props = ET.Element(tag("pPr")); p.insert(0, props)
        spacing = props.find("w:spacing", NS)
        if spacing is None:
            spacing = child(props, "spacing")
        spacing.attrib.clear()
        for key, value in {"before": "0", "after": "0", "line": "240", "lineRule": "auto"}.items():
            spacing.set(tag(key), value)
        # Do not chain a reviewer comment, response label and opening paragraph
        # into a single page-placement unit. Explicit false values also override
        # inherited styles when the file is opened in Word or WPS.
        pagination = {"keepNext": "0", "keepLines": "0", "pageBreakBefore": "0", "widowControl": "1", "snapToGrid": "0"}
        for name, value in pagination.items():
            for existing in props.findall("w:" + name, NS):
                props.remove(existing)
            child(props, name, val=value)
        # Keep paragraph properties in their OOXML schema order.
        order = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc", "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange"]
        props[:] = sorted(props, key=lambda x: order.index(x.tag.split("}")[-1]) if x.tag.split("}")[-1] in order else len(order))
        for run in p.findall(".//w:r", NS):
            for mark in list(run):
                if mark.tag == tag("lastRenderedPageBreak") or (mark.tag == tag("br") and mark.get(tag("type")) in {"page", "column"}):
                    run.remove(mark)

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
review_text = "\n".join(text_lines).strip() + "\n"
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
assert not parsed.findall(".//w:tbl", NS)
for p in parsed.findall("w:body/w:p", NS):
    assert plain(p).strip(), "Unexpected empty spacer paragraph"
    spacing = p.find("w:pPr/w:spacing", NS)
    assert all(spacing.get(tag(k)) == v for k, v in {"before": "0", "after": "0", "line": "240", "lineRule": "auto"}.items())
    for flag in ["keepNext", "keepLines", "pageBreakBefore", "snapToGrid"]:
        assert p.find("w:pPr/w:" + flag, NS).get(tag("val")) == "0"
assert not parsed.findall(".//w:lastRenderedPageBreak", NS)
assert not any(br.get(tag("type")) in {"page", "column"} for br in parsed.findall(".//w:br", NS))
assert all(term not in review_text for term in ["Revisions:", "published", "Table R1", "0.7737/0.9010"])
assert table[1][1] == "0.0476 → 0.0477", "Check the numerical correction example"
report = {
    "template_sha256": hashlib.sha256(TEMPLATE.read_bytes()).hexdigest(),
    "content_sha256": hashlib.sha256(CONTENT.read_bytes()).hexdigest(),
    "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
    "output_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    "original_table_source": "ae70903:minor_revision/Main Manuscript/paper/sn-article.tex",
    "comment_count": 6,
    "all_reviewer_comments_preserved": True,
    "word_count": len(review_text.split()),
    "correction_values_for_audit_only": table,
    "letter_contains_tables": False,
    "response_alignment": "left",
    "paragraph_spacing": "single line; zero before/after; no empty spacer paragraphs",
    "pagination": "keepNext/keepLines/pageBreakBefore/snapToGrid explicitly disabled; no manual or cached page breaks; widow control retained",
    "checks": "DOCX archive and all XML parts parse; six populated responses; original reviewer wording retained; correction example verified; no tables or Revisions labels",
}
(BASE / "revision_notes/response_letter_manifest.json").write_text(json.dumps(report, indent=2) + "\n")
(BASE / "Response to Reviewers_layout_fixed.docx").write_bytes(OUTPUT.read_bytes())
print(f"Created {OUTPUT}: {report['word_count']} words, six responses, verified numerical correction example; no tables.")
