"""Export auditable C3 tables, genuine XLSX, HTML, LaTeX and PGFPlots PDFs."""
import argparse
import csv
import gzip
import html
import importlib.util
import json
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
import numpy as np
from c3lib import OUT,ROOT,HERE,read,write,csv_write,PRIMARY_METRICS

spec=importlib.util.spec_from_file_location('c2_export_util',HERE.parent/'revision_c2/export_results.py')
util=importlib.util.module_from_spec(spec);spec.loader.exec_module(util)
load_csv,markdown,latex,excel=util.load_csv,util.markdown,util.latex,util.excel


def paper_latex(rows,columns,decimals):
    lines=[r'\begin{tabular}{l'+'r'*(len(columns)-1)+'}',r'\hline',
        ' & '.join(util.tex_escape(c) for c in columns)+r' \\',r'\hline']
    for row in rows:
        values=[f'{row[c]:.{decimals}f}' if isinstance(row[c],(int,float)) else str(row[c]) for c in columns]
        lines.append(' & '.join(util.tex_escape(v) for v in values)+r' \\')
    return '\n'.join(lines+[r'\hline',r'\end{tabular}'])


def workbook(path,tables):
    """Add frozen headers, readable widths, filters and header styling to OOXML."""
    excel(path,tables)
    with zipfile.ZipFile(path) as z:parts={name:z.read(name) for name in z.namelist()}
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    def el(tag,attributes=None):return ET.Element('{'+ns+'}'+tag,attributes or {})
    for name,data in list(parts.items()):
        if not name.startswith('xl/worksheets/'):continue
        root=ET.fromstring(data);sheet=root.find('{'+ns+'}sheetData');rows=sheet.findall('{'+ns+'}row')
        header=rows[0];header.set('ht','42');header.set('customHeight','1')
        cols=el('cols')
        for i,cell in enumerate(header,1):
            cell.set('s','1');text=''.join(cell.itertext())
            cols.append(el('col',dict(min=str(i),max=str(i),width=str(min(36,max(15,len(text)*.8))),customWidth='1')))
        views=el('sheetViews');view=el('sheetView',{'workbookViewId':'0'})
        view.append(el('pane',{'ySplit':'1','topLeftCell':'A2','activePane':'bottomLeft','state':'frozen'}));views.append(view)
        root.insert(0,views);root.insert(1,cols)
        last=header[-1].get('r').rstrip('0123456789')
        root.append(el('autoFilter',{'ref':f'A1:{last}{len(rows)}'}))
        parts[name]=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    parts['xl/styles.xml']=(f'<styleSheet xmlns="{ns}">'
        '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
        '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF214E72"/><bgColor indexed="64"/></patternFill></fill></fills>'
        '<borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment wrapText="1" vertical="center"/></xf></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>').encode()
    rel=ET.fromstring(parts['xl/_rels/workbook.xml.rels'])
    ET.SubElement(rel,'{http://schemas.openxmlformats.org/package/2006/relationships}Relationship',{'Id':'rIdStyles','Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles','Target':'styles.xml'})
    parts['xl/_rels/workbook.xml.rels']=ET.tostring(rel,encoding='utf-8',xml_declaration=True)
    content=ET.fromstring(parts['[Content_Types].xml'])
    ET.SubElement(content,'{http://schemas.openxmlformats.org/package/2006/content-types}Override',{'PartName':'/xl/styles.xml','ContentType':'application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml'})
    parts['[Content_Types].xml']=ET.tostring(content,encoding='utf-8',xml_declaration=True)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in parts.items():z.writestr(name,data)


def grouped(rows):
    buckets=defaultdict(list)
    for r in rows:buckets[(r['dataset'],r.get('split','test'),r['method'],r['budget'])].append(r)
    out=[]
    for (dataset,split,method,budget),rs in buckets.items():
        d=dict(dataset=dataset,split=split,method=method,budget=budget,seeds=len(rs),n=rs[0]['n'])
        for k in rs[0]:
            if k in ['dataset','split','method','budget','variant','seed','n']:continue
            try:vals=[float(r[k]) for r in rs if r.get(k) not in ['',None]]
            except (TypeError,ValueError):continue
            if vals:d[k]=float(np.mean(vals));d[k+'_seed_std']=float(np.std(vals,ddof=1)) if len(vals)>1 else 0.
        out.append(d)
    return out


