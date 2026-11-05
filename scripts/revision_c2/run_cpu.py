"""Candidate calibration, transfer, sensitivity, and topology-only graph audits."""
from __future__ import annotations

import argparse
import itertools
import time
from pathlib import Path

import numpy as np

from common import (ROOT, OUT, DATASETS, NATIVE, FEATURES, EDGE_FEATURES, EDGE_DEFAULT,
    read, write, csv_write, digest, freeze, environment, extract, load_rows, align,
    row_key, metrics, ranks, rr_of, order_of, native_score, native_order, subset, choose_l2,
    fit_pairwise, cluster_bootstrap, select_graph, graph_stats, mean_stats, reorder_row)


def combine(arrays):
    keys=["x","native","gold","groups","ids"]
    result={k:np.concatenate([a[k] for a in arrays]) for k in keys}
    domains=np.concatenate([np.full(len(a["gold"]),i) for i,a in enumerate(arrays)])
    result["domain"]=domains
    unique={}
    result["groups"]=np.array([unique.setdefault((int(d),int(g)),len(unique)) for d,g in zip(domains,result["groups"])])
    return result


def run(args):
    out=Path(args.out).resolve()
    protocol={"version":1,"datasets":args.datasets,"seed":args.seed,"folds":args.folds,
        "steps":args.steps,"bootstrap":args.bootstrap,"repeats":args.repeats,
        "l2_grid":[0.001,.01,.1,1.0],"native_beta":[0.,.1,.25,.5,.75,1.,2.],
        "native_gamma":[0.,.1,.2,.5],"native_mu":[0.,.25,.5,.75,.8,.9,.95,1.],
        "fractions":[.1,.25,.5,1.],"jitter_sigma":[.05,.1,.25,.5],
        "candidate_features":FEATURES,"edge_features":EDGE_FEATURES,"edge_default":EDGE_DEFAULT,
        "learned_objective":"pairwise logistic, nonnegative coefficients on signed features, L2",
        "selection":"query-group CV on existing validation only; never test-score selection",
        "transfer":"LODO: no target dataset validation labels in fit or hyperparameter selection",
        "scope":"Retrospective calibration study on already-used benchmarks, not a new prospective holdout",
        "code_sha256":{n:digest(Path(__file__).parent/n) for n in ['common.py','run_cpu.py']},
        "environment":environment()}
    freeze(out/"protocol_cpu.json",protocol)
    start=time.time()
    cache={}; audits=[]; all_metrics=[]; per_query=[]; cv_rows=[]; grid_rows=[]; weights=[]; curves=[]; sensitivities=[]
    exported={}; model_state={}; input_hashes={}
    for name in args.datasets:
        cache[name]={}
        for split in ["valid","test"]:
            rows,a,fp=extract(name,split)
            a["ids"]=np.array([r["rank_entities_id"] for r in rows])
            cache[name][split]=(rows,a)
            for p in [ROOT/DATASETS[name][k]/f"{split}.json" for k in ["raw","soft","fuzzy"]]+[fp]:
                input_hashes[str(p.relative_to(ROOT))]=digest(p)
            reproduced=native_order(a,NATIVE[name],name)
            if not np.array_equal(reproduced,a['original']):
                raise ValueError(f"Original soft-support replay failed: {name}/{split}")
            audits.append({"dataset":name,"split":split,"rows":len(rows),"unique_queries":len(np.unique(a['groups'])),
                "recoverable_gold_rows":int(np.sum(a['gold']>=0)),
                "native_formula_same_order_rate":float(np.mean(np.all(reproduced==a['original'],axis=1))),
                "native_formula_mrr":metrics(reproduced,a['gold'])["mrr_at20"],
                "original_soft_mrr":metrics(a['original'],a['gold'])["mrr_at20"],
                "feature_source":str(fp.relative_to(ROOT)),
                "alignment":"candidate IDs and original ranks; repoDB positional outer rows, otherwise query/gold IDs"})
        vg=set(cache[name]['valid'][1]['groups']); tg=set(cache[name]['test'][1]['groups'])
        audits.append({"dataset":name,"split":"overlap_audit","valid_test_shared_query_ids":len(vg&tg),
            "interpretation":"Task is transductive. Group CV prevents within-validation query overlap, not new-disease generalization."})
        print(f"Loaded and aligned {name}",flush=True)
    freeze(out/"input_hashes.json",input_hashes)
    write(out/"input_audit.json",audits)

    def record(name,variant,orders,config=None):
        test=cache[name]['test'][1]
        baseline=rr_of(test['original'],test['gold'])
        for split,order in orders.items():
            rows,a=cache[name][split]
            result={"dataset":name,"variant":variant,"split":split,**metrics(order,a['gold'])}
            result['same_top1_vs_raw']=float(np.mean(order[:,0]==0))
            result['mean_rank_displacement']=float(np.mean(np.abs(np.argsort(order,axis=1)-np.arange(20))))
            if split=='test':
                result.update(cluster_bootstrap(rr_of(order,a['gold'])-baseline,a['groups'],args.bootstrap,args.seed))
            all_metrics.append(result)
            if split=='test':
                r=ranks(order,a['gold'])
                for i,rank in enumerate(r):
                    per_query.append(dict(dataset=name,variant=variant,row=i,query_id=int(a['groups'][i]),
                        gold_id=int(rows[i]['gold_entity_id']),rank=int(rank),rr=float(1/rank) if rank<=20 else 0.))
            if variant in ['raw','original_soft','native_valid_grid','shared_equal','shared_learned','shared_lodo']:
                exported[(name,variant,split)]=order
        if config is not None:
            model_state.setdefault(name,{})[variant]=config

    # Selection always occurs before test scores are computed for that variant.
    for name in args.datasets:
        valid=cache[name]['valid'][1]
        record(name,'raw',{s:np.tile(np.arange(20),(len(a['gold']),1)) for s,(_,a) in cache[name].items()})
        record(name,'original_soft',{s:a['original'] for s,(_,a) in cache[name].items()})
        record(name,'native_fixed_b050',{s:native_order(a,[.5,.1,0.],name) for s,(_,a) in cache[name].items()},dict(beta=.5,gamma=.1,mu=0.))
        grid=[]
        for beta,gamma,mu in itertools.product(protocol['native_beta'],protocol['native_gamma'],protocol['native_mu']):
            m=metrics(native_order(valid,[beta,gamma,mu],name),valid['gold'])
            item=dict(dataset=name,beta=beta,gamma=gamma,mu=mu,valid_mrr=m['mrr_at20'],valid_hits1=m['hits1'])
            grid.append(item);grid_rows.append(item)
        # Conservative tie-break: prefer more original rank prior, then smaller penalties.
        best=max(grid,key=lambda r:(r['valid_mrr'],r['mu'],-r['beta'],-r['gamma']))
        pars=[best[k] for k in ['beta','gamma','mu']]
        record(name,'native_valid_grid',{s:native_order(a,pars,name) for s,(_,a) in cache[name].items()},best)
        record(name,'shared_equal',{s:order_of(a['x']@np.ones(len(FEATURES))) for s,(_,a) in cache[name].items()},dict(weights=[1.]*len(FEATURES)))
        for constrained,variant in [(True,'shared_learned'),(False,'shared_learned_unconstrained')]:
            l2,cv=choose_l2(valid,protocol['l2_grid'],args.folds,args.seed,args.steps,constrained)
            cv_rows.extend(dict(dataset=name,variant=variant,**r) for r in cv)
            w=fit_pairwise(valid,l2,args.steps,constrained)
            record(name,variant,{s:order_of(a['x']@w) for s,(_,a) in cache[name].items()},dict(weights=w.tolist(),l2=l2))
            weights.append(dict(dataset=name,variant=variant,l2=l2,**dict(zip(FEATURES,w.tolist()))))
        # Feature removal refits on validation; tests identify which shared cues matter.
        for j,feature in enumerate(FEATURES):
            av={k:v.copy() for k,v in valid.items()};av['x'][:,:,j]=0
            l2,_=choose_l2(av,protocol['l2_grid'],args.folds,args.seed,args.steps)
            w=fit_pairwise(av,l2,args.steps);w[j]=0
            record(name,'ablate_'+feature,{s:order_of(a['x']@w) for s,(_,a) in cache[name].items()},dict(weights=w.tolist(),l2=l2))
        # Calibration label efficiency; nested group-CV is rerun inside each subset.
        groups=np.unique(valid['groups'])
        for repeat in range(args.repeats):
            shuffled=groups.copy();np.random.default_rng(args.seed+repeat).shuffle(shuffled)
            for fraction in protocol['fractions']:
                selected=shuffled[:max(2,int(math_ceil(len(groups)*fraction)))]
                a=subset(valid,np.flatnonzero(np.isin(valid['groups'],selected)))
                l2,_=choose_l2(a,protocol['l2_grid'],args.folds,args.seed+repeat,args.steps)
                w=fit_pairwise(a,l2,args.steps)
                test=cache[name]['test'][1]
                curves.append(dict(dataset=name,fraction=fraction,seed=args.seed+repeat,calibration_groups=len(selected),
                    calibration_rows=len(a['gold']),recoverable_calibration_rows=int(np.sum(a['gold']>=0)),l2=l2,
                    **metrics(order_of(test['x']@w),test['gold'])))
        # Multiplicative coefficient perturbation, not independent per-candidate score noise.
        for family in ['native_selected','shared_learned']:
            for sigma in protocol['jitter_sigma']:
                for repeat in range(args.repeats):
                    rng=np.random.default_rng(args.seed+repeat)
                    test=cache[name]['test'][1]
                    if family=='native_selected':
                        p=np.array(NATIVE[name]);p=p*np.exp(rng.normal(0,sigma,3));p[2]=min(1.,p[2])
                        o=native_order(test,p,name);ref=test['original']
                    else:
                        w=np.array(model_state[name]['shared_learned']['weights'])*np.exp(rng.normal(0,sigma,len(FEATURES)))
                        o=order_of(test['x']@w);ref=exported[(name,'shared_learned','test')]
                    sensitivities.append(dict(dataset=name,family=family,sigma=sigma,seed=args.seed+repeat,
                        same_top1=float(np.mean(o[:,0]==ref[:,0])),**metrics(o,test['gold'])))
        print(f"Completed candidate calibration: {name}",flush=True)

    # Cross-dataset transfer has no target labels in training/model selection.
    for target in args.datasets:
        sources=[d for d in args.datasets if d!=target]
        if not sources:
            continue
        pooled=combine([cache[d]['valid'][1] for d in sources])
        # Leave-one-source-dataset-out CV, macro averaging prevents large datasets dominating.
        cross=[]
        for l2 in protocol['l2_grid']:
            scores=[]
            if len(sources)>1:
                for held in sources:
                    train=combine([cache[d]['valid'][1] for d in sources if d!=held])
                    w=fit_pairwise(train,l2,args.steps)
                    a=cache[held]['valid'][1]
                    scores.append(metrics(order_of(a['x']@w),a['gold'])['mrr_at20'])
            cross.append(dict(l2=l2,source_macro_mrr=float(np.mean(scores)) if scores else 0.))
        best=max(cross,key=lambda r:(r['source_macro_mrr'],r['l2']))
        w=fit_pairwise(pooled,best['l2'],args.steps)
        record(target,'shared_lodo',{s:order_of(a['x']@w) for s,(_,a) in cache[target].items()},
            dict(weights=w.tolist(),l2=best['l2'],source_datasets=sources,source_cv=cross))
        weights.append(dict(dataset=target,variant='shared_lodo',l2=best['l2'],**dict(zip(FEATURES,w.tolist()))))
        for source in sources:
            w=np.array(model_state[source]['shared_learned']['weights'])
            record(target,'transfer_from_'+source,{'test':order_of(cache[target]['test'][1]['x']@w)},dict(source=source,weights=w.tolist()))
    write(out/'candidate_models.json',model_state)
    csv_write(out/'candidate_metrics.csv',all_metrics)
    csv_write(out/'candidate_per_query.csv',per_query)
    csv_write(out/'calibration_cv.csv',cv_rows)
    csv_write(out/'native_validation_grid.csv',grid_rows)
    csv_write(out/'learned_weights.csv',weights)
    csv_write(out/'label_efficiency.csv',curves)
    csv_write(out/'coefficient_sensitivity.csv',sensitivities)
    for (name,variant,split),order in exported.items():
        write(out/'orders'/name/variant/f'{split}.json',order.tolist())
    # Graph audit fixes the original fuzzy input candidate order (raw for repoDB).
    graphs=[]
    for name in args.datasets:
        for split in ['valid','test']:
            rows=cache[name][split][0]
            fuzzy=align(rows,load_rows(name,split,'fuzzy'))
            paired=[]
            for r,f in zip(rows,fuzzy):
                indices=[r['rank_entities_id'].index(cid) for cid in f['rank_entities_id']]
                paired.append(reorder_row(r,indices))
            default=[select_graph(r,budget=len(f['subgraph'])) for r,f in zip(paired,fuzzy)]
            variants=[('original_fuzzy',None,None),('shared_fixed',EDGE_DEFAULT,None),('shared_equal',[1]*5,None)]
            variants.extend((f'budget_{ratio}',EDGE_DEFAULT,ratio) for ratio in [.35,.55,.75])
            for variant,w,ratio in variants:
                stats=[]
                for r,f,ref in zip(paired,fuzzy,default):
                    edges=f['subgraph'] if w is None else select_graph(r,w,ratio=ratio or .55,budget=None if ratio else len(f['subgraph']))
                    stats.append(graph_stats(r,edges,ref))
                graphs.append(dict(dataset=name,split=split,variant=variant,**mean_stats(stats)))
            for sigma in protocol['jitter_sigma']:
                for repeat in range(args.repeats):
                    w=np.array(EDGE_DEFAULT)*np.exp(np.random.default_rng(args.seed+repeat).normal(0,sigma,5))
                    stats=[graph_stats(r,select_graph(r,w,budget=len(f['subgraph'])),ref) for r,f,ref in zip(paired,fuzzy,default)]
                    graphs.append(dict(dataset=name,split=split,variant='coefficient_jitter',sigma=sigma,seed=args.seed+repeat,**mean_stats(stats)))
        print(f"Completed graph-weight audit: {name}",flush=True)
    csv_write(out/'graph_weight_audit.csv',graphs)
    write(out/'cpu_complete.json',dict(status='complete',seconds=round(time.time()-start,2),
        datasets=args.datasets,candidate_metric_rows=len(all_metrics),graph_audit_rows=len(graphs),
        warning='Topology audits are not E2E results. Candidate experiment does not retrain the upstream ranker/LLM.'))
    print(f"CPU suite complete: {out}",flush=True)


def math_ceil(x):
    return int(np.ceil(x))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',default=str(OUT))
    p.add_argument('--datasets',nargs='+',choices=list(DATASETS),default=list(DATASETS))
    p.add_argument('--seed',type=int,default=20261105)
    p.add_argument('--folds',type=int,default=5)
    p.add_argument('--steps',type=int,default=250)
    p.add_argument('--bootstrap',type=int,default=2000)
    p.add_argument('--repeats',type=int,default=5)
    run(p.parse_args())
