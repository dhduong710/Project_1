"""Audit FP16 versus FP32/BF16 on the actual legacy and repaired C2 graph inputs.

Encoder-only diagnostic; no new LLM generation and no selection from test scores.
Preserves each query/candidate order and edge occurrence, deduplicating only
identical encoder calls for computation. Variant counts still refer to all rows.
"""
import argparse
import fcntl
from collections import defaultdict
import gzip
import json
import os
from pathlib import Path
import sys
import time
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
from common import ROOT,OUT,DATASETS,EDGE_DEFAULT,read,write,csv_write,digest,object_digest,freeze,load_rows,reorder_row,select_graph
from run_e2e import canonical_graph_rows,select_calibration


def encoder_key(row):
    return object_digest(dict(query=row['query_entity_id'],ids=row['rank_entities_id'],graph=sorted(row['subgraph'])))


def variant_inputs(cpu,gpu,name):
    p=read(gpu/'protocol_e2e.json');selection=read(gpu/'frozen_edge_selection.json')[name]
    rows,fuzzy=canonical_graph_rows(name,'valid')
    ix=select_calibration(rows,p['calibration_max_rows'],p['seed'])
    for j,w in enumerate(p['edge_trials']):
        yield 'valid','edge_trial',f'edge_trial_{j:02d}',[
            dict(rows[i],subgraph=select_graph(rows[i],w,budget=len(fuzzy[i]['subgraph']))) for i in ix]
    raw=load_rows(name,'test')
    if p['test_max_rows']:raw=raw[:p['test_max_rows']]
    for v in p['candidate_variants']:
        orders=read(cpu/'orders'/name/v/'test.json')[:len(raw)]
        yield 'test','candidate',v,[reorder_row(r,o) for r,o in zip(raw,orders)]
    rows,fuzzy=canonical_graph_rows(name,'test');rows,fuzzy=rows[:len(raw)],fuzzy[:len(raw)]
    variants=[('source_graph',None),('original_fuzzy',None),('shared_fixed',EDGE_DEFAULT),('shared_auto',selection['auto_weights'])]
    if 'lodo_weights' in selection:variants.append(('shared_edge_lodo',selection['lodo_weights']))
    for v,w in variants:
        yield 'test','graph',v,[dict(r,subgraph=r['subgraph'] if v=='source_graph' else f['subgraph'] if v=='original_fuzzy' else select_graph(r,w,budget=len(f['subgraph']))) for r,f in zip(rows,fuzzy)]


