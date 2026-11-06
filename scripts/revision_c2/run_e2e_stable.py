"""C2 precision repair: rerun all validation selection and test inference.

Keep the frozen legacy runner/scoring/CPU and C3 implementation unchanged.
Reuse the exact C3 FP32-encoder/BF16-LLM generator, never legacy FP16 caches.
"""
import argparse
import fcntl
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
import run_e2e as legacy
from common import ROOT,OUT,DATASETS,read,write,digest,freeze

HERE=Path(__file__).resolve().parent
C3=HERE.parent/'revision_c3'
sys.path.insert(0,str(C3))
from run_gpu import StableGenerator


def dependency_hashes():
    paths=[Path(__file__),HERE/'run_e2e.py',HERE/'common.py',C3/'run_gpu.py',C3/'c3lib.py',
           ROOT/'model/gnn.py',ROOT/'model/drkgc.py']
    return {str(p.relative_to(ROOT)):digest(p) for p in paths}


def validate_c3(directory):
    done=read(directory/'gpu_complete.json');p=read(directory/'protocol_gpu.json')
    if done['status']!='complete' or not done['all_test_rows']:
        raise ValueError('Only completed C3 stable runs may supply caches')
    if digest(C3/'run_gpu.py')!=p['runner_sha256'] or digest(C3/'c3lib.py')!=p['common_sha256']:
        raise ValueError('C3 generator dependencies changed')
    if 'BF16' not in p['precision'] or 'FP32' not in p['precision']:
        raise ValueError('C3 precision policy mismatch')
    return read(directory/'model_fingerprints.json')


def import_matching_cache(destination,source,cache):
    """Import prediction-only records after the caller has matched full fingerprints."""
    imported=0
    with destination.open('a') as output:
        for line in source.read_text().splitlines():
            r=json.loads(line)
            if r['key'] in cache:
                if cache[r['key']]!=r['prediction']:raise ValueError('Conflicting identical cache key')
                continue
            cache[r['key']]=r['prediction'];output.write(line+'\n');imported+=1
    return imported


def run(args):
    out=Path(args.out).resolve();cpu=Path(args.cpu_results).resolve()
    out.mkdir(parents=True,exist_ok=True)
    if (out/'protocol_e2e.json').exists() and not (out/'precision_protocol.json').exists():
        raise ValueError('Legacy output directory: select a new output; FP16 results must remain archived')
    if read(cpu/'cpu_complete.json')['status']!='complete':raise ValueError('Complete CPU results required')
    for name,sha in read(cpu/'protocol_cpu.json')['code_sha256'].items():
        if digest(HERE/name)!=sha:raise ValueError(f'CPU dependency changed: {name}')
    donor=Path(args.c3_results).resolve() if args.c3_results else None
    donor_models=validate_c3(donor) if donor else {}
    protocol=dict(version=1,precision='graph encoder float32; LLM bfloat16',
        load_policy='original graph weights directly FP32; base and PEFT directly BF16; no FP16 round trip',
        finite_policy='assert finite graph projection before and after BF16 cast; no clipping or sample exclusion',
        dependency_sha256=dependency_hashes(),cpu_protocol_sha256=digest(cpu/'protocol_cpu.json'),
        c3_cache_directory=str(donor) if donor else None,
        c3_model_fingerprints=donor_models,legacy_cache_reuse=False,
        search_policy='rerun every validation trial; freeze new auto/LODO choices before test; unchanged scoring and tie rule')
    freeze(out/'precision_protocol.json',protocol)
    events=[]

    class RepairedGenerator(StableGenerator):
        def __init__(self,name,model_path,cache_dir,offline):
            super().__init__(name,model_path,cache_dir,offline)
            import torch
            assert all(p.dtype==torch.float32 for p in self.model.graph_model.parameters() if p.is_floating_point())
            assert all(p.dtype==torch.bfloat16 for p in self.model.llm_model.parameters() if p.is_floating_point())
            event=dict(dataset=name,model_fingerprint=self.fingerprint,initial_cache_records=len(self.cache),
                       imported_from_c3=0,source_cache=None,source_sha256=None)
            if donor and name in donor_models:
                if self.fingerprint!=donor_models[name]:raise ValueError(f'{name}: full C3 model fingerprint mismatch')
                source=donor/'cache'/self.cache_file.name
                event.update(source_cache=str(source),source_sha256=digest(source))
                event['imported_from_c3']=import_matching_cache(self.cache_file,source,self.cache)
            self.event=event
            print('Stable precision/cache',event,flush=True)

        def close(self):
            self.event.update(new_generations=self.new_generations,final_cache_records=len(self.cache))
            events.append(self.event)
            write(out/'cache_provenance_latest.json',events)
            super().close()

    start=time.monotonic()
    original=legacy.Generator
    legacy.Generator=RepairedGenerator
    try:legacy.run(args)
    finally:legacy.Generator=original
    done=read(out/'e2e_complete.json')
    import torch
    write(out/'environment.json',dict(python=sys.version,gpu=torch.cuda.get_device_name(0),
        packages={n:importlib.metadata.version(n) for n in ['numpy','torch','dgl','transformers','peft','accelerate','safetensors']}))
    write(out/'precision_complete.json',dict(status=done['status'],all_test_rows=done['all_test_rows'],
        metric_rows=done['metric_rows'],precision_protocol_sha256=digest(out/'precision_protocol.json'),
        final_invocation_seconds=round(time.monotonic()-start,2),
        note='Invocation duration excludes previous interrupted invocations and C3 cache computation.'))


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cpu-results',default=str(OUT));p.add_argument('--out',default=str(OUT/'e2e_stable'))
    p.add_argument('--datasets',nargs='+',choices=list(DATASETS),default=list(DATASETS))
    p.add_argument('--model-path',default=None);p.add_argument('--offline',action='store_true')
    p.add_argument('--edge-trials',type=int,default=12)
    p.add_argument('--calibration-max-rows',type=int,default=0)
    p.add_argument('--test-max-rows',type=int,default=0)
    p.add_argument('--seed',type=int,default=20261105);p.add_argument('--bootstrap',type=int,default=2000)
    p.add_argument('--candidate-variants',nargs='+',default=['raw','original_soft','native_valid_grid','shared_equal','shared_learned','shared_lodo'])
    p.add_argument('--c3-results',default=None,help='Optional completed C3 stable directory; require exact full fingerprint and input-key matches')
    return p


if __name__=='__main__':
    p=parser();args=p.parse_args()
    if args.edge_trials<1 or args.bootstrap<1 or min(args.test_max_rows,args.calibration_max_rows)<0:p.error('Invalid count')
    if not args.candidate_variants or args.candidate_variants[0]!='raw':p.error('First candidate variant must be raw')
    Path(args.out).mkdir(parents=True,exist_ok=True)
    with (Path(args.out)/'.inference.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run(args)
