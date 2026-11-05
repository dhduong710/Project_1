"""Replay native implementations and audit their actual behavior across budgets.

This extension preserves native reservation passes (including any budget excess),
unlike the strict native-score coverage control in the main comparison.
"""
import argparse
import ast
import importlib.util
import gzip
import json
from types import SimpleNamespace
from c3lib import *

SCRIPTS={
 'primekg':'scripts/week16/02_build_retrieval_variants.py',
 'pharmkg':'scripts/week23/04_build_fuzzy_retrieval_transfer.py',
 'hetionet':'scripts/week26/06_build_hetionet_fuzzy_retrieval.py',
 'drkg':'scripts/week27/07_build_drkg_fuzzy_retrieval_rgcn.py',
 'repodb':'scripts/week28/07_build_repodb_fuzzy_retrieval_rgcn.py',
}


def native_loader(name):
    path=ROOT/SCRIPTS[name]
    spec=importlib.util.spec_from_file_location('native_'+name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    defaults={}
    # Read literal CLI defaults without calling main() (which writes artifacts).
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='add_argument':
            kw={k.arg:k.value for k in node.keywords}
            if 'default' in kw:defaults[ast.literal_eval(node.args[0]).lstrip('-').replace('-','_')]=ast.literal_eval(kw['default'])
    return module,defaults


def run(args):
    root=Path(args.results).resolve();out=root/'native_budget_audit';cp=read(root/'protocol_cpu.json')
    for path,sha in read(root/'input_hashes.json').items():assert digest(ROOT/path)==sha
    protocol=dict(cpu_protocol_sha256=digest(root/'protocol_cpu.json'),ratios=cp['ratios'],
        script_sha256={n:digest(ROOT/SCRIPTS[n]) for n in cp['datasets']},runner_sha256=digest(Path(__file__)),
        policy='native selector unchanged; override target keep only; record actual budget violations; no test selection')
    freeze(out/'protocol.json',protocol);summaries=[];audits=[]
    for name in cp['datasets']:
        module,defaults=native_loader(name)
        relations={int(k):v for k,v in read(ROOT/MAP_DIRS[name]/'id2relation.json').items()}
        reverse={v:k for k,v in relations.items()}
        for split in cp['splits']:
            rows,contexts=load_dataset(name,split)
            feats=align(rows,read(ROOT/FEATURE_PATHS[name].format(split=split)))
            grouped={str(b):[] for b in ['native']+cp['ratios']};same=[]
            for i,(row,ctx,feat) in enumerate(zip(rows,contexts,feats)):
                for b in ['native']+cp['ratios']:
                    budget=ctx.budget if b=='native' else int(round(len(ctx.edges)*b))
                    if name=='primekg':
                        cfg=read(ROOT/'configs/week16/retrieval_tight.json');cfg.update(retain_ratio=0.,min_keep=budget)
                        selected=module.build_variant([feat],cfg)[0][0]['selected_subgraph']
                    elif name=='pharmkg':
                        module.CONFIG.update(retain_ratio=0.,min_keep=budget)
                        chosen=module.select_triples(feat['triple_feature_rows'],ctx.candidates,len(ctx.raw))[0]
                        selected=[tr['triple'] for tr in chosen]
                    else:
                        options=SimpleNamespace(**dict(defaults,retain_ratio=0.,min_keep=budget,max_keep=budget))
                        selected=module.select_subgraph(row,reverse,relations,options)[0] if name=='hetionet' else module.select_subgraph(row,relations,options)[0]
                    es=[tuple(e) for e in selected]
                    if b=='native':
                        match=set(es)==set(ctx.fuzzy) and len(es)==len(ctx.fuzzy);same.append(match)
                        assert match,f'Native replay failed: {name}/{split}/{i}'
                    result=dict(row=i,query_id=ctx.q,gold_id=row['gold_entity_id'],requested_budget=budget,
                        budget_excess=max(0,len(es)-budget),budget_violation=int(len(es)>budget),
                        **ctx.metrics(es,row['gold_entity_id']))
                    grouped[str(b)].append(result)
            for b,rs in grouped.items():
                summaries.append(dict(dataset=name,split=split,budget=b,**aggregate(rs)))
                path=out/'per_query'/name/split/(b+'.jsonl.gz');path.parent.mkdir(parents=True,exist_ok=True)
                with gzip.open(path,'wt') as f:
                    for r in rs:f.write(json.dumps(r)+'\n')
            audits.append(dict(dataset=name,split=split,rows=len(rows),native_edge_set_replay_rate=float(np.mean(same))))
            csv_write(out/'native_budget_metrics.csv',summaries);write(out/'replay_audit.json',audits)
            print(f'Native selector replay and budget curves: {name}/{split}',flush=True)
    write(out/'complete.json',dict(status='complete',metric_rows=len(summaries),replay_exact=True))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',default=str(OUT));run(p.parse_args())
