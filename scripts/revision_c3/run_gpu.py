"""Full-test frozen-LLM and graph-representation retention experiments.

Use FP32 graph encoding and BF16 LLM inference after auditing FP16 graph overflow.
This precision policy invalidates C2 caches. Every new prediction is resumable.
"""
import argparse
import json
import os
import time
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import numpy as np
from c3lib import *


def load_lines(path,field='value'):
    if not path.exists():return {}
    result={};lines=path.read_text().splitlines()
    for i,line in enumerate(lines):
        try:r=json.loads(line)
        except json.JSONDecodeError:
            if i!=len(lines)-1:raise
            path.write_text('\n'.join(lines[:i])+'\n');break
        result[r['key']]=r[field]
    return result


class StableGenerator(Generator):
    def __init__(self,name,model_path,cache_dir,offline):
        import torch
        from transformers import AutoTokenizer,LlamaForCausalLM,GenerationConfig
        from peft import PeftModel
        sys.path.insert(0,str(ROOT))
        from model import GraphEnhancer,DrKGC
        if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
            raise RuntimeError('This protocol requires a CUDA GPU supporting BF16 (RTX 4090 supported).')
        self.torch=torch;torch.manual_seed(20261105);torch.cuda.manual_seed_all(20261105)
        cfg=DATASETS[name];checkpoint=ROOT/cfg['checkpoint']
        model_path=model_path or read(checkpoint/'adapter_config.json')['base_model_name_or_path']
        self.tokenizer=AutoTokenizer.from_pretrained(model_path,use_fast=False,local_files_only=offline)
        self.tokenizer.pad_token=self.tokenizer.eos_token
        self.tokenizer.add_tokens(['[QUERY]','[ENTITY]','[RELATION]'])
        base=LlamaForCausalLM.from_pretrained(model_path,torch_dtype=torch.bfloat16,device_map={'':0},
            low_cpu_mem_usage=True,local_files_only=offline)
        llm=PeftModel.from_pretrained(base,str(checkpoint)).bfloat16()
        emb=torch.load(ROOT/cfg['embeddings'],map_location='cpu')
        enhancer=GraphEnhancer(emb,emb.shape[1],cfg['relations'],128,1,1024,llm.config.hidden_size,llm.config.hidden_act)
        enhancer.load_state_dict(torch.load(checkpoint/'graph_model.bin',map_location='cpu'))
        self.model=DrKGC(self.tokenizer,llm,enhancer.float().cuda()).eval()
        self.gen=GenerationConfig(max_new_tokens=16,min_new_tokens=1,do_sample=False,num_beams=1,
            repetition_penalty=cfg['repetition'],no_repeat_ngram_size=0,bos_token_id=self.tokenizer.bos_token_id,
            eos_token_id=self.tokenizer.eos_token_id,pad_token_id=self.tokenizer.pad_token_id,return_dict_in_generate=True)
        self.fingerprint=object_digest(dict(
            checkpoint={p.name:digest(p) for p in checkpoint.iterdir() if p.suffix in ['.bin','.json','.safetensors']},
            embeddings=digest(ROOT/cfg['embeddings']),model=str(model_path),model_commit=getattr(llm.config,'_commit_hash',None),
            generation=self.gen.to_dict(),torch=torch.__version__,graph_dtype='float32',llm_dtype='bfloat16',
            graph_code=digest(ROOT/'model/gnn.py'),wrapper_code=digest(ROOT/'model/drkgc.py'),runner_sha256=digest(Path(__file__))))
        cache_dir.mkdir(parents=True,exist_ok=True)
        self.cache_file=cache_dir/f'{name}_{self.fingerprint[:16]}.jsonl'
        self.cache=load_lines(self.cache_file,'prediction')
        self.new_generations=0

    def predict(self,row):
        graph=sorted(row['subgraph'])
        key=object_digest(dict(input=row['input'],query=row['query_entity_id'],ids=row['rank_entities_id'],graph=graph))
        if key in self.cache:return self.cache[key]
        torch=self.torch;model=self.model
        tokens=self.tokenizer(row['input'],return_tensors='pt').input_ids.cuda()
        qmask=tokens==model.query_token_id;emask=tokens==model.entity_token_id
        assert int(qmask.sum())==1 and int(emask.sum())==20
        with torch.inference_mode():
            q,e=model.graph_model(torch.tensor([row['query_entity_id']],device='cuda'),
                torch.tensor([row['rank_entities_id']],device='cuda'),[graph])
            if not bool(torch.isfinite(q).all() and torch.isfinite(e).all()):
                raise FloatingPointError(f'FP32 encoder nonfinite: query {row["query_entity_id"]}')
            clean=tokens.clone();clean[qmask|emask]=self.tokenizer.pad_token_id
            embeds=model._get_input_embed_layer()(clean).clone()
            q=q.to(embeds.dtype);e=e.to(embeds.dtype)
            if not bool(torch.isfinite(q).all() and torch.isfinite(e).all()):
                raise FloatingPointError('Graph projection overflows LLM input dtype; no clipping performed')
            embeds[qmask]=q;embeds[emask]=e
            output=model.llm_model.generate(inputs_embeds=embeds,attention_mask=torch.ones_like(tokens),generation_config=self.gen)
        prediction=self.tokenizer.decode(output.sequences[0].cpu().tolist(),skip_special_tokens=True).strip()
        self.cache[key]=prediction
        with self.cache_file.open('a') as f:
            f.write(json.dumps(dict(key=key,prediction=prediction),ensure_ascii=False)+'\n');f.flush()
        self.new_generations+=1
        return prediction


