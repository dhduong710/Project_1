"""Matched-budget selection comparisons and information-retention audits."""
import argparse
import gzip
import json
import time
from pathlib import Path
import numpy as np
from c3lib import *


def run(args):
    out=Path(args.out).resolve();start=time.monotonic()
    plan=variants(args.random_seeds,args.ratios)
    protocol=dict(version=1,datasets=args.datasets,splits=args.splits,random_seeds=args.random_seeds,
        ratios=args.ratios,bootstrap=args.bootstrap,max_rows=args.max_rows,variants=plan,
        gpu_variant_keys=[v['key'] for v in gpu_variants(plan)],
        main_budget='per-query number of UNIQUE edges in original fuzzy artifact',
        curve_budget='round(ratio * unique source edges); no minimum; <=10 edges invokes existing encoder fallback',
        topology='unique directed relation-labeled triples; path walks undirected, original edge direction/sign recorded',
        missing='conditional retention undefined if source denominator zero; omit and report eligible counts',
        selection='no gold labels; no selection of winning methods/ratios by validation or test results',
        checkpoint='same frozen raw/main checkpoint per dataset as revision_c2',
        primary_metrics=PRIMARY_METRICS,
        code_sha256={p.name:digest(p) for p in [HERE/'c3lib.py',HERE/'run_cpu.py',HERE.parent/'revision_c2/common.py',HERE.parent/'revision_c2/run_e2e.py']})
    freeze(out/'protocol_cpu.json',protocol)
    hashes={str(p.relative_to(ROOT)):digest(p) for n in args.datasets for s in args.splits for p in input_paths(n,s)}
    freeze(out/'input_hashes.json',hashes)
    summaries=[];contrasts=[];audits=[];timing=[]
    for name in args.datasets:
        for split in args.splits:
            rows,contexts=load_dataset(name,split)
            if args.max_rows:rows=rows[:args.max_rows];contexts=contexts[:args.max_rows]
            grouped={v['key']:[] for v in plan};times={v['key']:[] for v in plan}
            for i,(r,ctx) in enumerate(zip(rows,contexts)):
                for v in plan:
                    then=time.perf_counter();edges=ctx.select(v);ms=(time.perf_counter()-then)*1000
                    metrics=ctx.metrics(edges,r['gold_entity_id'])
                    grouped[v['key']].append(dict(row=i,query_id=r['query_entity_id'],gold_id=r['gold_entity_id'],**metrics))
                    times[v['key']].append(ms)
                if (i+1)%100==0:print(f'{name}/{split}: {i+1}/{len(rows)} source rows; {len(plan)} variants',flush=True)
            for v in plan:
                rs=grouped[v['key']]
                meta=dict(dataset=name,split=split,variant=v['key'],method=v['method'],budget=v['budget'],seed=v['seed'])
                summaries.append(dict(**meta,**aggregate(rs)))
                timing.append(dict(**meta,n=len(rs),selection_ms_mean=float(np.mean(times[v['key']])),
                    selection_ms_p50=float(np.median(times[v['key']])),selection_ms_p95=float(np.quantile(times[v['key']],.95)),
                    note='includes first-time per-source ordering cache; excludes metrics and I/O; descriptive CPU timing'))
                path=out/'per_query'/name/split/(v['key']+'.jsonl.gz');path.parent.mkdir(parents=True,exist_ok=True)
                with gzip.open(path,'wt',encoding='utf-8') as f:
                    for r in rs:f.write(json.dumps(r,allow_nan=False)+'\n')
                if split=='test' and v['budget']=='native' and v['method'] not in ['source_raw','source_unique','empty_graph','original_fuzzy']:
                    for c in paired(rs,grouped['original_fuzzy'],PRIMARY_METRICS,args.bootstrap):
                        contrasts.append(dict(**meta,reference='original_fuzzy',**c))
            audits.append(dict(dataset=name,split=split,rows=len(rows),unique_queries=len({r['query_entity_id'] for r in rows}),
                source_occurrences_mean=float(np.mean([len(c.raw) for c in contexts])),
                source_unique_mean=float(np.mean([len(c.edges) for c in contexts])),
                fuzzy_unique_mean=float(np.mean([c.budget for c in contexts])),
                sources_with_duplicates=sum(len(c.raw)!=len(c.edges) for c in contexts),
                score_source_exact_alignment=True,native_subset_verified=True,candidate_order_fixed=True,
                source_gene_path_eligible=sum(bool(c.gene_paths) for c in contexts)))
            csv_write(out/'retention_metrics.csv',summaries);csv_write(out/'retention_contrasts.csv',contrasts)
            csv_write(out/'selection_timing.csv',timing);write(out/'input_audit.json',audits)
            print(f'Completed {name}/{split}',flush=True)
    write(out/'cpu_complete.json',dict(status='smoke_only' if args.max_rows else 'complete',datasets=args.datasets,splits=args.splits,
        metric_rows=len(summaries),variants_per_dataset_split=len(plan),seconds=round(time.monotonic()-start,2)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',default=str(OUT));p.add_argument('--datasets',nargs='+',choices=list(DATASETS),default=list(DATASETS))
    p.add_argument('--splits',nargs='+',choices=['valid','test'],default=['valid','test'])
    p.add_argument('--random-seeds',type=int,default=5);p.add_argument('--ratios',type=float,nargs='+',default=[.2,.35,.55,.75,.9])
    p.add_argument('--bootstrap',type=int,default=2000);p.add_argument('--max-rows',type=int,default=0)
    args=p.parse_args()
    if args.random_seeds<1 or any(r<=0 or r>1 for r in args.ratios) or args.bootstrap<1 or args.max_rows<0:p.error('Invalid counts/ratios')
    run(args)
