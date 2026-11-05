"""Read-only preflight. Exit nonzero if requested GPU execution is unavailable."""
import argparse
import importlib.metadata
import json
import subprocess
from pathlib import Path

from common import ROOT,DATASETS


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gpu',action='store_true')
    args=p.parse_args()
    info={'packages':{},'datasets':{},'errors':[]}
    for name in ['numpy','torch','dgl','transformers','peft','accelerate','safetensors']:
        try:info['packages'][name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:info['packages'][name]='not_installed'
    for name,cfg in DATASETS.items():
        paths=[ROOT/cfg[k]/f'{s}.json' for k in ['raw','soft','fuzzy'] for s in ['valid','test']]
        paths += [ROOT/cfg['embeddings'],ROOT/cfg['checkpoint']/'adapter_config.json',ROOT/cfg['checkpoint']/'graph_model.bin']
        adapter=ROOT/cfg['checkpoint']
        if not any((adapter/n).exists() for n in ['adapter_model.bin','adapter_model.safetensors']):
            paths.append(adapter/'adapter_model.bin')
        missing=[str(x.relative_to(ROOT)) for x in paths if not x.exists()]
        info['datasets'][name]={'missing_files':missing}
        info['errors'].extend(missing)
    if args.gpu:
        try:
            import torch
            import dgl
            import transformers
            import peft
            info['cuda_available']=torch.cuda.is_available()
            if not info['cuda_available']:info['errors'].append('CUDA unavailable in this process')
            else:
                info['gpu_name']=torch.cuda.get_device_name(0)
                info['gpu_vram_gib']=torch.cuda.get_device_properties(0).total_memory/(1024**3)
        except Exception as e:info['errors'].append(repr(e))
    print(json.dumps(info,indent=2))
    raise SystemExit(bool(info['errors']))


if __name__=='__main__':main()