def model_input_key(row,graph):
    return object_digest(dict(query=row['query_entity_id'],ids=row['rank_entities_id'],graph=sorted(graph)))


def embed(gen,row,graph):
    torch=gen.torch
    with torch.inference_mode():
        q,e=gen.model.graph_model(torch.tensor([row['query_entity_id']],device='cuda'),
            torch.tensor([row['rank_entities_id']],device='cuda'),[sorted(graph)])
        x=torch.cat([q,e],dim=0).float().cpu().numpy()
    assert np.isfinite(x).all()
    return x


def distance(a,b):
    a=a.astype(np.float64);b=b.astype(np.float64)
    an=np.linalg.norm(a,axis=1);bn=np.linalg.norm(b,axis=1)
    cosine=np.sum(a*b,axis=1)/np.maximum(an*bn,1e-15)
    cosine=np.clip(cosine,-1,1)
    relative=np.linalg.norm(a-b,axis=1)/np.maximum(bn,1e-15)
    return cosine.tolist(),relative.tolist()


def rep_metrics(value,gold_index):
    result={}
    for ref in ['raw','unique']:
        cos,rel=value[ref]
        result.update({f'query_cosine_vs_{ref}':cos[0],f'candidate_cosine_vs_{ref}':float(np.mean(cos[1:])),
            f'query_rel_l2_vs_{ref}':rel[0],f'candidate_rel_l2_vs_{ref}':float(np.mean(rel[1:])),
            f'gold_cosine_vs_{ref}':cos[gold_index+1] if gold_index is not None else None})
    return result


def benchmark(gen,rows,contexts,plan,repeats=3):
    torch=gen.torch
    # Label-blind fixed seed, one representative input per query ID.
    unique={}
    for i,r in enumerate(rows):unique.setdefault(r['query_entity_id'],i)
    ix=list(unique.values());np.random.default_rng(20261106).shuffle(ix);ix=ix[:32]
    keep=['source_raw','source_unique','original_fuzzy','random_s0','ppr_terminals','empty_graph']
    summaries=[]
    for v in [v for v in plan if v['key'] in keep]:
        for i in ix[:2]:embed(gen,rows[i],contexts[i].select(v))
        torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
        times=[]
        for _ in range(repeats):
            for i in ix:
                edges=contexts[i].select(v)
                torch.cuda.synchronize();start=time.perf_counter()
                embed(gen,rows[i],edges);torch.cuda.synchronize()
                times.append((time.perf_counter()-start)*1000)
        summaries.append(dict(variant=v['key'],queries=len(ix),repeats=repeats,calls=len(times),
            encoder_ms_mean=float(np.mean(times)),encoder_ms_p50=float(np.median(times)),encoder_ms_p95=float(np.quantile(times,.95)),
            resident_plus_peak_cuda_mib=torch.cuda.max_memory_allocated()/1024**2,
            scope='graph construction/encoder/projection/device-to-host; LLM resident but generation excluded'))
    return summaries


