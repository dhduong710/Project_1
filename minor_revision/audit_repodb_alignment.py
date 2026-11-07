#!/usr/bin/env python3
"""Read-only reproduction of the repoDB preprocessing claims in Supplement S11.1.

Writes only the revision audit JSON; never invokes a preparation script's main().
Run from the repository root with an environment containing pandas.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
assert Path.cwd() == ROOT, "Run from the SoftFuse-KGC repository root"
DATA = Path("dataset/setting_f_repodb")
inputs = []


def track(path):
    path = Path(path)
    inputs.append(path)
    return path


def read(path):
    return json.loads(track(path).read_text())


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, track(path))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


n = module("normalize_repodb", "scripts/week28/02_normalize_freeze_repodb_task.py")
g = module("graph_repodb", "scripts/week28/03_build_repodb_splits_graph.py")
# Source files inspected for canonical/numeric IDs and display-name separation.
track("scripts/week28/05_build_repodb_fograg_ready.py")
track("scripts/week28/06c_make_repodb_rgcn_raw_display_control.py")
raw = n.load_raw_table(track(DATA / "00_raw_inventory/repodb_best_table_raw.tsv"))
normalized = n.normalize_rows(raw)
approved = n.dedupe_pairs(normalized, "approved", n.TARGET_RELATION)
failed_before = n.dedupe_pairs(normalized, "failed_like", n.FAILED_RELATION)
conflicts, failed = n.find_conflicts(approved, failed_before)
assert approved == read(DATA / "01_task_spec/approved_pairs_unique.json")
assert failed == read(DATA / "01_task_spec/failed_pairs_unique.json")
track("dataset/setting_e_drkg/03_graph/entity2id.json")
mapping = n.mapping_probe(approved, failed)
assert mapping == read(DATA / "01_task_spec/mapping_probe_drkg.json")
target_edges = [(r["compound_entity"], n.TARGET_RELATION, r["disease_entity"]) for r in approved]
failed_edges = [(r["compound_entity"], n.FAILED_RELATION, r["disease_entity"]) for r in failed]
train, valid, test, split_info = g.make_coverage_safe_split(target_edges, 500, 500, 2028)
for name, edges in [("train", train), ("valid", valid), ("test", test)]:
    assert edges == g.read_edges_tsv(track(DATA / f"02_splits/{name}.tsv"))
coverage = g.check_coverage(train, valid, test)
assert coverage["coverage_pass"]
summary = read(DATA / "03_graph/graph_summary.json")
caps = summary["graph_build_stats"]["caps"]
track("dataset/setting_e_drkg/03_graph/train_enriched.tsv")
edges, edge_set, entities, relations, stats = g.build_graph(train, valid, test, failed_edges, SimpleNamespace(**caps))
stored_edges = g.read_edges_tsv(track(DATA / "03_graph/train_enriched.tsv"))
assert edge_set == set(stored_edges) and len(edges) == len(stored_edges)
assert stats == summary["graph_build_stats"]
assert not (set(valid) | set(test)) & edge_set
assert not set(train) & (set(valid) | set(test)) and not set(valid) & set(test)
assert entities == set(read(DATA / "03_graph/entity2id.json"))
assert relations == set(read(DATA / "03_graph/relation2id.json"))
candidates = read(DATA / "02_splits/candidate_universe_compound.json")["candidate_entities"]
assert set(candidates) == {h for h, _, _ in train}
report = {
    "audit": "Recomputed normalization, identifier probes, split, and capped graph using repository functions; exact artifact agreement",
    "raw_rows": len(raw),
    "valid_identifier_rows": sum(r["valid_drugbank_and_cui"] for r in normalized),
    "approved_pairs": len(approved),
    "failed_pairs_before_conflicts": len(failed_before),
    "conflicting_pairs": len(conflicts),
    "failed_pairs_after_conflicts": len(failed),
    "mapping": {k: v for k, v in mapping.items() if not k.startswith("sample_") and k != "disease_form_hits_sample"},
    "split": split_info,
    "seed": 2028,
    "coverage": coverage,
    "candidate_compounds": len(candidates),
    "graph": stats,
    "heldout_exact_target_edges_in_graph": 0,
    "all_task_entities_retained": True,
    "inputs_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(inputs))},
}
out = ROOT / "minor_revision/revision_notes/comment5_alignment_audit.json"
out.write_text(json.dumps(report, indent=2) + "\n")
print(f"PASS: normalization, mapping, split and all {len(edges):,} graph edges reproduced. Audit: {out}")
