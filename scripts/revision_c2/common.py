"""Auditable, CPU-only primitives for Reviewer 1 / Comment 2.

All paths are relative to the repository, never to the caller's working directory.
No original input, checkpoint, or manuscript is modified by this package.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/revision_c2"
FEATURES = ["rank_prior", "source_contact", "source_degree_log", "shared_neighbor_log", "negative_direct_contact"]
EDGE_FEATURES = ["rank_band", "candidate_incidence", "query_incidence", "negative_direct_contact", "degree_log"]
EDGE_DEFAULT = [1.0, .35, .05, .8, .05]
NATIVE = {
    "primekg": [0.5, .1, 0.0], "pharmkg": [.5, .1, 0.0],
    "hetionet": [.5, .1, 0.0], "drkg": [.1, .1, .8], "repodb": [0.0, .2, .95],
}
DATASETS = {
    "primekg": dict(raw="dataset/setting_a/29_n2_e2e_infer_ready/backbone_raw",
        soft="dataset/setting_a/29_n2_e2e_infer_ready/soft_support_raw",
        fuzzy="dataset/setting_a/29_n2_e2e_infer_ready/retrieval_main",
        features="dataset/setting_a/25_n2_support_features/{split}_support_features.json",
        checkpoint="results/week20/e2e_primary_checkpoint",
        embeddings="dataset/setting_a/08_backbone_ready/entity_embeddings_rgcn.pt", relations=4, repetition=1.0),
    "pharmkg": dict(raw="dataset/setting_c_pharmkg/13_e2e_infer_ready/backbone_raw",
        soft="dataset/setting_c_pharmkg/13_e2e_infer_ready/soft_support_raw",
        fuzzy="dataset/setting_c_pharmkg/13_e2e_infer_ready/fuzzy_retrieval_main",
        features="dataset/setting_c_pharmkg/08_support_features/{split}_support_features.json",
        checkpoint="results/week23/e2e_pharmkg/main_checkpoint/checkpoint-final",
        embeddings="dataset/setting_c_pharmkg/13_e2e_infer_ready/entity_embeddings_rgcn.pt", relations=28, repetition=1.05),
    "hetionet": dict(raw="dataset/setting_d_hetionet/06_fograg_ready",
        soft="dataset/setting_d_hetionet/09_e2e_soft_support_ready",
        fuzzy="dataset/setting_d_hetionet/11_e2e_fuzzy_retrieval_ready",
        features="dataset/setting_d_hetionet/07_support_features/{split}_support_features.json",
        checkpoint="results/week26/e2e_hetionet/backbone_raw/checkpoint-final",
        embeddings="dataset/setting_d_hetionet/06_fograg_ready/entity_embeddings_rgcn.pt", relations=24, repetition=1.0),
    "drkg": dict(raw="dataset/setting_e_drkg/06_fograg_ready/rgcn",
        soft="dataset/setting_e_drkg/09_e2e_soft_support_ready/rgcn_sweep_selected",
        fuzzy="dataset/setting_e_drkg/11_e2e_fuzzy_retrieval_ready/rgcn",
        features="dataset/setting_e_drkg/07_support_features/rgcn/{split}_support_features.json",
        checkpoint="results/week27/e2e_drkg_rgcn/backbone_raw/checkpoint-final",
        embeddings="dataset/setting_e_drkg/06_fograg_ready/rgcn/entity_embeddings_rgcn.pt", relations=85, repetition=1.0),
    "repodb": dict(raw="dataset/setting_f_repodb/09_e2e_soft_support_ready/rgcn_raw_display_control",
        soft="dataset/setting_f_repodb/09_e2e_soft_support_ready/rgcn_sweep_selected",
        fuzzy="dataset/setting_f_repodb/11_e2e_fuzzy_retrieval_ready/rgcn",
        features="dataset/setting_f_repodb/07_support_features/rgcn/{split}_support_features.json",
        checkpoint="results/week28/e2e_repodb_rgcn/backbone_raw/checkpoint-final",
        embeddings="dataset/setting_f_repodb/09_e2e_soft_support_ready/rgcn_raw_display_control/entity_embeddings_rgcn.pt", relations=63, repetition=1.0),
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    tmp.replace(path)


def csv_write(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def object_digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def freeze(path, obj):
    """Refuse silent changes to an existing experiment protocol."""
    path = Path(path)
    if path.exists() and read(path) != obj:
        raise ValueError(f"Protocol changed: {path}. Choose a new --out directory.")
    write(path, obj)


def environment():
    p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return {"python": platform.python_version(), "numpy": np.__version__, "git_head": p.stdout.strip()}


def row_key(row):
    return (int(row["query_entity_id"]), int(row["gold_entity_id"]))


def align(reference, rows):
    keys = [row_key(r) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate (query,gold) rows: ambiguous alignment")
    lookup = dict(zip(keys, rows))
    if set(lookup) != {row_key(r) for r in reference}:
        raise ValueError("Mismatched query/gold keys")
    return [lookup[row_key(r)] for r in reference]


def load_rows(name, split, kind="raw"):
    return read(ROOT / DATASETS[name][kind] / f"{split}.json")


def graph_features(row):
    """Shared topology features; no labels, names, native formula, or relation mapping."""
    ids = list(map(int, row["rank_entities_id"]))
    q = int(row["query_entity_id"])
    deg, adj = Counter(), defaultdict(set)
    for h, _, t in row["subgraph"]:
        deg[h] += 1
        deg[t] += 1
        adj[h].add(t)
        adj[t].add(h)
    return np.array([[(20-i)/20, float(deg[c] > 0),
        min(1., math.log1p(deg[c])/math.log(101)),
        min(1., math.log1p(len(adj[c] & adj[q]))/math.log(21)),
        -float(q in adj[c])] for i, c in enumerate(ids)], dtype=np.float64)


def extract(name, split):
    rows = load_rows(name, split)
    soft = align(rows, load_rows(name, split, "soft"))
    path = ROOT / DATASETS[name]["features"].format(split=split)
    if name == "primekg" and split == "test":
        path = ROOT / "dataset/setting_a/26_n2_soft_support/test_top20_soft_support_main.json"
    features = read(path)
    if name != "repodb":
        features = align(rows, features)
    if len(features) != len(rows):
        raise ValueError("Feature row count mismatch")
    xs, native, gold, groups, original = [], [], [], [], []
    for row, sr, fr in zip(rows, soft, features):
        ids = list(map(int, row["rank_entities_id"]))
        if len(ids) != 20 or len(set(ids)) != 20:
            raise ValueError("Expected 20 unique candidate IDs")
        if set(sr["rank_entities_id"]) != set(ids):
            raise ValueError("Soft baseline changes candidate membership")
        fs = fr if isinstance(fr, list) else fr.get("candidate_feature_rows", fr.get("candidate_debug_rows"))
        byid = {int(f.get("candidate_id", f.get("candidate_entity_id"))): f for f in fs}
        if set(byid) != set(ids):
            raise ValueError("Candidate ID alignment failed")
        values = []
        for i, cid in enumerate(ids):
            f = byid[cid]
            if int(f.get("original_rank", f.get("base_rank"))) != i+1:
                raise ValueError("Native original rank alignment failed")
            if name in ("primekg", "pharmkg"):
                e = float(f.get("support_feature_vector", {}).get("evidence_positive", f.get("evidence_edge_touch_count", 0) > 0))
                d = float(f.get("direct_T_candidate_query_flag", f.get("candidate_query_edge_count", 0) > 0))
                x = float(f.get("contra_penalty", f.get("contra_flag", 0)))
            else:
                e, d = float(f["evidence_positive"]), float(f["direct_shortcut_penalty"])
                x = float(f.get("contradiction_penalty", f.get("failed_diagnostic_penalty", 0)))
            values.append([e, d, x])
        gid = int(row["gold_entity_id"])
        gold.append(ids.index(gid) if gid in ids else -1)
        groups.append(int(row["query_entity_id"]))
        original.append([ids.index(c) for c in sr["rank_entities_id"]])
        xs.append(graph_features(row))
        native.append(values)
    a = dict(x=np.array(xs), native=np.array(native), gold=np.array(gold), groups=np.array(groups), original=np.array(original))
    return rows, a, path


def ranks(order, gold):
    result = np.full(len(gold), 21, dtype=int)
    present = gold >= 0
    result[present] = np.argmax(order[present] == gold[present, None], axis=1)+1
    return result


def order_of(scores):
    return np.argsort(-scores, axis=1, kind="stable")


def rr_of(order, gold):
    r = ranks(order, gold)
    return np.where(r <= 20, 1./r, 0.)


def metrics(order, gold):
    r = ranks(order, gold)
    return {"n": len(r), "gold_at20": float(np.mean(gold >= 0)),
        "mrr_at20": float(np.mean(np.where(r <= 20, 1./r, 0.))),
        **{f"hits{k}": float(np.mean(r <= k)) for k in [1, 3, 10]},
        "conditional_mrr_present": float(np.mean(1./r[gold >= 0])) if np.any(gold >= 0) else None}


def native_score(a, beta, gamma, mu):
    e, d, x = np.moveaxis(a["native"], -1, 0)
    s = e-beta*d-gamma*x
    if mu > 0:
        lo, hi = s.min(axis=1, keepdims=True), s.max(axis=1, keepdims=True)
        s = np.divide(s-lo, hi-lo, out=np.full_like(s, .5), where=(hi-lo) > 1e-12)
    return mu*a["x"][:, :, 0]+(1-mu)*s


def native_order(a, params, name):
    beta,gamma,mu=params
    score=native_score(a,beta,gamma,mu)
    if name == 'drkg':
        e,d,x=np.moveaxis(a['native'],-1,0)
        evidence=e-beta*d-gamma*x
        return np.lexsort((np.broadcast_to(np.arange(20),score.shape),-evidence,-score),axis=1)
    return order_of(score)


def subset(a, indices):
    return {k: v[indices] for k, v in a.items()}


def grouped_folds(groups, folds, seed):
    unique = np.unique(groups).copy()
    np.random.default_rng(seed).shuffle(unique)
    if len(unique) < 2:
        return []
    result = []
    for held in np.array_split(unique, min(folds, len(unique))):
        val = np.flatnonzero(np.isin(groups, held))
        train = np.flatnonzero(~np.isin(groups, held))
        result.append((train, val))
    return result


def fit_pairwise(a, l2=.1, steps=250, constrained=True):
    """Convex pairwise logistic objective, deterministic projected gradient descent.

    Known other positives of the same calibration query are excluded as negatives.
    Missing-gold rows cannot supply pairs, but remain in evaluation denominators.
    Dataset weights are equal when 'domain' is supplied (LODO).
    """
    x, gold, groups = a["x"], a["gold"], a["groups"]
    domains = a.get("domain", np.zeros(len(gold), dtype=int))
    known = defaultdict(set)
    # Candidate IDs are necessary to identify positives across different lists.
    ids = a.get("ids")
    for i, g in enumerate(gold):
        if g >= 0 and ids is not None:
            known[(int(domains[i]), int(groups[i]))].add(int(ids[i, g]))
    pairs, weights = [], []
    domain_counts = Counter(domains[gold >= 0].tolist())
    for i, g in enumerate(gold):
        if g < 0:
            continue
        neg = [j for j in range(20) if j != g and (ids is None or int(ids[i,j]) not in known[(int(domains[i]),int(groups[i]))])]
        if not neg:
            continue
        pairs.extend(x[i,g]-x[i,neg])
        weights.extend([1./(domain_counts[int(domains[i])]*len(neg))]*len(neg))
    w = np.zeros(x.shape[-1])
    if not pairs:
        w[0] = 1.
        return w
    diff = np.asarray(pairs)
    pw = np.asarray(weights)
    pw /= pw.sum()
    # Hessian bound <= .25*weighted ||difference||^2 + l2.
    lr = 1./max(.25*np.sum(pw*np.sum(diff*diff, axis=1))+l2, 1e-6)
    for _ in range(steps):
        z = np.clip(diff@w, -60, 60)
        grad = -(diff.T@(pw/(1.+np.exp(z))))+l2*w
        w -= lr*grad
        if constrained:
            w = np.maximum(w, 0.)
    return w


def choose_l2(a, grid, folds, seed, steps, constrained=True):
    splits = grouped_folds(a["groups"], folds, seed)
    if not splits:
        return max(grid), []
    records = []
    for l2 in grid:
        vals = []
        for train, val in splits:
            w = fit_pairwise(subset(a, train), l2, steps, constrained)
            vals.extend(rr_of(order_of(a["x"][val]@w), a["gold"][val]))
        records.append({"l2": l2, "group_cv_mrr": float(np.mean(vals))})
    best = max(records, key=lambda r: (r["group_cv_mrr"], r["l2"]))
    return best["l2"], records


def cluster_bootstrap(delta, groups, repetitions=2000, seed=20261105):
    """Paired query-cluster resampling; queries with multiple golds stay together."""
    unique = np.unique(groups)
    sums = np.array([delta[groups == g].sum() for g in unique])
    counts = np.array([np.sum(groups == g) for g in unique])
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(repetitions):
        idx = rng.integers(0, len(unique), len(unique))
        samples.append(sums[idx].sum()/counts[idx].sum())
    lo, hi = np.quantile(samples, [.025, .975])
    return {"delta_mrr": float(np.mean(delta)), "ci95_low": float(lo), "ci95_high": float(hi), "clusters": len(unique)}


def edge_matrix(row):
    triples = list(dict.fromkeys(tuple(map(int,e)) for e in row["subgraph"]))
    ids, q = list(map(int,row["rank_entities_id"])), int(row["query_entity_id"])
    bands = {c: 1. if i<5 else .6 if i<10 else .25 for i,c in enumerate(ids)}
    deg = Counter(n for h,_,t in triples for n in (h,t))
    matrix = []
    for h,_,t in triples:
        band = max(bands.get(h,0),bands.get(t,0))
        direct = (h == q and t in bands) or (t == q and h in bands)
        matrix.append([band,float(h in bands or t in bands),float(h == q or t == q),-float(direct),
            min(1., (math.log1p(deg[h])+math.log1p(deg[t]))/10.)])
    return triples, np.array(matrix).reshape(-1,5)


def select_graph(row, weights=EDGE_DEFAULT, ratio=.55, budget=None):
    triples, matrix = edge_matrix(row)
    if not triples:
        return []
    budget = min(len(triples),max(1, int(round(len(triples)*ratio)))) if budget is None else min(len(triples),int(budget))
    if budget <= 0:
        return []
    score = matrix@np.asarray(weights)
    ordered = sorted(range(len(triples)),key=lambda i:(-score[i], i))
    chosen = set()
    # A strict budget; coverage is measured, never assumed to be guaranteed.
    for c in row["rank_entities_id"]+[row["query_entity_id"]]:
        if len(chosen)>=budget:
            break
        if any(c in (triples[j][0],triples[j][2]) for j in chosen):
            continue
        for j in ordered:
            if c in (triples[j][0],triples[j][2]):
                chosen.add(j)
                break
    for j in ordered:
        if len(chosen)>=budget:
            break
        chosen.add(j)
    return [list(triples[j]) for j in sorted(chosen)]


def graph_stats(row, selected, reference=None):
    source = {tuple(e) for e in row["subgraph"]}
    edges = {tuple(e) for e in selected}
    if not edges <= source:
        raise ValueError("Selected edge is absent from source graph")
    def nodes(es):
        return {n for h,_,t in es for n in (h,t)}
    def adj(es):
        a=defaultdict(set)
        for h,_,t in es:
            a[h].add(t); a[t].add(h)
        return a
    candidates=set(row["rank_entities_id"])
    q=row["query_entity_id"]
    src_nodes, sel_nodes=nodes(source), nodes(edges)
    before, after=adj(source),adj(edges)
    connected = {c for c in candidates if q in before[c] or before[c]&before[q]}
    retained = {c for c in connected if q in after[c] or after[c]&after[q]}
    original_rel={e[1] for e in source}
    result={"source_edges":len(source),"selected_edges":len(edges),
        "candidate_coverage_absolute":len(candidates&sel_nodes)/20.,
        "candidate_coverage_retained":len(candidates&sel_nodes)/max(1,len(candidates&src_nodes)),
        "query_present":float(q in sel_nodes),
        "twohop_connected_before":len(connected),"twohop_connected_after":len(retained),
        "twohop_retention":len(retained)/len(connected) if connected else None,
        "relation_type_retention":len({e[1] for e in edges})/max(1,len(original_rel))}
    if reference is not None:
        ref={tuple(e) for e in reference}
        result["jaccard_vs_default"] = len(ref&edges)/max(1,len(ref|edges))
    return result


def mean_stats(items):
    return {k: float(np.mean([r[k] for r in items if r[k] is not None]))
        if any(r[k] is not None for r in items) else None for k in items[0]}


def reorder_row(row, order):
    # Export a minimal, synchronized inference schema, avoiding stale native scores.
    ids=[row["rank_entities_id"][int(i)] for i in order]
    names=[row["rank_entities"][int(i)] for i in order]
    qname=row.get("query_display",row["query_entity"])
    text=row["input"]
    question=text.rsplit("Question:",1)[1].split("\nAnswer:",1)[0].strip()
    options="("+", ".join(repr(n) for n in names)+")"
    refs=", ".join([f"'{qname}': [QUERY]"]+[f"'{n}': [ENTITY]" for n in names])
    prompt=("You are a biomedical scientist. The task is to predict the answer based on the given question, "
        f"and you only need to answer one entity. The answer must be in {options}.\n"
        f"You can refer to the entity embeddings: {refs}.\n\nQuestion: {question}\nAnswer: ")
    out={k:row[k] for k in ["query_entity_id","gold_entity_id","query_entity","output"]}
    out.update(input=prompt,rank_entities=names,rank_entities_id=ids,subgraph=row["subgraph"],
        rank=ids.index(row["gold_entity_id"])+1 if row["gold_entity_id"] in ids else 21)
    if "rank_entities_canonical" in row:
        out["rank_entities_canonical"]=[row["rank_entities_canonical"][int(i)] for i in order]
    return out
