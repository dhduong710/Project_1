"""Hold legacy selected edge weights fixed under repaired precision.

Diagnostic only, executed after the main stable selections are frozen. Separates
arithmetic-policy change from validation reselection in the two adaptive arms.
"""
import argparse
import fcntl
import os
from pathlib import Path
import sys
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
from common import ROOT,OUT,read,write,csv_write,digest,freeze,select_graph
from run_e2e import canonical_graph_rows,evaluate,summarize
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'revision_c3'))
from run_gpu import StableGenerator


def run(args):
    stable=Path(args.stable_results).resolve();old=Path(args.legacy_results).resolve()
    out=stable/'legacy_choice_diagnostic'
    done=read(stable/'precision_complete.json')
    if done['status']!='complete' or not done['all_test_rows']:raise ValueError('Complete main stable run required')
    gp=read(stable/'protocol_e2e.json');old_choices=read(old/'frozen_edge_selection.json')
    protocol=dict(version=1,role='diagnostic old selections at stable precision; no new model selection',
        runner_sha256=digest(Path(__file__)),stable_precision_sha256=digest(stable/'precision_protocol.json'),
        old_selection_sha256=digest(old/'frozen_edge_selection.json'),datasets=gp['datasets'])
    freeze(out/'protocol.json',protocol);summaries=[];provenance=[]
    for name in gp['datasets']:
        gen=StableGenerator(name,args.model_path,stable/'cache',args.offline)
        if gen.fingerprint!=read(stable/'model_fingerprints.json')[name]:raise ValueError('Stable model fingerprint mismatch')
        rows,fuzzy=canonical_graph_rows(name,'test')
        for variant,field in [('shared_auto','auto_weights'),('shared_edge_lodo','lodo_weights')]:
            if field not in old_choices[name]:continue
            weights=old_choices[name][field]
            inputs=[dict(r,subgraph=select_graph(r,weights,budget=len(f['subgraph']))) for r,f in zip(rows,fuzzy)]
            scored=evaluate(gen,inputs,name,'graph_'+variant,'test',out)
            summary=dict(dataset=name,arm='graph',variant=variant,**summarize(scored))
            summaries.append(summary);csv_write(out/'metrics.csv',summaries)
            print('Legacy-choice stable diagnostic',summary,flush=True)
        provenance.append(dict(dataset=name,model_fingerprint=gen.fingerprint,new_generations=gen.new_generations))
        gen.close()
    write(out/'cache_provenance.json',provenance)
    write(out/'complete.json',dict(status='complete',metric_rows=len(summaries),role=protocol['role']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stable-results',default=str(OUT/'e2e_stable'));p.add_argument('--legacy-results',default=str(OUT/'e2e'))
    p.add_argument('--model-path',default=None);p.add_argument('--offline',action='store_true')
    args=p.parse_args()
    with (Path(args.stable_results)/'.inference.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run(args)