def run(args):
    out=Path(args.out).resolve();cpu=Path(args.cpu_results).resolve()
    cp=read(cpu/'protocol_cpu.json');done=read(cpu/'cpu_complete.json')
    if done['status']!='complete' and not args.max_rows:raise ValueError('Full GPU run requires a complete CPU run')
    if 'test' not in cp['splits']:raise ValueError('CPU test graphs required')
    for path,h in read(cpu/'input_hashes.json').items():
        if digest(ROOT/path)!=h:raise ValueError(f'Changed input: {path}')
    assert digest(HERE/'c3lib.py')==cp['code_sha256']['c3lib.py']
    names=args.datasets or cp['datasets'];assert set(names)<=set(cp['datasets'])
    plan=gpu_variants(cp['variants'])
    protocol=dict(version=1,datasets=names,max_rows=args.max_rows,variants=plan,bootstrap=args.bootstrap,
        cpu_protocol_sha256=digest(cpu/'protocol_cpu.json'),cpu_inputs_sha256=digest(cpu/'input_hashes.json'),
        runner_sha256=digest(Path(__file__)),common_sha256=digest(HERE/'c3lib.py'),
        metrics='exact answer primary; promote-to-front adjusted RR secondary; separate graph-encoder cosine/L2',
        reference='original fuzzy order fixed; source_raw retains duplicates; source_unique removes duplicate triples only',
        selection='all methods predefined; no validation/test winner selection',
        precision='graph encoder original checkpoint FP32; LLM BF16; finite checks before/after input cast; no clipping',
        skip_benchmark=args.skip_benchmark)
    freeze(out/'protocol_gpu.json',protocol)
    summaries=[];contrasts=[];bench=[];models={};provenance=[];start=time.monotonic()
    for name in names:
        gen=StableGenerator(name,args.model_path,out/'cache',args.offline)
        models[name]=gen.fingerprint
        upstream=ROOT/'results/revision_c2/e2e/cache'/gen.cache_file.name
        imported=0
        if upstream.exists():
            for line in upstream.read_text().splitlines():
                r=json.loads(line)
                if r['key'] not in gen.cache:gen.cache[r['key']]=r['prediction'];imported+=1
        rows,contexts=load_dataset(name,'test')
        if args.max_rows:rows=rows[:args.max_rows];contexts=contexts[:args.max_rows]
        raw_reps={};unique_reps={}
        for row,ctx in zip(rows,contexts):
            key=model_input_key(row,ctx.raw)
            if key not in raw_reps:raw_reps[key]=embed(gen,row,ctx.raw)
            ukey=model_input_key(row,ctx.edges)
            if ukey not in unique_reps:unique_reps[ukey]=raw_reps[key] if sorted(ctx.raw)==sorted(ctx.edges) else embed(gen,row,ctx.edges)
        repfile=out/'cache'/f'{name}_{gen.fingerprint[:16]}_representations.jsonl'
        repcache=load_lines(repfile);grouped={}
        for v in plan:
            scored=[];last=time.monotonic()
            for i,(row,ctx) in enumerate(zip(rows,contexts)):
                edges=ctx.select(v);r=dict(row,subgraph=[list(e) for e in edges])
                prediction=gen.predict(r)
                rkey=model_input_key(row,ctx.raw);ukey=model_input_key(row,ctx.edges);key=model_input_key(row,edges)
                repkey=object_digest([rkey,ukey,key])
                if repkey not in repcache:
                    rep=raw_reps[rkey] if key==rkey else unique_reps[ukey] if key==ukey else embed(gen,row,edges)
                    value=dict(raw=distance(rep,raw_reps[rkey]),unique=distance(rep,unique_reps[ukey]))
                    repcache[repkey]=value
                    with repfile.open('a') as f:f.write(json.dumps(dict(key=repkey,value=value))+'\n');f.flush()
                gi=row['rank_entities_id'].index(row['gold_entity_id']) if row['gold_entity_id'] in row['rank_entities_id'] else None
                score=score_prediction(row,prediction)
                scored.append(dict(row=i,query_id=row['query_entity_id'],gold_id=row['gold_entity_id'],prediction=prediction,
                    **score,**rep_metrics(repcache[repkey],gi),selected_edges=len(edges),
                    encoder_global_fallback=int(len(edges)<=10)))
                if time.monotonic()-last>30:
                    print(f'{name}/{v["key"]}: {i+1}/{len(rows)}; new generations={gen.new_generations}',flush=True);last=time.monotonic()
            grouped[v['key']]=scored
            raw=grouped['source_raw']
            for r,base in zip(scored,raw):r['prediction_agreement_raw']=int(normalize(r['prediction'])==normalize(base['prediction']))
            write(out/'predictions'/name/(v['key']+'.json'),scored)
            meta=dict(dataset=name,variant=v['key'],method=v['method'],budget=v['budget'],seed=v['seed'])
            summary=dict(**meta,**aggregate(scored))
            summaries.append(summary);csv_write(out/'e2e_metrics.csv',summaries)
            print(name,v['key'],{k:summary[k] for k in ['n','exact_match','adjusted_rr','prediction_agreement_raw','candidate_cosine_vs_raw']},flush=True)
        for v in plan:
            for ref in ['original_fuzzy','source_raw']:
                if v['key']==ref:continue
                for c in paired(grouped[v['key']],grouped[ref],['exact_match','adjusted_rr','candidate_cosine_vs_raw','candidate_rel_l2_vs_raw'],args.bootstrap):
                    contrasts.append(dict(dataset=name,variant=v['key'],reference=ref,**c))
        csv_write(out/'e2e_contrasts.csv',contrasts)
        if not args.skip_benchmark:
            bench.extend(dict(dataset=name,**r) for r in benchmark(gen,rows,contexts,plan))
            csv_write(out/'encoder_benchmark.csv',bench)
        provenance.append(dict(dataset=name,model_fingerprint=gen.fingerprint,upstream_cache=str(upstream),
            upstream_cache_sha256=digest(upstream) if upstream.exists() else None,imported_predictions=imported,
            new_generations_this_invocation=gen.new_generations,gpu_name=gen.torch.cuda.get_device_name(0)))
        write(out/'cache_provenance.json',provenance);write(out/'model_fingerprints.json',models)
        gen.close();print(f'Finished dataset {name}',flush=True)
    write(out/'gpu_complete.json',dict(status='smoke_only' if args.max_rows else 'complete',datasets=names,
        metric_rows=len(summaries),variants_per_dataset=len(plan),all_test_rows=not bool(args.max_rows),seconds=round(time.monotonic()-start,2)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cpu-results',default=str(OUT));p.add_argument('--out',default=str(OUT/'gpu'))
    p.add_argument('--datasets',nargs='+',choices=list(DATASETS));p.add_argument('--model-path',default=None)
    p.add_argument('--offline',action='store_true');p.add_argument('--max-rows',type=int,default=0)
    p.add_argument('--bootstrap',type=int,default=2000);p.add_argument('--skip-benchmark',action='store_true')
    args=p.parse_args()
    if args.max_rows<0 or args.bootstrap<1:p.error('Invalid count')
    run(args)
