"""Export all available tables to Markdown/LaTeX/HTML/CSV and an Excel workbook.

Uses the standard library and numpy. Incomplete or smoke E2E runs are labelled explicitly.
No values are filled in for missing runs; report generation never performs selection.
"""
import argparse
import csv
import html
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape
from collections import defaultdict

import numpy as np

from common import OUT,read,write,csv_write,cluster_bootstrap


def load_csv(path):
    if not path.exists():return []
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def fmt(value):
    if value is None or value=='':return '—'
    try:
        n=float(value)
        return f'{n:.6f}' if not n.is_integer() else str(int(n))
    except (ValueError,TypeError):return str(value)


def markdown(rows,columns):
    return '\n'.join(['| '+' | '.join(columns)+' |','|'+'|'.join(['---']*len(columns))+'|']+
        ['| '+' | '.join(fmt(r.get(c)).replace('|','/') for c in columns)+' |' for r in rows])


def tex_escape(s):
    return ''.join({'_':r'\_','%':r'\%','&':r'\&','#':r'\#','{':r'\{','}':r'\}'}.get(c,c) for c in str(s))


def latex(rows,columns):
    return '\n'.join([r'\begin{tabular}{'+'l'*len(columns)+'}',r'\hline',
        ' & '.join(map(tex_escape,columns))+r' \\',r'\hline']+
        [' & '.join(tex_escape(fmt(r.get(c))) for c in columns)+r' \\' for r in rows]+[r'\hline',r'\end{tabular}'])


