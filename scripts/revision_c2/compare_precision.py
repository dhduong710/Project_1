"""Compare repaired C2 results with archived FP16 and check C3 shared anchors."""
import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path
import numpy as np
from common import ROOT,OUT,read,write,csv_write,digest,cluster_bootstrap
from run_e2e import normalize
from audit_precision_c2 import variant_inputs,encoder_key


def prediction_map(rows):
    result={(r['query_id'],r['gold_id']):r for r in rows}
    if len(result)!=len(rows):raise ValueError('Duplicate query/gold keys')
    return result


def run(args):
    root=Path(args.results).resolve();old=Path(args.legacy_results).resolve();new=Path(args.stable_results).resolve()
    out=root/'precision_comparison';out.mkdir(parents=True,exist_ok=True)
    cp=read(root/'protocol_cpu.json');gp=read(new/'protocol_e2e.json');op=read(old/'protocol_e2e.json')
    if read(new/'precision_complete.json')['status']!='complete':raise ValueError('Stable inference incomplete')
    for k in ['datasets','seed','edge_trials','candidate_variants','calibration_max_rows','test_max_rows']:
        if gp[k]!=op[k]:raise ValueError(f'Precision comparison protocol differs: {k}')
    ns=read(new/'edge_validation_search.json');os=read(old/'edge_validation_search.json')
    nsel=read(new/'frozen_edge_selection.json');osel=read(old/'frozen_edge_selection.json')
    trials=[];choices=[];changes=[];strata=[];per_query=[];anchors=[];decomposition=[]
    for name in gp['datasets']:
        for a,b in zip(ns[name],os[name]):
            assert a['trial']==b['trial'] and a['weights']==b['weights']
            r=dict(dataset=name,trial=a['trial'],n=a['n'])
            for metric in ['exact_match','adjusted_rr','invalid']:
                r.update({metric+'_legacy':b[metric],metric+'_stable':a[metric],metric+'_delta':a[metric]-b[metric]})
            trials.append(r)
        choice=dict(dataset=name)
        for prefix in ['auto','lodo']:
            field=prefix+'_trial'
            if field in nsel[name]:choice.update({field+'_legacy':osel[name][field],field+'_stable':nsel[name][field],field+'_changed':nsel[name][field]!=osel[name][field]})
        for label,search in [('legacy',os),('stable',ns)]:
            best=max(search[name],key=lambda r:(r['exact_match'],r['adjusted_rr'],-r['trial']))
            choice[label+'_best_ties']=sum(r['exact_match']==best['exact_match'] and r['adjusted_rr']==best['adjusted_rr'] for r in search[name])
        choices.append(choice)
        actual={label:{(s,a,v):rs for s,a,v,rs in variant_inputs(root,d,name)} for label,d in [('legacy',old),('stable',new)]}
        ap=root/'precision_audit/per_query'/f'{name}.jsonl.gz';audit={}
        if ap.exists():
            with gzip.open(ap,'rt') as f:
                for line in f:
                    r=json.loads(line)
                    if r['run']=='legacy_fp16':audit[(r['split'],r['arm'],r['variant'],r['query_id'],r['gold_id'])]=r
        for (split,arm,v),rows in actual['stable'].items():
            filename=v if arm=='edge_trial' else arm+'_'+v
            after=read(new/'predictions'/name/filename/(split+'.json'))
            before=read(old/'predictions'/name/filename/(split+'.json'))
            bl=prediction_map(before);assert set(bl)==set(prediction_map(after))
            oldrows={(r['query_entity_id'],r['gold_entity_id']):r for r in actual['legacy'][(split,arm,v)]}
            assert len(after)==len(rows)
            paired=[]
            for a,r in zip(after,rows):
                key=(a['query_id'],a['gold_id']);b=bl[key]
                assert key==(r['query_entity_id'],r['gold_entity_id'])
                ar=audit.get((split,arm,v,*key))
                paired.append(dict(dataset=name,split=split,arm=arm,variant=v,query_id=key[0],gold_id=key[1],
                    prediction_changed=int(normalize(a['prediction'])!=normalize(b['prediction'])),
                    encoder_input_changed=int(encoder_key(r)!=encoder_key(oldrows[key])),
                    legacy_fp16_nonfinite=ar['fp16_nonfinite'] if ar else None,
                    exact_delta=a['exact_match']-b['exact_match'],adjusted_rr_delta=a['adjusted_rr']-b['adjusted_rr']))
            per_query.extend(paired)
            summary=dict(dataset=name,split=split,arm=arm,variant=v,n=len(paired),
                changed_predictions=sum(r['prediction_changed'] for r in paired),
                changed_encoder_inputs=sum(r['encoder_input_changed'] for r in paired))
            summary['interpretation']='precision plus validation reselection' if summary['changed_encoder_inputs'] else 'same inputs, precision policy changed'
            for metric in ['exact_match','adjusted_rr','invalid','top1_copy']:
                summary[metric+'_legacy']=float(np.mean([r[metric] for r in before]))
                summary[metric+'_stable']=float(np.mean([r[metric] for r in after]))
                summary[metric+'_delta']=summary[metric+'_stable']-summary[metric+'_legacy']
            changes.append(summary)
            for flag in [0,1]:
                rs=[r for r in paired if r['legacy_fp16_nonfinite']==flag]
                if rs:strata.append(dict(dataset=name,split=split,arm=arm,variant=v,legacy_fp16_nonfinite=flag,n=len(rs),
                    changed_predictions=sum(r['prediction_changed'] for r in rs),exact_delta=float(np.mean([r['exact_delta'] for r in rs]))))
        c3=Path(args.c3_results)
        if (c3/'gpu_complete.json').exists():
            assert read(new/'model_fingerprints.json')[name]==read(c3/'model_fingerprints.json')[name]
            for cv,nv in [('source_raw','source_graph'),('original_fuzzy','original_fuzzy')]:
                c=prediction_map(read(c3/'predictions'/name/(cv+'.json')))
                rs=read(new/'predictions'/name/('graph_'+nv)/'test.json')
                assert set(c)==set(prediction_map(rs))
                mismatches=sum(normalize(r['prediction'])!=normalize(c[(r['query_id'],r['gold_id'])]['prediction']) for r in rs)
                anchors.append(dict(dataset=name,c3_variant=cv,c2_variant=nv,n=len(rs),prediction_mismatches=mismatches))
                assert mismatches==0,f'C2/C3 anchor mismatch: {name}/{nv}'
        diagnostic=new/'legacy_choice_diagnostic'
        if (diagnostic/'complete.json').exists():
            assert read(diagnostic/'complete.json')['status']=='complete'
            for variant in ['shared_auto','shared_edge_lodo']:
                v='graph_'+variant
                paths=[d/'predictions'/name/v/'test.json' for d in [old,diagnostic,new]]
                if not all(p.exists() for p in paths):continue
                maps=[prediction_map(read(p)) for p in paths]
                keys=list(maps[0]);assert all(set(m)==set(keys) for m in maps)
                for metric in ['exact_match','adjusted_rr','invalid']:
                    values=[np.array([m[k][metric] for k in keys]) for m in maps]
                    r=dict(dataset=name,variant=variant,metric=metric,n=len(keys),
                        legacy_fp16=float(values[0].mean()),legacy_choice_stable=float(values[1].mean()),new_choice_stable=float(values[2].mean()),
                        precision_at_old_choice=float((values[1]-values[0]).mean()),
                        reselection_at_stable_precision=float((values[2]-values[1]).mean()),total_change=float((values[2]-values[0]).mean()))
                    assert np.isclose(r['total_change'],r['precision_at_old_choice']+r['reselection_at_stable_precision'])
                    decomposition.append(r)
    for name,rs in [('variant_changes',changes),('validation_changes',trials),('selection_changes',choices),('nonfinite_strata',strata),('c3_anchor_checks',anchors),('adaptive_decomposition',decomposition)]:
        csv_write(out/(name+'.csv'),rs)
    path=out/'per_query.jsonl.gz'
    with gzip.open(path,'wt') as f:
        for r in per_query:f.write(json.dumps(r)+'\n')
    write(out/'complete.json',dict(status='complete',variant_rows=len(changes),test_variant_rows=sum(r['split']=='test' for r in changes),
        row_variant_pairs=len(per_query),all_cpu_artifacts_reused=True,
        audit_complete=(root/'precision_audit/complete.json').exists(),
        diagnostic_decomposition_rows=len(decomposition),
        legacy_protocol_sha256=digest(old/'protocol_e2e.json'),stable_protocol_sha256=digest(new/'precision_protocol.json'),
        caveat='Changes combine FP32 graph and BF16 LLM precision; adaptive graph arms can also reflect validation reselection. No single-component causal attribution.'))
    print('Precision comparison:',len(changes),'validation/test variants;',len(anchors),'C3 anchors matched',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',default=str(OUT));p.add_argument('--legacy-results',default=str(OUT/'e2e'))
    p.add_argument('--stable-results',default=str(OUT/'e2e_stable'));p.add_argument('--c3-results',default=str(ROOT/'results/revision_c3/gpu'))
    run(p.parse_args())
