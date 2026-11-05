"""Read-only validation of completed C3 sources, predictions and exports."""
import argparse
import csv
import gzip
import json
import math
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from c3lib import *


def table(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def run(args):
    root=Path(args.results).resolve();gpu=Path(args.gpu_results).resolve() if args.gpu_results else root/'gpu'
    cp=read(root/'protocol_cpu.json');gp=read(gpu/'protocol_gpu.json')
    cd=read(root/'cpu_complete.json');gd=read(gpu/'gpu_complete.json')
    assert cd['status']==gd['status']=='complete' and gd['all_test_rows']
    for path,sha in read(root/'input_hashes.json').items():assert digest(ROOT/path)==sha,f'Input changed: {path}'
    for name,sha in cp['code_sha256'].items():
        path=HERE/name if name in ['c3lib.py','run_cpu.py'] else HERE.parent/'revision_c2'/name
        assert digest(path)==sha,f'CPU dependency changed: {path}'
    assert digest(HERE/'run_gpu.py')==gp['runner_sha256']
    assert digest(HERE/'c3lib.py')==gp['common_sha256']
    assert digest(root/'protocol_cpu.json')==gp['cpu_protocol_sha256']
    assert digest(root/'input_hashes.json')==gp['cpu_inputs_sha256']
    cpu=table(root/'retention_metrics.csv')
    assert len(cpu)==cd['metric_rows']==len(cp['datasets'])*len(cp['splits'])*len(cp['variants'])
    keys={(r['dataset'],r['split'],r['variant']) for r in cpu};assert len(keys)==len(cpu)
    native=root/'native_budget_audit'
    if (native/'complete.json').exists():
        nd=read(native/'complete.json');np_=read(native/'protocol.json')
        assert nd['status']=='complete' and nd['replay_exact']
        assert digest(HERE/'audit_native_budgets.py')==np_['runner_sha256']
        assert digest(root/'protocol_cpu.json')==np_['cpu_protocol_sha256']
        from audit_native_budgets import SCRIPTS
        for name,sha in np_['script_sha256'].items():assert digest(ROOT/SCRIPTS[name])==sha
        assert all(r['native_edge_set_replay_rate']==1 for r in read(native/'replay_audit.json'))
        assert len(table(native/'native_budget_metrics.csv'))==nd['metric_rows']
    plan={v['key']:v for v in cp['variants']};n_cpu_rows=0
    for name in cp['datasets']:
        for split in cp['splits']:
            raw=load_rows(name,split);fuzzy=align(raw,load_rows(name,split,'fuzzy'))
            for variant,v in plan.items():
                path=root/'per_query'/name/split/(variant+'.jsonl.gz')
                with gzip.open(path,'rt') as f:rows=[json.loads(line) for line in f]
                assert len(rows)==len(raw)
                for row,r,f in zip(rows,raw,fuzzy):
                    assert (row['query_id'],row['gold_id'])==(r['query_entity_id'],r['gold_entity_id'])
                    unique=len({tuple(e) for e in r['subgraph']})
                    assert row['source_unique_edges']==unique
                    assert row['source_edge_occurrences']==len(r['subgraph'])
                    if v['method'] not in ['source_raw','source_unique','original_fuzzy','empty_graph']:
                        budget=len(f['subgraph']) if v['budget']=='native' else round(unique*v['budget'])
                        assert row['selected_unique_edges']==budget
                    assert row['selected_unique_edges']<=unique
                    for m in PRIMARY_METRICS:
                        if row.get(m) is not None:assert -1e-12<=row[m]<=1+1e-12
                n_cpu_rows+=len(rows)
    metrics=table(gpu/'e2e_metrics.csv');expected=len(gp['datasets'])*len(gp['variants'])
    assert len(metrics)==gd['metric_rows']==expected
    assert len({(r['dataset'],r['variant']) for r in metrics})==expected
    raw_lookup={n:load_rows(n,'test') for n in gp['datasets']}
    fuzzy_lookup={n:align(raw_lookup[n],load_rows(n,'test','fuzzy')) for n in gp['datasets']}
    for summary in metrics:
        name,variant=summary['dataset'],summary['variant']
        preds=read(gpu/'predictions'/name/(variant+'.json'));source=read(gpu/'predictions'/name/'source_raw.json')
        assert len(preds)==int(summary['n'])==len(raw_lookup[name])
        for pred,r,f,base in zip(preds,raw_lookup[name],fuzzy_lookup[name],source):
            row=reorder_row(r,[r['rank_entities_id'].index(c) for c in f['rank_entities_id']])
            assert (pred['query_id'],pred['gold_id'])==(row['query_entity_id'],row['gold_entity_id'])
            score=score_prediction(row,pred['prediction'])
            for k,value in score.items():assert math.isclose(pred[k],value,abs_tol=1e-12)
            assert pred['prediction_agreement_raw']==int(normalize(pred['prediction'])==normalize(base['prediction']))
            for k,value in pred.items():
                if 'cosine' in k and value is not None:assert math.isfinite(value) and -1.000001<=value<=1.000001
                if 'rel_l2' in k:assert math.isfinite(value) and value>=0
        aggregate_pred=aggregate(preds)
        for k,value in aggregate_pred.items():assert math.isclose(float(summary[k]),value,abs_tol=1e-12),f'{name}/{variant}/{k}'
    manifest=read(root/'exports/export_manifest.json')
    assert manifest['cpu_status']==manifest['gpu_status']=='complete'
    assert Path(manifest['gpu_directory'])==gpu
    with zipfile.ZipFile(root/'exports/comment3_results.xlsx') as z:
        assert z.testzip() is None
        for p in z.namelist():
            if p.endswith(('.xml','.rels')):ET.fromstring(z.read(p))
    print(f'PASS: frozen code/inputs; {len(cpu)} CPU summaries and {n_cpu_rows} row/variant records; strict budgets; {expected} full GPU summaries; predictions/rescoring/aggregates; finite representation metrics; XLSX.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',default=str(OUT));p.add_argument('--gpu-results',default=None)
    run(p.parse_args())