def load_queries(root,name,variant,gpu=False):
    if gpu:
        path=root/'predictions'/name/(variant+'.json')
        return read(path) if path.exists() else []
    path=root/'per_query'/name/'test'/(variant+'.jsonl.gz')
    if not path.exists():return []
    with gzip.open(path,'rt') as f:return [json.loads(line) for line in f]


def random_contrasts(root,datasets,seeds,gpu=False):
    """Joint query-cluster and global random-seed bootstrap, conditional on these seeds."""
    metrics=['exact_match','adjusted_rr','candidate_cosine_vs_raw'] if gpu else PRIMARY_METRICS
    out=[]
    for name in datasets:
        base=load_queries(root,name,'original_fuzzy',gpu)
        if not base:continue
        for method in ['random','random_coverage']:
            runs=[load_queries(root,name,f'{method}_s{s}',gpu) for s in range(seeds)]
            if not all(runs):continue
            keys=[(r['query_id'],r['gold_id']) for r in base]
            assert all([(r['query_id'],r['gold_id']) for r in run]==keys for run in runs)
            for metric in metrics:
                ix=[i for i,r in enumerate(base) if r.get(metric) is not None and all(run[i].get(metric) is not None for run in runs)]
                if not ix:continue
                delta=np.array([[run[i][metric]-base[i][metric] for run in runs] for i in ix])
                groups=np.array([base[i]['query_id'] for i in ix]);uq=np.unique(groups)
                sums=np.array([delta[groups==g].sum(axis=0) for g in uq]);counts=np.array([sum(groups==g) for g in uq])
                rng=np.random.default_rng(20261106);samples=[]
                for _ in range(2000):
                    qi=rng.integers(0,len(uq),len(uq));si=rng.integers(0,seeds,seeds)
                    samples.append(sums[qi][:,si].sum()/counts[qi].sum()/seeds)
                lo,hi=np.quantile(samples,[.025,.975])
                out.append(dict(dataset=name,method=method,reference='original_fuzzy',metric=metric,
                    n_eligible=len(ix),query_clusters=len(uq),seeds=seeds,delta_mean=float(delta.mean()),
                    ci95_low=float(lo),ci95_high=float(hi),bootstrap='2000 joint query-cluster and seed resamples'))
    return out


def distributions(root,datasets):
    out=[]
    for name in datasets:
        for variant in ['original_fuzzy','native_topk','native_coverage','random_s0','random_coverage_s0','ppr_terminals','shortest_paths']:
            rows=load_queries(root,name,variant)
            for metric in ['reach3_retention','path3_retention','relation_retention','candidate_coverage_retained']:
                values=[r[metric] for r in rows if r.get(metric) is not None]
                if not values:continue
                q=np.quantile(values,[.1,.5,.9])
                out.append(dict(dataset=name,variant=variant,metric=metric,n_eligible=len(values),
                    p10=float(q[0]),p50=float(q[1]),p90=float(q[2]),zero_fraction=float(np.mean(np.array(values)==0))))
    return out


