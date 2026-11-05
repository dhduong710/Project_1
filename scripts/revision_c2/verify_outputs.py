"""Read-only consistency checks for a completed Comment 2 experiment/export."""
import argparse
import csv
import math
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ROOT, OUT, read, digest, load_rows


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def run(args):
    root=Path(args.results).resolve()
    gpu=Path(args.e2e_results).resolve() if args.e2e_results else root/'e2e'
    cpu_done=read(root/'cpu_complete.json')
    gpu_done=read(gpu/'e2e_complete.json')
    assert cpu_done['status']=='complete', 'CPU is incomplete'
    assert gpu_done['status']=='complete' and gpu_done['all_test_rows'], 'GPU is incomplete or smoke-only'
    cp=read(root/'protocol_cpu.json');gp=read(gpu/'protocol_e2e.json')
    for name,sha in cp['code_sha256'].items():
        assert digest(Path(__file__).with_name(name))==sha, f'CPU code changed: {name}'
    assert digest(Path(__file__).with_name('run_e2e.py'))==gp['code_sha256'], 'E2E code changed'
    assert digest(Path(__file__).with_name('common.py'))==gp['common_sha256'], 'Common code changed'
    assert digest(root/'protocol_cpu.json')==gp['cpu_protocol_sha256']
    assert digest(root/'candidate_models.json')==gp['cpu_models_sha256']
    for path,sha in read(root/'input_hashes.json').items():
        assert digest(ROOT/path)==sha, f'Input changed: {path}'
    audit=read(root/'input_audit.json')
    assert all(r['native_formula_same_order_rate']==1 for r in audit if r['split'] in ['valid','test'])
    cm=csv_rows(root/'candidate_metrics.csv')
    assert len(cm)==cpu_done['candidate_metric_rows']
    for name in cp['datasets']:
        for split in ['valid','test']:
            rs=[r for r in cm if r['dataset']==name and r['split']==split]
            assert len({r['gold_at20'] for r in rs})==1, f'Candidate recall changed: {name}/{split}'
        for variant in gp['candidate_variants']:
            orders=read(root/'orders'/name/variant/'test.json')
            assert len(orders)==len(load_rows(name,'test'))
            assert all(sorted(o)==list(range(20)) for o in orders)
    search=read(gpu/'edge_validation_search.json');selection=read(gpu/'frozen_edge_selection.json')
    for name in gp['datasets']:
        rs=search[name]
        assert len(rs)==len(gp['edge_trials'])
        best=max(rs,key=lambda r:(r['exact_match'],r['adjusted_rr'],-r['trial']))
        assert selection[name]['auto_trial']==best['trial']
        sources=selection[name].get('source_datasets',[])
        assert name not in sources
        if sources:
            assert set(sources)==set(gp['datasets'])-{name}
            best_j=max(range(len(rs)),key=lambda j:(
                sum(search[d][j]['exact_match'] for d in sources)/len(sources),
                sum(search[d][j]['adjusted_rr'] for d in sources)/len(sources),-j))
            assert selection[name]['lodo_trial']==best_j
    metrics=csv_rows(gpu/'e2e_metrics.csv')
    expected=len(gp['datasets'])*(len(gp['candidate_variants'])+4+(len(gp['datasets'])>1))
    assert len(metrics)==expected==gpu_done['metric_rows']
    keys={(r['dataset'],r['arm'],r['variant']) for r in metrics}
    assert len(keys)==expected
    for row in metrics:
        name,arm,variant=[row[k] for k in ['dataset','arm','variant']]
        preds=read(gpu/'predictions'/name/(arm+'_'+variant)/'test.json')
        raw=load_rows(name,'test')
        assert len(preds)==int(row['n'])==len(raw)
        assert [(p['query_id'],p['gold_id']) for p in preds]==[(r['query_entity_id'],r['gold_entity_id']) for r in raw]
        for metric in ['exact_match','invalid','top1_copy','adjusted_rr','candidate_rr','gold_present']:
            actual=sum(p[metric] for p in preds)/len(preds)
            assert math.isclose(actual,float(row[metric]),abs_tol=1e-12), f'{name}/{variant}/{metric}'
        assert all(p['adjusted_rr']==0 for p in preds if not p['gold_present'])
    manifest=read(root/'exports/export_manifest.json')
    assert manifest['cpu_status']=='complete' and manifest['e2e_status']=='complete'
    assert Path(manifest['e2e_directory'])==gpu
    with zipfile.ZipFile(root/'exports/comment2_results.xlsx') as z:
        assert z.testzip() is None
        for path in z.namelist():
            if path.endswith(('.xml','.rels')):ET.fromstring(z.read(path))
    for path in (root/'exports').glob('*.svg'):ET.parse(path)
    print(f'PASS: frozen code/input hashes; native replay; candidate recall/orders; validation selections; {expected} complete E2E rows; prediction-derived metrics; XLSX/SVG structure.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',default=str(OUT));p.add_argument('--e2e-results',default=None)
    run(p.parse_args())
