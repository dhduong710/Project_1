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
    gpu=Path(args.e2e_results).resolve() if args.e2e_results else root/'e2e_stable'
    cpu_done=read(root/'cpu_complete.json')
    gpu_done=read(gpu/'e2e_complete.json')
    assert cpu_done['status']=='complete', 'CPU is incomplete'
    assert gpu_done['status']=='complete' and gpu_done['all_test_rows'], 'GPU is incomplete or smoke-only'
    cp=read(root/'protocol_cpu.json');gp=read(gpu/'protocol_e2e.json')
    stable=(gpu/'precision_protocol.json').exists()
    if stable:
        pp=read(gpu/'precision_protocol.json');pd=read(gpu/'precision_complete.json')
        assert pd['status']=='complete' and pd['all_test_rows']
        assert pd['precision_protocol_sha256']==digest(gpu/'precision_protocol.json')
        assert pp['precision']=='graph encoder float32; LLM bfloat16' and not pp['legacy_cache_reuse']
        for path,sha in pp['dependency_sha256'].items():assert digest(ROOT/path)==sha,f'Stable dependency changed: {path}'
        snapshot=root/'legacy_fp16_snapshot/source_hashes.json'
        if snapshot.exists():
            for path,sha in read(snapshot).items():assert digest(root/path)==sha,f'Archived/CPU result changed: {path}'
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
    if stable:
        from audit_precision_c2 import variant_inputs
        from run_e2e import score_prediction,summarize
        checked=0
        for name in gp['datasets']:
            for split,arm,variant,rows in variant_inputs(root,gpu,name):
                filename=variant if arm=='edge_trial' else arm+'_'+variant
                preds=read(gpu/'predictions'/name/filename/(split+'.json'))
                assert len(preds)==len(rows)
                for r,pred in zip(rows,preds):
                    assert (r['query_entity_id'],r['gold_entity_id'])==(pred['query_id'],pred['gold_id'])
                    for key,value in score_prediction(r,pred['prediction']).items():
                        assert math.isclose(value,pred[key],abs_tol=1e-12),f'Rescoring: {name}/{variant}/{key}'
                if arm=='edge_trial':
                    trial=int(variant.rsplit('_',1)[1]);summary=summarize(preds)
                    for key,value in summary.items():assert math.isclose(value,search[name][trial][key],abs_tol=1e-12)
                checked+=len(preds)
        audit=root/'precision_audit'
        done=read(audit/'complete.json');ap=read(audit/'protocol.json')
        assert done['status']=='complete' and done['all_fp32_bf16_finite']
        assert ap['runner_sha256']==digest(Path(__file__).with_name('audit_precision_c2.py'))
        assert ap['input_hashes_sha256']==digest(root/'input_hashes.json')
        from common import DATASETS
        for name,sha in ap['checkpoint_sha256'].items():assert digest(ROOT/DATASETS[name]['checkpoint']/'graph_model.bin')==sha
        for label,directory in [('legacy_fp16',root/'e2e'),('stable',gpu)]:
            for filename,sha in ap['runs'][label].items():assert digest(directory/filename)==sha
        audit_rows=csv_rows(audit/'summary.csv')
        assert len(audit_rows)==done['summary_rows']
        assert all(int(r['fp32_nonfinite'])==int(r['fp32_to_bf16_nonfinite'])==0 for r in audit_rows)
        comparison=read(root/'precision_comparison/complete.json')
        assert comparison['status']=='complete' and comparison['audit_complete']
        assert comparison['row_variant_pairs']==checked
        assert comparison['stable_protocol_sha256']==digest(gpu/'precision_protocol.json')
        assert all(int(r['prediction_mismatches'])==0 for r in csv_rows(root/'precision_comparison/c3_anchor_checks.csv'))
        diag=gpu/'legacy_choice_diagnostic'
        dd=read(diag/'complete.json');dp=read(diag/'protocol.json')
        assert dd['status']=='complete'
        assert dp['runner_sha256']==digest(Path(__file__).with_name('evaluate_legacy_choices_stable.py'))
        assert dp['stable_precision_sha256']==digest(gpu/'precision_protocol.json')
        assert dp['old_selection_sha256']==digest(root/'e2e/frozen_edge_selection.json')
        dm=csv_rows(diag/'metrics.csv')
        assert len(dm)==dd['metric_rows']==2*len(gp['datasets'])
        for name in gp['datasets']:
            for split,arm,v,rows in variant_inputs(root,root/'e2e',name):
                if split!='test' or arm!='graph' or v not in ['shared_auto','shared_edge_lodo']:continue
                preds=read(diag/'predictions'/name/('graph_'+v)/'test.json')
                assert len(preds)==len(rows)
                for r,pred in zip(rows,preds):
                    for key,value in score_prediction(r,pred['prediction']).items():assert math.isclose(value,pred[key],abs_tol=1e-12)
                summary=next(r for r in dm if r['dataset']==name and r['variant']==v)
                for key,value in summarize(preds).items():assert math.isclose(value,float(summary[key]),abs_tol=1e-12)
        decomp=csv_rows(root/'precision_comparison/adaptive_decomposition.csv')
        assert len(decomp)==comparison['diagnostic_decomposition_rows']==len(dm)*3
        for r in decomp:assert math.isclose(float(r['total_change']),float(r['precision_at_old_choice'])+float(r['reselection_at_stable_precision']),abs_tol=1e-12)
    manifest=read(root/'exports/export_manifest.json')
    assert manifest['cpu_status']=='complete' and manifest['e2e_status']=='complete'
    assert Path(manifest['e2e_directory'])==gpu
    with zipfile.ZipFile(root/'exports/comment2_results.xlsx') as z:
        assert z.testzip() is None
        for path in z.namelist():
            if path.endswith(('.xml','.rels')):ET.fromstring(z.read(path))
    for path in (root/'exports').glob('*.svg'):ET.parse(path)
    print(f'PASS: frozen code/input hashes; native replay; candidate recall/orders; validation selections; {expected} complete E2E rows; prediction-derived metrics; XLSX/SVG structure.')
    if stable:print(f'PASS: stable precision dependencies; archived FP16 and CPU unchanged; {checked} validation/test predictions rescored; FP32/BF16 finite audit; C3 anchor agreement; {len(dm)} old-choice diagnostics and additive decomposition.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',default=str(OUT));p.add_argument('--e2e-results',default=None)
    run(p.parse_args())