def subgroup_tables(cpu,gpu,datasets):
    out=[]
    for name in datasets:
        baseline=load_queries(cpu,name,'source_raw')
        if not baseline:continue
        for variant in ['original_fuzzy','native_topk','random_s0','random_coverage_s0','ppr_terminals','shortest_paths','empty_graph']:
            topology=load_queries(cpu,name,variant);preds=load_queries(gpu,name,variant,True)
            if not topology:continue
            assert len(topology)==len(baseline)
            if preds and len(preds)!=len(baseline):preds=[]  # smoke outputs never mixed with full strata
            for label,indices in [
                ('query_present_in_source',[i for i,r in enumerate(baseline) if r['query_present']]),
                ('query_absent_from_source',[i for i,r in enumerate(baseline) if not r['query_present']]),
                ('gold_in_top20',[i for i,r in enumerate(baseline) if r['gold_in_candidates']]),
                ('gold_absent_top20',[i for i,r in enumerate(baseline) if not r['gold_in_candidates']])]:
                if not indices:continue
                r=dict(dataset=name,variant=variant,subgroup=label,n=len(indices))
                for metric in ['candidate_coverage_retained','reach3_retention','path3_retention']:
                    vals=[topology[i][metric] for i in indices if topology[i].get(metric) is not None]
                    r[metric]=float(np.mean(vals)) if vals else None;r[metric+'_eligible']=len(vals)
                for metric in ['exact_match','adjusted_rr','candidate_cosine_vs_raw']:
                    r[metric]=float(np.mean([preds[i][metric] for i in indices])) if preds else None
                out.append(r)
    return out


def plots(out,retention,audit):
    datasets=list(dict.fromkeys(r['dataset'] for r in retention))
    methods=['native_coverage','random','ppr_terminals','shortest_paths']
    colors=['blue','gray','orange','teal'];labels=['Native coverage','Random','PPR terminals','Shortest paths']
    tex_start=r'\documentclass[tikz,border=5pt]{standalone}'+'\n'+r'\usepackage{pgfplots}\usepgfplotslibrary{groupplots}\pgfplotsset{compat=1.18}'+'\n'+r'\begin{document}\begin{tikzpicture}'+'\n'
    for metric in ['reach3_retention','path3_retention']:
        tex=[tex_start,r'\begin{groupplot}[group style={group size=3 by 2,horizontal sep=1.4cm,vertical sep=1.5cm},width=5.5cm,height=4.5cm,xmin=.15,xmax=.95,ymin=0,ymax=1.05,grid=major,unbounded coords=jump,xlabel={Unique-edge budget ratio},ylabel={Retention},tick label style={font=\scriptsize},label style={font=\scriptsize},title style={font=\small},legend style={font=\tiny,at={(.02,.02)},anchor=south west}]']
        for name in datasets:
            tex.append(r'\nextgroupplot[title={'+name+'}]')
            for method,color,label in zip(methods,colors,labels):
                rows=sorted([r for r in retention if r['dataset']==name and r['split']=='test' and r['method']==method and r['budget']!='native'],key=lambda r:float(r['budget']))
                fn=f'plot_{metric}_{name}_{method}.csv'
                csv_write(out/fn,[dict(x=r['budget'],y=r.get(metric,'nan'),error=r.get(metric+'_seed_std',0)) for r in rows])
                tex.append(r'\addplot+[color='+color+r',mark=*,mark size=1.2pt,error bars/.cd,y dir=both,y explicit] table[x=x,y=y,y error=error,col sep=comma]{'+fn+'};')
        tex.append(r'\nextgroupplot[hide axis,xmin=0,xmax=1,ymin=0,ymax=1,legend style={font=\small,at={(.5,.5)},anchor=center}]')
        for color,label in zip(colors,labels):
            tex.append(r'\addlegendimage{color='+color+r',mark=*,line width=.6pt}\addlegendentry{'+label+'}')
        tex += [r'\end{groupplot}\end{tikzpicture}\end{document}']
        (out/f'budget_{metric}.tex').write_text('\n'.join(tex))
    rows=[r for r in audit if r['split']=='test']
    csv_write(out/'plot_compression.csv',[dict(dataset=r['dataset'],retained=r['fuzzy_unique_mean'],
        removed_unique=r['source_unique_mean']-r['fuzzy_unique_mean'],duplicates=r['source_occurrences_mean']-r['source_unique_mean']) for r in rows])
    tex=[tex_start,r'\begin{axis}[ybar stacked,width=14cm,height=7cm,bar width=22pt,ymin=0,ylabel={Mean edge count per test row},symbolic x coords={'+','.join(datasets)+r'},xtick=data,legend style={at={(.5,1.04)},anchor=south,legend columns=3},grid=major]']
    for key,label in [('retained','Retained unique'),('removed_unique','Removed unique'),('duplicates','Duplicate occurrences')]:
        tex.append(r'\addplot table[x=dataset,y='+key+r',col sep=comma]{plot_compression.csv};\addlegendentry{'+label+'}')
    tex += [r'\end{axis}\end{tikzpicture}\end{document}']
    (out/'compression_decomposition.tex').write_text('\n'.join(tex))
    # PGFPlots' CSV parser does not accept the Excel-oriented UTF-8 BOM.
    for path in out.glob('plot_*.csv'):
        path.write_text(path.read_text(encoding='utf-8-sig'),encoding='utf-8')
    for stem in ['budget_reach3_retention','budget_path3_retention','compression_decomposition']:
        proc=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error',stem+'.tex'],cwd=out,capture_output=True,text=True)
        if proc.returncode:raise RuntimeError(proc.stdout[-2500:])