def excel(path,tables):
    """Small standards-compliant XLSX with inline strings; no openpyxl needed."""
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    def column(n):
        out=''
        while n:
            n,r=divmod(n-1,26);out=chr(65+r)+out
        return out
    content=['<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>']
    sheets=[];rels=[]
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for index,(name,rows) in enumerate(tables.items(),1):
            columns=list(dict.fromkeys(k for r in rows for k in r)) if rows else ['status']
            values=[columns]+[[r.get(c,'') for c in columns] for r in rows]
            xml=[]
            for ri,vals in enumerate(values,1):
                cells=[]
                for ci,value in enumerate(vals,1):
                    address=f'{column(ci)}{ri}'
                    s=str(value)
                    try:
                        float(s)
                        cells.append(f'<c r="{address}"><v>{s}</v></c>')
                    except ValueError:
                        cells.append(f'<c r="{address}" t="inlineStr"><is><t xml:space="preserve">{escape(s)}</t></is></c>')
                xml.append(f'<row r="{ri}">'+''.join(cells)+'</row>')
            z.writestr(f'xl/worksheets/sheet{index}.xml',f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="{ns}"><sheetData>'+''.join(xml)+'</sheetData></worksheet>')
            sheets.append(f'<sheet name="{escape(name[:31])}" sheetId="{index}" r:id="rId{index}"/>')
            rels.append(f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>')
            content.append(f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+''.join(sheets)+'</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(rels)+'</Relationships>')
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'+''.join(content)+'</Types>')


def chart(path,rows):
    names=list(dict.fromkeys(r['dataset'] for r in rows))
    variants=['original_soft','shared_equal','shared_learned','shared_lodo']
    colors=['#687a90','#d69e36','#147d92','#844da5']
    lookup={(r['dataset'],r['variant']):float(r['mrr_at20']) for r in rows}
    maximum=max(lookup.values(),default=.1)*1.15
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="490" viewBox="0 0 1000 490">',
        '<rect width="1000" height="490" fill="white"/>','<g font-family="sans-serif" font-size="14" fill="#172b40">',
        '<text x="60" y="30" font-size="20">Comment 2 — candidate MRR@20 (test)</text>']
    for j in range(6):
        val=maximum*j/5;y=370-280*j/5
        svg += [f'<line x1="60" y1="{y}" x2="960" y2="{y}" stroke="#e3e8ee"/>',f'<text x="7" y="{y+4}">{val:.3f}</text>']
    for i,name in enumerate(names):
        for j,v in enumerate(variants):
            val=lookup.get((name,v),0);height=val/maximum*280;x=85+i*175+j*32
            svg.append(f'<rect x="{x}" y="{370-height}" width="26" height="{height}" fill="{colors[j]}"><title>{name} {v}: {val:.6f}</title></rect>')
        svg.append(f'<text x="{85+i*175}" y="398">{name}</text>')
    for j,v in enumerate(variants):
        svg += [f'<rect x="{65+j*230}" y="430" width="16" height="16" fill="{colors[j]}"/>',f'<text x="{88+j*230}" y="443">{v}</text>']
    svg.append('<text x="60" y="475">Descriptive results; paired query-cluster confidence intervals are in the tables.</text></g></svg>')
    path.write_text('\n'.join(svg))


def grouped_summary(rows,keys,values):
    grouped=defaultdict(list)
    for r in rows:grouped[tuple(r[k] for k in keys)].append(r)
    out=[]
    for key,items in grouped.items():
        row=dict(zip(keys,key));row['repeats']=len(items)
        for value in values:
            xs=np.array([float(r[value]) for r in items if r.get(value) not in [None,'']])
            row[value+'_mean']=float(xs.mean()) if len(xs) else None
            row[value+'_std']=float(xs.std(ddof=1)) if len(xs)>1 else 0.
        out.append(row)
    return out


def e2e_contrasts(directory,datasets):
    """Paired contrasts isolate learning/search from the feature-set change.

    The reference for every contrast is explicit. Predictions must match by
    (query ID, gold ID), rather than trusting positional alignment across files.
    These comparisons do not participate in calibration or model selection.
    """
    comparisons={
        'candidate':[(v,b) for v in ['native_valid_grid','shared_equal','shared_learned','shared_lodo']
            for b in ['original_soft']]+[(v,'shared_equal') for v in ['shared_learned','shared_lodo']],
        'graph':[(v,b) for v in ['shared_fixed','shared_auto','shared_edge_lodo']
            for b in ['original_fuzzy']]+[(v,'shared_fixed') for v in ['shared_auto','shared_edge_lodo']],
    }
    results=[]
    for name in datasets:
        for arm,pairs in comparisons.items():
            for variant,reference in pairs:
                paths=[directory/'predictions'/name/(arm+'_'+v)/'test.json' for v in [variant,reference]]
                if not all(p.exists() for p in paths):continue
                rows,base=map(read,paths)
                key=lambda r:(r['query_id'],r['gold_id'])
                lookup={key(r):r for r in base}
                if len(lookup)!=len(base) or len({key(r) for r in rows})!=len(rows) or set(lookup)!={key(r) for r in rows}:
                    raise ValueError(f'E2E contrast alignment failed: {name}/{arm}/{variant}/{reference}')
                groups=np.array([r['query_id'] for r in rows])
                for metric in ['exact_match','adjusted_rr']:
                    delta=np.array([r[metric]-lookup[key(r)][metric] for r in rows])
                    interval=cluster_bootstrap(delta,groups)
                    results.append(dict(dataset=name,arm=arm,variant=variant,reference=reference,
                        metric=metric,n=len(rows),delta_mean=interval['delta_mrr'],
                        ci95_low=interval['ci95_low'],ci95_high=interval['ci95_high'],clusters=interval['clusters']))
    return results


def curve_chart(path,rows):
    names=list(dict.fromkeys(r['dataset'] for r in rows))
    colors=['#147d92','#844da5','#d69e36','#ae3e52','#407d3b']
    maxval=max(float(r['mrr_at20_mean'])+float(r['mrr_at20_std']) for r in rows)*1.1
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="920" height="500">',
        '<rect width="920" height="500" fill="white"/><g font-family="sans-serif" font-size="14" fill="#173047">',
        '<text x="70" y="30" font-size="20">Calibration-label efficiency — test candidate MRR@20</text>']
    for j in range(6):
        v=maxval*j/5;y=385-300*j/5
        svg.extend([f'<line x1="70" y1="{y}" x2="790" y2="{y}" stroke="#dce4ea"/>',f'<text x="10" y="{y+4}">{v:.3f}</text>'])
    for fraction in [.1,.25,.5,1.]:
        x=70+720*fraction
        svg.append(f'<text x="{x-15}" y="412">{int(fraction*100)}%</text>')
    for i,name in enumerate(names):
        data=sorted([r for r in rows if r['dataset']==name],key=lambda r:float(r['fraction']))
        points=[]
        for r in data:
            x=70+720*float(r['fraction']);y=385-300*float(r['mrr_at20_mean'])/maxval
            err=300*float(r['mrr_at20_std'])/maxval
            points.append(f'{x},{y}')
            svg.extend([f'<line x1="{x}" y1="{y-err}" x2="{x}" y2="{y+err}" stroke="{colors[i%5]}"/>',
                f'<circle cx="{x}" cy="{y}" r="4" fill="{colors[i%5]}"/>'])
        svg.extend([f'<polyline points="{" ".join(points)}" fill="none" stroke="{colors[i%5]}" stroke-width="2"/>',
            f'<text x="{70+i*165}" y="450" fill="{colors[i%5]}">{name}</text>'])
    svg.append('<text x="70" y="480">Bars: standard deviation across calibration-subset seeds, not a test confidence interval.</text></g></svg>')
    path.write_text('\n'.join(svg))


def run(args):
    root=Path(args.results).resolve();e2e=Path(args.e2e_results).resolve() if args.e2e_results else root/'e2e'
    out=root/'exports';out.mkdir(parents=True,exist_ok=True)
    files=['candidate_metrics','calibration_cv','native_validation_grid','learned_weights','label_efficiency','coefficient_sensitivity','graph_weight_audit']
    tables={f:load_csv(root/(f+'.csv')) for f in files}
    tables['e2e_metrics']=load_csv(e2e/'e2e_metrics.csv')
    cpu=read(root/'cpu_complete.json') if (root/'cpu_complete.json').exists() else {'status':'not_complete'}
    gpu=read(e2e/'e2e_complete.json') if (e2e/'e2e_complete.json').exists() else {'status':'not_complete'}
    primary=[r for r in tables['candidate_metrics'] if r['split']=='test' and r['variant'] in
        ['raw','original_soft','native_fixed_b050','native_valid_grid','shared_equal','shared_learned','shared_lodo']]
    columns=['dataset','variant','gold_at20','mrr_at20','hits1','hits10','delta_mrr','ci95_low','ci95_high']
    tables['label_efficiency_summary']=grouped_summary(tables['label_efficiency'],['dataset','fraction'],['mrr_at20','hits1','hits10','calibration_rows','recoverable_calibration_rows'])
    tables['sensitivity_summary']=grouped_summary(tables['coefficient_sensitivity'],['dataset','family','sigma'],['mrr_at20','same_top1'])
    candidate_test=[r for r in tables['candidate_metrics'] if r['split']=='test']
    datasets=list(dict.fromkeys(r['dataset'] for r in candidate_test))
    lookup={(r['dataset'],r['variant']):r['mrr_at20'] for r in candidate_test}
    tables['transfer_matrix']=[dict(source=s,**{t:lookup.get((t,'shared_learned' if s==t else 'transfer_from_'+s),'') for t in datasets}) for s in datasets]
    # Explicit same-feature contrast: do not attribute feature engineering gains to learning.
    pq=load_csv(root/'candidate_per_query.csv');contrasts=[]
    for name in datasets:
        base={int(r['row']):r for r in pq if r['dataset']==name and r['variant']=='shared_equal'}
        for variant in ['shared_learned','shared_lodo']:
            rs=sorted([r for r in pq if r['dataset']==name and r['variant']==variant],key=lambda r:int(r['row']))
            if not rs:continue
            delta=np.array([float(r['rr'])-float(base[int(r['row'])]['rr']) for r in rs])
            groups=np.array([int(r['query_id']) for r in rs])
            contrasts.append(dict(dataset=name,variant=variant,reference='shared_equal',**cluster_bootstrap(delta,groups)))
    tables['learning_vs_equal']=contrasts
    tables['e2e_paired_contrasts']=e2e_contrasts(e2e,datasets)
    search_path=e2e/'edge_validation_search.json'
    if search_path.exists():
        search=read(search_path)
        tables['edge_validation_trials']=[dict(r,weights=json.dumps(r['weights'])) for rs in search.values() for r in rs]
        selection=read(e2e/'frozen_edge_selection.json') if (e2e/'frozen_edge_selection.json').exists() else {}
        tables['edge_calibration_selection']=[]
        for name,rs in search.items():
            best=max(rs,key=lambda r:(r['exact_match'],r['adjusted_rr'],-r['trial']))
            ties=sum(r['exact_match']==best['exact_match'] and r['adjusted_rr']==best['adjusted_rr'] for r in rs)
            tables['edge_calibration_selection'].append(dict(dataset=name,trials=len(rs),best_validation_exact=best['exact_match'],
                best_validation_adjusted_rr=best['adjusted_rr'],tied_best_trials=ties,
                frozen_auto_trial=selection.get(name,{}).get('auto_trial','not_frozen'),
                frozen_lodo_trial=selection.get(name,{}).get('lodo_trial','not_frozen')))
    for name in ['label_efficiency_summary','sensitivity_summary','transfer_matrix','learning_vs_equal','edge_calibration_selection','edge_validation_trials','e2e_paired_contrasts']:
        if name in tables:csv_write(out/(name+'.csv'),tables[name])
    csv_write(out/'table_candidate_main.csv',primary)
    (out/'table_candidate_main.tex').write_text(latex(primary,columns))
    chart(out/'candidate_mrr.svg',primary)
    if tables['label_efficiency_summary']:curve_chart(out/'label_efficiency.svg',tables['label_efficiency_summary'])
    tables['run_status']=[dict(stage='CPU',status=cpu['status']),dict(stage='E2E',status=gpu['status'])]
    excel(out/'comment2_results.xlsx',tables)
    notes=[
        '# Comment 2 — experiment report',
        f"CPU status: **{cpu['status']}**. E2E status: **{gpu['status']}**.",
        'Candidate MRR is not generated-answer accuracy. Native formula replay was checked against original soft-support ordering.',
        'Shared-equal vs shared-learned isolates coefficient learning on the same five topology features. Comparisons to original-soft ALSO change feature definitions.',
        'Shared-LODO excludes target validation labels. The target KG, its structural retriever, and its prepared subgraphs are still available; this is coefficient transfer, not zero-shot KG completion.',
        'All intervals are paired query-cluster bootstrap intervals vs original_soft (candidate tables); exploratory comparisons, no multiplicity adjustment. Intervals crossing zero do not establish improvement.',
        'These are retrospective checks on previously studied benchmark splits; no new prospective test set was created.',
        '## Candidate results',markdown(primary,columns),
        '## Learning effect with identical shared features',
        markdown(contrasts,['dataset','variant','reference','delta_mrr','ci95_low','ci95_high']),
        '## Transfer matrix (diagonal: within-dataset learned; off-diagonal: source-only coefficients)',
        markdown(tables['transfer_matrix'],['source']+datasets),
        '## E2E results',
    ]
    if tables['e2e_metrics']:
        ec=['dataset','arm','variant','n','exact_match','invalid','top1_copy','adjusted_rr','exact_delta','exact_ci_low','exact_ci_high']
        notes.append(markdown(tables['e2e_metrics'],ec))
        if gpu['status']!='complete':notes.append('**These E2E rows are partial or smoke-only. Do not use them as full-test manuscript results.**')
        (out/'table_e2e.tex').write_text(latex(tables['e2e_metrics'],ec))
        if tables['e2e_paired_contrasts']:
            notes.extend(['## Paired E2E comparisons (explicit references)',
                'Candidate comparisons to shared_equal isolate coefficient learning. Graph comparisons to shared_fixed isolate automatic coefficient selection within the same edge selector. Exact-match deltas are fractions, not percentage points.',
                markdown(tables['e2e_paired_contrasts'],['dataset','arm','variant','reference','metric','delta_mean','ci95_low','ci95_high'])])
    else:notes.append('Not run / no E2E results available. No GPU result is inferred from candidate metrics.')
    notes += ['## Interpretation constraints',
        '- Frozen checkpoints isolate input calibration; they do not compare separately retrained end-to-end systems.',
        '- Topology-based two-hop retention ignores relation semantics/direction and is NOT mechanistic or clinical information retention.',
        '- Native fuzzy graph sizes provide per-query budgets. Shared edge scoring has no dataset-specific relation-family weights.',
        '- Edge LODO excludes target validation scores only in the new coefficient-selection step; its inherited fuzzy candidate order and budgets retain historical dataset-specific choices.',
        '- E2E uses one consistent promote-to-front rule and exact candidate matching, including invalid outputs. Historical collectors used differing rules; do not splice their numbers into this table.',
        '- Coefficient jitter keeps zeros zero and is different from independent score noise; the original noise limitation is not negated.',
        '- Unchanged candidate metrics under graph perturbation do not establish E2E robustness.',
        '- Counts of independent query groups, calibration positives, learned weights and CV traces are exported for audit.']
    report='\n\n'.join(notes)+'\n'
    (out/'REPORT.md').write_text(report,encoding='utf-8')
    html_parts=['<!doctype html><meta charset="utf-8"><title>Comment 2 results</title><style>body{font:15px system-ui;margin:32px;color:#173047}table{border-collapse:collapse;margin:20px 0}td,th{border:1px solid #ccd6df;padding:7px;text-align:left}th{background:#edf4f7}img{max-width:100%}</style>',
        '<h1>Comment 2 — experiment results</h1>',f'<p>CPU: {cpu["status"]}; E2E: {gpu["status"]}</p>',
        '<img src="candidate_mrr.svg" alt="Candidate MRR comparison">']
    for name,rows in [('Candidate results',primary),('E2E results',tables['e2e_metrics'])]:
        if not rows:continue
        cols=columns if name.startswith('Candidate') else ['dataset','arm','variant','n','exact_match','invalid','adjusted_rr']
        html_parts += ['<h2>'+name+'</h2><table><tr>'+''.join('<th>'+c+'</th>' for c in cols)+'</tr>']
        html_parts += ['<tr>'+''.join('<td>'+html.escape(fmt(r.get(c)))+'</td>' for c in cols)+'</tr>' for r in rows]
        html_parts.append('</table>')
    html_parts.append('<p>See REPORT.md for uncertainty, protocol and interpretation limits.</p>')
    (out/'report.html').write_text('\n'.join(html_parts))
    write(out/'export_manifest.json',dict(cpu_status=cpu['status'],e2e_status=gpu['status'],e2e_directory=str(e2e),
        files=sorted(p.name for p in out.iterdir())))
    print(f'Exported {out}',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',default=str(OUT));p.add_argument('--e2e-results',default=None)
    run(p.parse_args())