def run(args):
    import torch
    if not torch.cuda.is_available():raise RuntimeError('CUDA is required for the encoder precision audit')
    sys.path.insert(0,str(ROOT))
    from model import GraphEnhancer
    cpu=Path(args.results).resolve();out=Path(args.out).resolve()
    dirs={'legacy_fp16':Path(args.legacy_results).resolve(),'stable':Path(args.stable_results).resolve()}
    for d in dirs.values():
        if read(d/'e2e_complete.json')['status']!='complete':raise ValueError('Completed runs required')
    protocol=dict(version=1,datasets=args.datasets,runner_sha256=digest(Path(__file__)),
        input_hashes_sha256=digest(cpu/'input_hashes.json'),
        runs={k:{f:digest(d/f) for f in ['protocol_e2e.json','frozen_edge_selection.json']} for k,d in dirs.items()},
        scope='actual encoder calls; FP16 and original checkpoint FP32, plus FP32-to-BF16 and FP32-to-FP16 casts; no clipping',
        checkpoint_sha256={n:digest(ROOT/DATASETS[n]['checkpoint']/'graph_model.bin') for n in args.datasets})
    freeze(out/'protocol.json',protocol)
    summaries=[];total_unique=0;start=time.monotonic()
    for name in args.datasets:
        unique={};groups=[]
        for label,d in dirs.items():
            for split,arm,v,rows in variant_inputs(cpu,d,name):
                keys=[]
                for r in rows:
                    key=encoder_key(r);unique.setdefault(key,r);keys.append(key)
                groups.append((label,split,arm,v,rows,keys))
        cfg=DATASETS[name];state=torch.load(ROOT/cfg['checkpoint']/'graph_model.bin',map_location='cpu')
        emb=torch.load(ROOT/cfg['embeddings'],map_location='cpu')
        model=GraphEnhancer(emb,emb.shape[1],cfg['relations'],128,1,1024,state['adapter.3.weight'].shape[0],'silu').eval().cuda()
        measured={key:{} for key in unique}
        for dtype in ['fp16','fp32']:
            model=model.half() if dtype=='fp16' else model.float()
            model.load_state_dict(state)  # original FP32 values, never recover by upcasting rounded FP16 weights
            for key,r in unique.items():
                with torch.inference_mode():
                    q,e=model(torch.tensor([r['query_entity_id']],device='cuda'),torch.tensor([r['rank_entities_id']],device='cuda'),[sorted(r['subgraph'])])
                    x=torch.cat([q,e]);finite=bool(torch.isfinite(x).all())
                    measured[key][dtype+'_nonfinite']=int(not finite)
                    measured[key][dtype+'_max_abs']=float(x.abs().max()) if finite else None
                    if dtype=='fp32':
                        measured[key]['fp32_to_bf16_nonfinite']=int(not bool(torch.isfinite(x.bfloat16()).all()))
                        measured[key]['fp32_to_fp16_nonfinite']=int(not bool(torch.isfinite(x.half()).all()))
            print(name,dtype,'unique calls',len(unique),'nonfinite',sum(x[dtype+'_nonfinite'] for x in measured.values()),flush=True)
        records=[]
        for label,split,arm,v,rows,keys in groups:
            values=[measured[k] for k in keys]
            for i,(r,key) in enumerate(zip(rows,keys)):
                records.append(dict(dataset=name,run=label,split=split,arm=arm,variant=v,row=i,
                    query_id=r['query_entity_id'],gold_id=r['gold_entity_id'],encoder_key=key,**measured[key]))
            summary=dict(dataset=name,run=label,split=split,arm=arm,variant=v,n=len(rows),unique_encoder_calls=len(set(keys)))
            for field in ['fp16_nonfinite','fp32_nonfinite','fp32_to_bf16_nonfinite','fp32_to_fp16_nonfinite']:
                summary[field]=sum(r[field] for r in values)
            for field in ['fp16_max_abs','fp32_max_abs']:
                summary[field]=max((r[field] for r in values if r[field] is not None),default=None)
            summaries.append(summary)
        path=out/'per_query'/f'{name}.jsonl.gz';path.parent.mkdir(parents=True,exist_ok=True)
        with gzip.open(path,'wt') as f:
            for r in records:f.write(json.dumps(r,allow_nan=False)+'\n')
        write(out/f'{name}_nonfinite_cases.json',[r for r in records if r['fp16_nonfinite'] or r['fp32_nonfinite'] or r['fp32_to_bf16_nonfinite']])
        csv_write(out/'summary.csv',summaries)
        total_unique+=len(unique)
        del model;torch.cuda.empty_cache()
    if any(r['fp32_nonfinite'] or r['fp32_to_bf16_nonfinite'] for r in summaries):
        raise FloatingPointError('Repaired precision is not finite for all audited calls')
    write(out/'complete.json',dict(status='complete',summary_rows=len(summaries),unique_encoder_calls=total_unique,
        all_fp32_bf16_finite=True,seconds=round(time.monotonic()-start,2)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',default=str(OUT));p.add_argument('--legacy-results',default=str(OUT/'e2e'))
    p.add_argument('--stable-results',default=str(OUT/'e2e_stable'));p.add_argument('--out',default=str(OUT/'precision_audit'))
    p.add_argument('--datasets',nargs='+',choices=list(DATASETS),default=list(DATASETS))
    args=p.parse_args()
    with (Path(args.stable_results)/'.inference.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run(args)