def run(args):
    root=Path(args.results).resolve();gpu=Path(args.gpu_results).resolve() if args.gpu_results else root/'gpu'
    out=root/'exports';out.mkdir(parents=True,exist_ok=True)
    tables={k:load_csv(root/(k+'.csv')) for k in ['retention_metrics','retention_contrasts','selection_timing']}
    for k in ['e2e_metrics','e2e_contrasts','encoder_benchmark']:tables[k]=load_csv(gpu/(k+'.csv'))
    tables['native_budget_metrics']=load_csv(root/'native_budget_audit/native_budget_metrics.csv')
    cpu_status=read(root/'cpu_complete.json')['status'] if (root/'cpu_complete.json').exists() else 'not_complete'
    gpu_status=read(gpu/'gpu_complete.json')['status'] if (gpu/'gpu_complete.json').exists() else 'not_complete'
    cp=read(root/'protocol_cpu.json');datasets=cp['datasets'];audit=read(root/'input_audit.json')
    tables['seed_retention_summary']=grouped(tables['retention_metrics']);tables['seed_e2e_summary']=grouped(tables['e2e_metrics'])
    tables['random_retention_contrasts']=random_contrasts(root,datasets,cp['random_seeds'])
    tables['random_e2e_contrasts']=random_contrasts(gpu,datasets,cp['random_seeds'],True)
    tables['retention_distribution']=distributions(root,datasets)
    tables['metric_eligibility']=[dict(dataset=r['dataset'],split=r['split'],variant=r['variant'],metric=m,
        n=int(r['n']),n_eligible=int(float(r.get(m+'_eligible') or 0)))
        for r in tables['retention_metrics'] for m in dict.fromkeys(PRIMARY_METRICS+['path2_retention','gene_path_retention'])]
    tables['subgroup_analysis']=subgroup_tables(root,gpu,datasets)
    tables['input_audit']=audit
    precision_path=root/'precision_audit.json'
    tables['precision_audit']=[]
    if precision_path.exists():
        for r in read(precision_path):
            for dtype,values in r['results'].items():
                tables['precision_audit'].append(dict(dataset=r['dataset'],dtype=dtype,test_rows=r['test_rows'],
                    encoder_cases=r['test_rows']*len(r['variants']),nonfinite_cases=values['nonfinite_cases'],max_abs_finite_output=values['max_abs_finite_output']))
    for name in ['seed_retention_summary','seed_e2e_summary','random_retention_contrasts','random_e2e_contrasts','retention_distribution','metric_eligibility','subgroup_analysis','precision_audit']:
        if tables[name]:csv_write(out/(name+'.csv'),tables[name])
    keep=['original_fuzzy','native_topk','random','random_coverage','ppr_terminals','shortest_paths','relation_diverse']
    main=[r for r in tables['seed_retention_summary'] if r['split']=='test' and r['budget']=='native' and r['method'] in keep]
    rc=['dataset','method','candidate_coverage_retained','reach3_retention','path3_retention','relation_retention','relation_jsd']
    e2e=[r for r in tables['seed_e2e_summary'] if r['budget']=='native' and r['method'] in keep+['source_raw','source_unique','empty_graph']]
    ec=['dataset','method','exact_match','adjusted_rr','prediction_agreement_raw','candidate_cosine_vs_raw']
    csv_write(out/'table_retention_main.csv',main);(out/'table_retention_main.tex').write_text(latex(main,rc))
    if e2e:csv_write(out/'table_e2e_main.csv',e2e);(out/'table_e2e_main.tex').write_text(latex(e2e,ec))
    if gpu_status=='complete':
        lookup={(r['dataset'],r['method']):r for r in tables['seed_e2e_summary'] if r['budget']=='native'}
        compact=[];encoder=[]
        methods=[('source_raw','Source raw'),('source_unique','Source unique'),('original_fuzzy','Original fuzzy'),
            ('empty_graph','Empty local graph'),('native_topk','Native score top-k'),('native_coverage','Native coverage'),
            ('degree_topk','Degree top-k'),('query_bfs','Query BFS'),('ppr_query','PPR query'),('ppr_terminals','PPR terminals'),
            ('shortest_paths','Shortest paths'),('relation_diverse','Relation stratified'),
            ('random','Random (5 seeds)'),('random_coverage','Random + coverage (5 seeds)')]
        for method,label in methods:
            compact.append(dict(Method=label,**{name:100*float(lookup[(name,method)]['exact_match']) for name in datasets}))
        for name in datasets:
            r=lookup[(name,'original_fuzzy')]
            encoder.append(dict(Dataset=name,**{'Query cosine':r['query_cosine_vs_raw'],'Candidate cosine':r['candidate_cosine_vs_raw'],
                'Query rel. L2':r['query_rel_l2_vs_raw'],'Candidate rel. L2':r['candidate_rel_l2_vs_raw'],'Answer agreement (%)':100*r['prediction_agreement_raw']}))
        (out/'table_accuracy_compact.tex').write_text(paper_latex(compact,['Method']+datasets,2))
        (out/'table_encoder_compact.tex').write_text(paper_latex(encoder,['Dataset','Query cosine','Candidate cosine','Query rel. L2','Candidate rel. L2','Answer agreement (%)'],4))
    else:
        for stem in ['table_accuracy_compact','table_encoder_compact']:
            (out/(stem+'.tex')).write_text(r'\textit{GPU evaluation is not complete; no final table is available.}')
    tables['run_status']=[dict(stage='CPU',status=cpu_status),dict(stage='GPU',status=gpu_status)]
    workbook(out/'comment3_results.xlsx',tables)
    notes=['# Comment 3 — information retention and subgraph selection',
        f'CPU: **{cpu_status}**. GPU: **{gpu_status}**.',
        'All matched-budget selectors receive the same candidate order and unique edge budget per query. Source/raw, source/unique and empty-graph are diagnostic references, not matched-budget competitors.',
        'Coverage means candidate-node incidence. Reachability counts candidates connected to the query within three edges. Path retention counts exact edge-labeled simple paths of length three. These are different quantities; none establishes biomedical mechanism retention.',
        'Paths can traverse edges in either direction; path signatures retain relation labels and traversal signs. The directed two-layer incoming-edge audit is reported separately for the actual encoder. All denominators refer to the retrieved source graph, not the entire KG.',
        'Undefined source denominators are omitted, with eligible counts exported. Do not substitute 1.0 or 0.0 for missing paths. Gold-specific metrics are post-selection diagnostics only.',
        'Random results average all declared seeds; seed standard deviations are not test confidence intervals. Joint query-cluster/seed bootstrap contrasts are exported separately; intervals are exploratory without multiplicity correction.',
        '## Duplicate removal versus unique-edge removal',markdown([r for r in audit if r['split']=='test'],['dataset','rows','source_occurrences_mean','source_unique_mean','fuzzy_unique_mean','sources_with_duplicates']),
        '## Native implementation replay and budget audit',
        'The optional native audit calls the original selection functions and checks exact edge-set replay at the original budget. At smaller budgets its actual edge count can exceed the requested count (PrimeKG coverage pass); these points are not strict-budget comparisons.',
        markdown([r for r in tables['native_budget_metrics'] if r['split']=='test' and r['dataset']=='primekg'],['dataset','budget','requested_budget','selected_unique_edges','budget_violation','reach3_retention']),
        '## Matched-budget test retention',markdown(main,rc),
        '## Frozen-model test results',markdown(e2e,ec) if e2e else 'No GPU result is available yet.',
        '## Numerical precision audit',markdown(tables['precision_audit'],['dataset','dtype','encoder_cases','nonfinite_cases','max_abs_finite_output']),
        'The final C3 run uses FP32 graph encoding and BF16 LLM inference, with finite checks before/after the cast. The FP16 graph audit found nonfinite outputs; FP32 outputs can also exceed the FP16 exponent range. No clipping or sample exclusion is used. C2/legacy FP16 cached predictions are not reused under this new fingerprint.',
        '## Interpretation limits',
        '- A graph with at most 10 edge occurrences triggers the existing global-embedding fallback. Empty graph disables local graph messages, not pretrained/global KG knowledge.',
        '- The GNN consumes directed triples. Undirected path preservation can change without changing the embeddings of the query/candidates; inspect encoder cosine and L2 as well as topology.',
        '- Identical generated answers are not evidence that discarded edges were semantically irrelevant or that methods are equivalent.',
        '- Native-score coverage and top-k controls reuse the archived native scores. The strict coverage implementation is explicitly a new control, not claimed to reproduce all native reservation passes.',
        '- Gene-intermediate paths use explicit DRKG/repoDB namespaces and unambiguous Hetionet metadata. PrimeKG/PharmKG types are not guessed; annotation eligibility is reported.',
        '- Graph-encoder timings exclude LLM generation and cannot be presented as end-to-end speedups. Graphs enter the LLM through embeddings; fewer edges do not directly reduce prompt token count.',
        '- CPU selection timings start after Context construction and archived-score loading. They exclude common adjacency/path preprocessing and may reuse per-source ordering caches; they are descriptive selection-call timings, not a total-runtime ranking of selectors.',
        '- Budgets and methods were declared before the run. No test-winning method or ratio is selected as a new default. Historical benchmark reuse makes this a retrospective analysis.']
    if gpu_status!='complete':notes.insert(2,'**GPU rows are partial or smoke-only. They are not full-run manuscript results.**')
    (out/'REPORT.md').write_text('\n\n'.join(notes)+'\n')
    parts=['<!doctype html><meta charset="utf-8"><title>Comment 3 experiments</title><style>body{font:14px system-ui;margin:32px;color:#163047}table{border-collapse:collapse;margin:20px 0}td,th{border:1px solid #ccd6df;padding:6px}th{background:#eef4f8}</style>',
        '<h1>Comment 3 experiments</h1>',f'<p>CPU: {cpu_status}; GPU: {gpu_status}. Read REPORT.md for definitions and limitations.</p>',
        '<p><a href="comment3_results.xlsx">Excel workbook</a> · <a href="budget_reach3_retention.pdf">Budget/reachability</a> · <a href="budget_path3_retention.pdf">Budget/path retention</a> · <a href="compression_decomposition.pdf">Duplicate decomposition</a></p>']
    for title,rows,cols in [('Retention',main,rc),('LLM and encoder',e2e,ec)]:
        parts.append('<h2>'+title+'</h2><table><tr>'+''.join('<th>'+c+'</th>' for c in cols)+'</tr>')
        for r in rows:parts.append('<tr>'+''.join('<td>'+html.escape(util.fmt(r.get(c)))+'</td>' for c in cols)+'</tr>')
        parts.append('</table>')
    (out/'report.html').write_text('\n'.join(parts))
    if args.plots:plots(out,tables['seed_retention_summary'],audit)
    write(out/'export_manifest.json',dict(cpu_status=cpu_status,gpu_status=gpu_status,gpu_directory=str(gpu),
        files=sorted(p.name for p in out.iterdir() if p.suffix not in ['.aux','.log'])))
    print(f'Exported {out}',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',default=str(OUT));p.add_argument('--gpu-results',default=None)
    p.add_argument('--plots',action='store_true',help='Compile publication-ready vector PDF charts with installed PGFPlots/pdflatex')
    run(p.parse_args())
