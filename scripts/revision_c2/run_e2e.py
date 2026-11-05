"""Frozen-checkpoint LLM evaluation and validation-only edge-weight calibration.

One GPU, one dataset/model at a time. Every generated query is cached and resumable.
Candidate arm fixes source graphs. Graph arm fixes original fuzzy candidate order.
The learned candidate model is fit by run_cpu.py; edge calibration is black-box
validation search, NOT a learned GNN and NOT selected by candidate MRR.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np

from common import (ROOT,OUT,DATASETS,EDGE_DEFAULT,read,write,csv_write,freeze,digest,
    object_digest,load_rows,align,reorder_row,select_graph,graph_stats,mean_stats,
    cluster_bootstrap)


def normalize(text):
    text=str(text).strip()
    text=re.split(r'(?i)answer\s*:',text)[-1].strip().split('\n')[0]
    return re.sub(r'\s+',' ',text).strip(" \"'`.,;:").casefold()


def score_prediction(row,prediction):
    """Use a single explicit rule for all five datasets.

    Generated candidate is moved to the front of the supplied ranking.
    Invalid output occupies a virtual rank-1 slot. Absent gold ALWAYS has RR=0.
    Exact answer accuracy is separately reported and is the primary search metric.
    """
    names=row['rank_entities'];ids=row['rank_entities_id'];gold=row['gold_entity_id']
    ans=normalize(prediction)
    aliases=row.get('rank_entities_canonical',names)
    matches={i for i,(name,alias) in enumerate(zip(names,aliases)) if ans in {normalize(name),normalize(alias)}}
    # Ambiguous display names are invalid; no substring/containment matching.
    pi=next(iter(matches)) if len(matches)==1 else None
    gr=ids.index(gold)+1 if gold in ids else 21
    exact=pi is not None and ids[pi]==gold
    if gr==21: adjusted=21
    elif exact: adjusted=1
    elif pi is None or pi+1>gr: adjusted=min(21,gr+1)
    else: adjusted=gr
    return dict(candidate_rank=gr,pred_candidate_rank=pi+1 if pi is not None else 21,
        exact_match=int(exact),invalid=int(pi is None),top1_copy=int(pi==0),
        adjusted_rank=adjusted,adjusted_rr=1./adjusted if adjusted<=20 else 0.,
        candidate_rr=1./gr if gr<=20 else 0.,gold_present=int(gr<=20))


def summarize(scored):
    return dict(n=len(scored),**{k:float(np.mean([r[k] for r in scored])) for k in
        ['exact_match','invalid','top1_copy','adjusted_rr','candidate_rr','gold_present']})


def edge_candidates(seed,trials):
    # Default and interpretable controls precede seeded search candidates.
    base=[EDGE_DEFAULT,[1,1,1,1,1],[1,.35,.05,0,.05],[1,0,0,0,0],
          [1,.35,.25,.8,0],[1,.35,.05,1.6,.05]]
    rng=np.random.default_rng(seed)
    while len(base)<trials:
        w=np.array(EDGE_DEFAULT)*np.exp(rng.normal(0,.8,5))
        w/=w[0]  # Overall score scale is unidentifiable for TopEdges.
        base.append(w.tolist())
    return base[:trials]


class Generator:
    def __init__(self,name,model_path,cache_dir,offline):
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA unavailable. Run in the GPU-enabled server environment (outside sandbox if required).')
        from transformers import AutoTokenizer,LlamaForCausalLM,GenerationConfig
        from peft import PeftModel
        sys.path.insert(0,str(ROOT))
        from model import GraphEnhancer,DrKGC
        self.torch=torch
        torch.manual_seed(20261105)
        torch.cuda.manual_seed_all(20261105)
        cfg=DATASETS[name]
        checkpoint=ROOT/cfg['checkpoint']
        meta=read(checkpoint/'adapter_config.json')
        model_path=model_path or meta['base_model_name_or_path']
        self.tokenizer=AutoTokenizer.from_pretrained(model_path,use_fast=False,local_files_only=offline)
        self.tokenizer.pad_token=self.tokenizer.eos_token
        self.tokenizer.add_tokens(['[QUERY]','[ENTITY]','[RELATION]'])
        base=LlamaForCausalLM.from_pretrained(model_path,torch_dtype=torch.float16,
            device_map={'':0},low_cpu_mem_usage=True,local_files_only=offline)
        llm=PeftModel.from_pretrained(base,str(checkpoint)).half()
        emb=torch.load(ROOT/cfg['embeddings'],map_location='cpu')
        enhancer=GraphEnhancer(emb,emb.shape[1],cfg['relations'],128,1,1024,
            llm.config.hidden_size,llm.config.hidden_act)
        enhancer.load_state_dict(torch.load(checkpoint/'graph_model.bin',map_location='cpu'))
        enhancer=enhancer.half().cuda()
        self.model=DrKGC(self.tokenizer,llm,enhancer).eval()
        self.gen=GenerationConfig(max_new_tokens=16,min_new_tokens=1,do_sample=False,num_beams=1,
            repetition_penalty=cfg['repetition'],no_repeat_ngram_size=0,
            bos_token_id=self.tokenizer.bos_token_id,eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,return_dict_in_generate=True)
        checkpoint_hash={p.name:digest(p) for p in checkpoint.iterdir() if p.suffix in ['.bin','.json','.safetensors']}
        self.fingerprint=object_digest(dict(checkpoint=checkpoint_hash,model=str(model_path),
            model_commit=getattr(llm.config,'_commit_hash',None),generation=self.gen.to_dict(),
            embeddings=digest(ROOT/cfg['embeddings']),torch=torch.__version__,
            graph_code=digest(ROOT/'model/gnn.py'),wrapper_code=digest(ROOT/'model/drkgc.py'),
            runner_code=digest(Path(__file__))))
        cache_dir.mkdir(parents=True,exist_ok=True)
        self.cache_file=cache_dir/f'{name}_{self.fingerprint[:16]}.jsonl'
        self.cache={}
        if self.cache_file.exists():
            lines=self.cache_file.read_text().splitlines()
            for i,line in enumerate(lines):
                try:r=json.loads(line)
                except json.JSONDecodeError:
                    if i!=len(lines)-1:raise
                    # Repair an interrupted last write before appending.
                    self.cache_file.write_text('\n'.join(lines[:i])+'\n')
                    break
                self.cache[r['key']]=r['prediction']
        self.new_generations=0

    def predict(self,row):
        # Canonical edge ordering across ALL arms reduces irrelevant order differences.
        graph=sorted(row['subgraph'])
        payload=dict(input=row['input'],query=row['query_entity_id'],ids=row['rank_entities_id'],graph=graph)
        key=object_digest(payload)
        if key in self.cache:return self.cache[key]
        torch=self.torch
        tokens=self.tokenizer(row['input'],return_tensors='pt').input_ids.cuda()
        if int((tokens==self.model.entity_token_id).sum())!=20 or int((tokens==self.model.query_token_id).sum())!=1:
            raise ValueError('Prompt placeholder/ID mismatch')
        with torch.inference_mode():
            embeddings=self.model._replace_placeholders(tokens,torch.tensor([row['query_entity_id']],device='cuda'),
                torch.tensor([row['rank_entities_id']],device='cuda'),[graph])
            output=self.model.llm_model.generate(inputs_embeds=embeddings,
                attention_mask=torch.ones_like(tokens),generation_config=self.gen)
        text=self.tokenizer.decode(output.sequences[0].cpu().tolist(),skip_special_tokens=True).strip()
        self.cache[key]=text
        with self.cache_file.open('a',encoding='utf-8') as f:
            f.write(json.dumps(dict(key=key,prediction=text),ensure_ascii=False)+'\n')
            f.flush()
        self.new_generations+=1
        return text

    def close(self):
        del self.model
        import gc
        gc.collect();self.torch.cuda.empty_cache()


def canonical_graph_rows(name,split):
    raw=load_rows(name,split)
    fuzzy=align(raw,load_rows(name,split,'fuzzy'))
    rows=[reorder_row(r,[r['rank_entities_id'].index(c) for c in f['rank_entities_id']]) for r,f in zip(raw,fuzzy)]
    return rows,fuzzy


def select_calibration(rows,limit,seed):
    # Label-blind deterministic query-group subset; use all rows for final test.
    if limit<=0 or limit>=len(rows):return np.arange(len(rows))
    groups=np.unique([r['query_entity_id'] for r in rows]);np.random.default_rng(seed).shuffle(groups)
    selected=[]
    for g in groups:
        selected.extend(i for i,r in enumerate(rows) if r['query_entity_id']==g)
        if len(selected)>=limit:break
    return np.array(sorted(selected))


def evaluate(gen,rows,name,variant,split,out):
    scored=[];last=time.monotonic()
    for i,row in enumerate(rows):
        pred=gen.predict(row)
        scored.append(dict(row=i,query_id=row['query_entity_id'],gold_id=row['gold_entity_id'],
            prediction=pred,**score_prediction(row,pred)))
        if time.monotonic()-last>30:
            print(f'{name}/{split}/{variant}: {i+1}/{len(rows)}; new generations={gen.new_generations}',flush=True)
            last=time.monotonic()
    write(out/'predictions'/name/variant/f'{split}.json',scored)
    return scored


def run(args):
    out=Path(args.out).resolve();cpu=Path(args.cpu_results).resolve()
    if not (cpu/'cpu_complete.json').exists():raise FileNotFoundError('Run run_cpu.py first')
    trials=edge_candidates(args.seed,args.edge_trials)
    protocol=dict(version=1,datasets=args.datasets,seed=args.seed,edge_trials=trials,
        calibration_max_rows=args.calibration_max_rows,test_max_rows=args.test_max_rows,
        smoke_only=args.test_max_rows>0,
        candidate_variants=args.candidate_variants,
        checkpoint_policy='one frozen raw-backbone checkpoint per dataset; no variant-specific fine-tuning',
        graph_policy='original fuzzy candidate order fixed; each compressed graph uses original per-row edge budget',
        metric='exact candidate-ID match primary; promote-to-front adjusted RR@20 secondary; invalid virtual rank1',
        selection='validation exact accuracy, then adjusted MRR, then earlier predefined trial; source macro for LODO',
        cpu_protocol_sha256=digest(cpu/'protocol_cpu.json'),cpu_models_sha256=digest(cpu/'candidate_models.json'),
        code_sha256=digest(Path(__file__)),common_sha256=digest(Path(__file__).with_name('common.py')))
    freeze(out/'protocol_e2e.json',protocol)
    # Verify CPU exports still correspond to unchanged source artifacts.
    for path,h in read(cpu/'input_hashes.json').items():
        if digest(ROOT/path)!=h:raise ValueError(f'Input changed after CPU run: {path}')
    search={};models={};summaries=[];pairs=[]
    for name in args.datasets:
        gen=Generator(name,args.model_path,out/'cache',args.offline)
        models[name]=gen.fingerprint
        rows,fuzzy=canonical_graph_rows(name,'valid')
        ix=select_calibration(rows,args.calibration_max_rows,args.seed)
        write(out/'calibration_indices'/f'{name}.json',ix.tolist())
        search[name]=[]
        for j,w in enumerate(trials):
            candidates=[]
            for i in ix:
                r=dict(rows[i]);r['subgraph']=select_graph(r,w,budget=len(fuzzy[i]['subgraph']))
                candidates.append(r)
            scored=evaluate(gen,candidates,name,f'edge_trial_{j:02d}','valid',out)
            summary=dict(dataset=name,trial=j,weights=w,**summarize(scored))
            search[name].append(summary)
            print('edge calibration',name,j,summary,flush=True)
        gen.close()
        write(out/'edge_validation_search.json',search)
    selection={}
    for name in args.datasets:
        chosen=max(search[name],key=lambda r:(r['exact_match'],r['adjusted_rr'],-r['trial']))['trial']
        entry=dict(auto_trial=chosen,auto_weights=trials[chosen])
        sources=[d for d in args.datasets if d!=name]
        if sources:
            scores=[(float(np.mean([search[d][j]['exact_match'] for d in sources])),
                     float(np.mean([search[d][j]['adjusted_rr'] for d in sources])),-j) for j in range(len(trials))]
            j=max(range(len(trials)),key=lambda j:scores[j])
            entry.update(lodo_trial=j,lodo_weights=trials[j],source_datasets=sources)
        selection[name]=entry
    # Persist all selections before ANY test generation in this run.
    freeze(out/'frozen_edge_selection.json',selection)
    write(out/'model_fingerprints.json',models)
    for name in args.datasets:
        gen=Generator(name,args.model_path,out/'cache',args.offline)
        if gen.fingerprint!=models[name]:raise ValueError('Checkpoint changed between calibration and test')
        raw=load_rows(name,'test')
        if args.test_max_rows>0:raw=raw[:args.test_max_rows]
        baseline_rr=None;baseline_exact=None
        for variant in args.candidate_variants:
            orders=read(cpu/'orders'/name/variant/'test.json')[:len(raw)]
            rows=[reorder_row(r,o) for r,o in zip(raw,orders)]
            scored=evaluate(gen,rows,name,'candidate_'+variant,'test',out)
            result=dict(dataset=name,arm='candidate',variant=variant,split='test',**summarize(scored))
            rr=np.array([r['adjusted_rr'] for r in scored]);exact=np.array([r['exact_match'] for r in scored]);groups=np.array([r['query_id'] for r in scored])
            if baseline_rr is None:baseline_rr,baseline_exact=rr,exact
            result.update(cluster_bootstrap(rr-baseline_rr,groups,args.bootstrap,args.seed))
            ac=cluster_bootstrap(exact-baseline_exact,groups,args.bootstrap,args.seed)
            result.update(exact_delta=ac['delta_mrr'],exact_ci_low=ac['ci95_low'],exact_ci_high=ac['ci95_high'])
            summaries.append(result)
            print('candidate test',result,flush=True)
            csv_write(out/'e2e_metrics.csv',summaries)
        rows,fuzzy=canonical_graph_rows(name,'test')
        if args.test_max_rows>0:rows,fuzzy=rows[:args.test_max_rows],fuzzy[:args.test_max_rows]
        variants=[('source_graph',None),('original_fuzzy',None),('shared_fixed',EDGE_DEFAULT),('shared_auto',selection[name]['auto_weights'])]
        if 'lodo_weights' in selection[name]:variants.append(('shared_edge_lodo',selection[name]['lodo_weights']))
        reference=None;ref_exact=None
        for variant,w in variants:
            new=[];stats=[]
            for r,f in zip(rows,fuzzy):
                edges=r['subgraph'] if variant=='source_graph' else f['subgraph'] if variant=='original_fuzzy' else select_graph(r,w,budget=len(f['subgraph']))
                stats.append(graph_stats(r,edges))
                x=dict(r);x['subgraph']=edges;new.append(x)
            scored=evaluate(gen,new,name,'graph_'+variant,'test',out)
            result=dict(dataset=name,arm='graph',variant=variant,split='test',**summarize(scored),**mean_stats(stats))
            rr=np.array([r['adjusted_rr'] for r in scored]);exact=np.array([r['exact_match'] for r in scored]);groups=np.array([r['query_id'] for r in scored])
            if reference is None:reference,ref_exact=rr,exact
            result.update(cluster_bootstrap(rr-reference,groups,args.bootstrap,args.seed))
            ac=cluster_bootstrap(exact-ref_exact,groups,args.bootstrap,args.seed)
            result.update(exact_delta=ac['delta_mrr'],exact_ci_low=ac['ci95_low'],exact_ci_high=ac['ci95_high'])
            summaries.append(result)
            print('graph test',result,flush=True)
            csv_write(out/'e2e_metrics.csv',summaries)
        gen.close()
    write(out/'e2e_complete.json',dict(status='smoke_only' if args.test_max_rows>0 else 'complete',
        datasets=args.datasets,metric_rows=len(summaries),all_test_rows=args.test_max_rows==0,
        calibration_max_rows=args.calibration_max_rows))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cpu-results',default=str(OUT))
    p.add_argument('--out',default=str(OUT/'e2e'))
    p.add_argument('--datasets',nargs='+',choices=list(DATASETS),default=list(DATASETS))
    p.add_argument('--model-path',default=None,help='Local model folder or HF ID; default uses checkpoint metadata')
    p.add_argument('--offline',action='store_true')
    p.add_argument('--edge-trials',type=int,default=12)
    p.add_argument('--calibration-max-rows',type=int,default=0,help='0=all validation; positive=label-blind query-group subset')
    p.add_argument('--test-max-rows',type=int,default=0,help='SMOKE ONLY; positive invalidates publication-ready status')
    p.add_argument('--seed',type=int,default=20261105)
    p.add_argument('--bootstrap',type=int,default=2000)
    p.add_argument('--candidate-variants',nargs='+',default=['raw','original_soft','native_valid_grid','shared_equal','shared_learned','shared_lodo'])
    a=p.parse_args()
    if a.edge_trials<1:p.error('--edge-trials must be positive')
    if not a.candidate_variants or a.candidate_variants[0]!='raw':p.error('First candidate variant must be raw (paired reference)')
    os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
    run(a)
