"""Audit graph-encoder FP16 overflow; compare identical weights in FP32."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
import argparse
import numpy as np
from c3lib import *


def run(args):
    import torch
    sys.path.insert(0,str(ROOT))
    from model import GraphEnhancer
    all_rows=[]
    for name in args.datasets:
        cfg=DATASETS[name];state=torch.load(ROOT/cfg['checkpoint']/'graph_model.bin',map_location='cpu')
        emb=torch.load(ROOT/cfg['embeddings'],map_location='cpu')
        output_size=state['adapter.3.weight'].shape[0]
        model=GraphEnhancer(emb,emb.shape[1],cfg['relations'],128,1,1024,output_size,'silu')
        model.load_state_dict(state);model=model.eval().cuda()
        rows,ctxs=load_dataset(name,'test');stats={}
        for dtype in ['float16','float32']:
            model=model.half() if dtype=='float16' else model.float()
            # Reload original checkpoint to avoid quantizing FP32 weights via FP16.
            if dtype=='float32':model.load_state_dict(state)
            bad=[];maximum=0.
            for i,(r,c) in enumerate(zip(rows,ctxs)):
                for variant,edges in [('source_raw',c.raw),('original_fuzzy',c.fuzzy)]:
                    with torch.inference_mode():
                        q,e=model(torch.tensor([c.q],device='cuda'),torch.tensor([c.candidates],device='cuda'),[sorted(edges)])
                        x=torch.cat([q,e]).float()
                        finite=bool(torch.isfinite(x).all())
                        if finite:maximum=max(maximum,float(x.abs().max()))
                    if not finite:bad.append(dict(row=i,query_id=c.q,variant=variant,edges=len(edges)))
            stats[dtype]=dict(nonfinite_cases=len(bad),max_abs_finite_output=maximum,cases=bad)
            print(name,dtype,len(bad),'nonfinite cases',flush=True)
        all_rows.append(dict(dataset=name,test_rows=len(rows),variants=['source_raw','original_fuzzy'],results=stats))
        write(Path(args.out),all_rows)
        del model;torch.cuda.empty_cache()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--datasets',nargs='+',choices=list(DATASETS),default=list(DATASETS))
    p.add_argument('--out',default=str(OUT/'precision_audit.json'))
    run(p.parse_args())
