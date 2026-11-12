#!/usr/bin/env python3
"""Export paper-ready tables from complete C2/C3 results; does not run experiments."""
from pathlib import Path
import csv,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'minor_revision/Supplementary Materal/Supplementary Materal/revision_tables'
MAIN=ROOT/'minor_revision/Main Manuscript/paper/revision_tables'
OUT.mkdir(exist_ok=True);MAIN.mkdir(exist_ok=True)
D=['primekg','pharmkg','hetionet','drkg','repodb']; N=dict(zip(D,['PrimeKG','PharmKG','Hetionet','DRKG','repoDB']))
inputs={}
def read(path):
 p=ROOT/path;inputs[path]=hashlib.sha256(p.read_bytes()).hexdigest()
 return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def table(name,headers,rows,out=OUT,align=None,best_columns=None):
 # Compare only like-for-like metrics within each dataset; include displayed ties.
 if best_columns:
  for row in rows:
   values={i:float(row[i].strip('$').split(r'\pm',1)[0]) for i in best_columns}
   best=max(values.values())
   for i,value in values.items():
    if value==best:
     cell=row[i]
     row[i]=(r'$\boldsymbol{'+cell[1:-1]+'}$') if cell.startswith('$') else (r'\textbf{'+cell+'}')
 text='\\begin{tabular}{'+(align or 'l'+'r'*(len(headers)-1))+'}\n\\toprule\n'+' & '.join(headers)+r' \\'+'\n\\midrule\n'
 text+='\n'.join(' & '.join(map(str,row))+r' \\' for row in rows)+'\n\\bottomrule\n\\end{tabular}\n'
 (out/(name+'.tex')).write_text(text)
def f(v,n=5): return f'{float(v):.{n}f}' if v not in ['',None] else '--'
def pm(a,b,n=5): return '$'+f(a,n)+r'\pm'+f(b,n)+'$'
def pick(rs,**kw):
 matches=[r for r in rs if all(r[k]==str(v) for k,v in kw.items())]
 assert len(matches)==1,(kw,len(matches));return matches[0]
for path in ['results/revision_c2/cpu_complete.json','results/revision_c2/e2e_stable/e2e_complete.json','results/revision_c2/e2e_stable/precision_complete.json','results/revision_c3/gpu/gpu_complete.json']:
 p=ROOT/path;obj=json.loads(p.read_text());assert obj['status']=='complete',path
 inputs[path]=hashlib.sha256(p.read_bytes()).hexdigest()
c=read('results/revision_c2/candidate_metrics.csv'); e=read('results/revision_c2/e2e_stable/e2e_metrics.csv')
cv=lambda d,v:pick(c,dataset=d,variant=v,split='test')
ev=lambda d,v:pick(e,dataset=d,variant=v,split='test')
table('calibration_main',['Dataset','Gold@20','Original soft','Shared equal','Learned','LODO'],[[N[d],f(cv(d,'original_soft')['gold_at20'],3)]+[f(cv(d,v)['mrr_at20']) for v in ['original_soft','shared_equal','shared_learned','shared_lodo']] for d in D],MAIN,best_columns=(2,3,4,5))
table('native_calibration',['Dataset','Original','Fixed native','Grid selected','Unconstrained'],[[N[d]]+[f(cv(d,v)['mrr_at20']) for v in ['original_soft','native_fixed_b050','native_valid_grid','shared_learned_unconstrained']] for d in D])
w=read('results/revision_c2/learned_weights.csv'); fields=['rank_prior','source_contact','source_degree_log','shared_neighbor_log','negative_direct_contact']
table('weights',['Dataset','Fit',r'$\lambda$',r'$w_1$',r'$w_2$',r'$w_3$',r'$w_4$',r'$w_5$'],[[N[d],lab,f(pick(w,dataset=d,variant=v)['l2'],3)]+[f(pick(w,dataset=d,variant=v)[k],4) for k in fields] for d in D for v,lab in [('shared_learned','Target'),('shared_lodo','LODO')]],align='llrrrrrr')
l=read('results/revision_c2/exports/learning_vs_equal.csv')
table('learning_equal',['Dataset','Fit',r'$\Delta$MRR',r'95\% lower',r'95\% upper'],[[N[d],lab]+[f(pick(l,dataset=d,variant=v)[k],6) for k in ['delta_mrr','ci95_low','ci95_high']] for d in D for v,lab in [('shared_learned','Learned'),('shared_lodo','LODO')]],align='llrrr')
t=read('results/revision_c2/exports/transfer_matrix.csv')
table('transfer',['Source / target']+[N[d] for d in D],[[N[r['source']]]+[f(r[d]) for d in D] for r in t])
l=read('results/revision_c2/exports/label_efficiency_summary.csv')
table('label_efficiency',['Dataset',r'10\%',r'25\%',r'50\%',r'100\%'],[[N[d]]+[pm(pick(l,dataset=d,fraction=x)['mrr_at20_mean'],pick(l,dataset=d,fraction=x)['mrr_at20_std'],4) for x in ['0.1','0.25','0.5','1.0']] for d in D])
table('ablation',['Dataset','Full','No rank','No contact','No degree','No shared','No direct'],[[N[d],f(cv(d,'shared_learned')['mrr_at20'])]+[f(cv(d,'ablate_'+k)['mrr_at20']) for k in fields] for d in D])
s=read('results/revision_c2/exports/sensitivity_summary.csv')
table('sensitivity',['Dataset','Family',r'MRR ($\sigma=0.1$)',r'MRR ($\sigma=0.5$)',r'Top1 same ($\sigma=0.5$)'],[[N[d],lab]+[pm(pick(s,dataset=d,family=family,sigma=x)['mrr_at20_mean'],pick(s,dataset=d,family=family,sigma=x)['mrr_at20_std'],4) for x in ['0.1','0.5']]+[f(pick(s,dataset=d,family=family,sigma='0.5')['same_top1_mean'],3)] for d in D for family,lab in [('native_selected','Original'),('shared_learned','Learned')]],align='llrrr')
# S23 combines exact accuracy and adjusted ranking to avoid mistaking the latter for correctness.
variants=[('raw','Raw'),('original_soft','Original soft'),('native_valid_grid','Native grid'),('shared_equal','Shared equal'),('shared_learned','Shared learned'),('shared_lodo','Shared LODO')]
for metric,name,mult,n in [('exact_match','candidate_accuracy',100,2),('adjusted_rr','candidate_adjusted',1,5)]:
 table(name,['Candidate order']+[N[d] for d in D],[[label]+[f(float(ev(d,v)[metric])*mult,n) for d in D] for v,label in variants])
sel=read('results/revision_c2/exports/edge_calibration_selection.csv')
table('edge_validation',['Dataset','Auto trial','LODO trial','Best ties / 12'],[[N[d]]+[pick(sel,dataset=d)[k] for k in ['frozen_auto_trial','frozen_lodo_trial','tied_best_trials']] for d in D])
for metric,name,mult,n in [('adjusted_rr','edge_adjusted',1,6),('exact_match','edge_accuracy',100,2)]:
 table(name,['Dataset','Original fuzzy','Shared fixed','Shared auto','Edge LODO'],[[N[d]]+[f(float(ev(d,v)[metric])*mult,n) for v in ['original_fuzzy','shared_fixed','shared_auto','shared_edge_lodo']] for d in D])
r=read('results/revision_c3/exports/seed_retention_summary.csv')
g=read('results/revision_c3/exports/seed_e2e_summary.csv')
rv=lambda d,m:pick(r,dataset=d,method=m,budget='native',split='test')
gv=lambda d,m:pick(g,dataset=d,method=m,budget='native',split='test')
methods=[('original_fuzzy','Original fuzzy'),('native_topk','Native score top-$k$'),('native_coverage','Strict native coverage'),('degree_topk','Degree top-$k$'),('query_bfs','Query BFS'),('ppr_query','Query PPR'),('ppr_terminals','Terminal PPR'),('shortest_paths','Shortest paths'),('relation_diverse','Relation stratified'),('random','Random (5 seeds)'),('random_coverage','Random + coverage (5 seeds)')]
# Actual method identifiers must match exports, fail loudly if upstream format changes.
print('C3 method identifiers:',sorted({x['method'] for x in r}))
table('retention_main',['Dataset','$N$','Fuzzy','Random','Shortest paths','Shortest coverage'],[[N[d],str(int(float(rv(d,'original_fuzzy')['reach3_retention_eligible']))),f(rv(d,'original_fuzzy')['reach3_retention'],4),pm(rv(d,'random')['reach3_retention'],rv(d,'random')['reach3_retention_seed_std'],4),f(rv(d,'shortest_paths')['reach3_retention'],4),f(rv(d,'shortest_paths')['candidate_coverage_retained'],4)] for d in D],MAIN,best_columns=(2,3,4))
table('all_reachability',['Selector']+[N[d] for d in D],[[label]+[f(rv(d,m)['reach3_retention'],4) for d in D] for m,label in methods])
table('path_retention',['Dataset','$N$','Fuzzy','Random (5 seeds)','Shortest paths'],[[N[d],str(int(float(rv(d,'original_fuzzy')['path3_retention_eligible']))),f(rv(d,'original_fuzzy')['path3_retention'],4),pm(rv(d,'random')['path3_retention'],rv(d,'random')['path3_retention_seed_std'],4),f(rv(d,'shortest_paths')['path3_retention'],4)] for d in D])
table('other_retention',['Dataset','Nodes','Relation types','Relation JSD','Incoming-2','Rare edges'],[[N[d]]+[f(rv(d,'original_fuzzy')[k],4) for k in ['node_retention','relation_retention','relation_jsd','incoming2_retention','rare_relation_edge_retention']] for d in D])
refs=[('source_raw','Source multiset'),('source_unique','Source unique'),('empty_graph','Empty local graph')]
table('selector_accuracy',['Selector']+[N[d] for d in D],[[label]+[f(float(gv(d,m)['exact_match'])*100,2) for d in D] for m,label in refs+methods])
table('encoder',['Dataset','Query cosine','Candidate cosine','Query rel. L2','Candidate rel. L2',r'Agreement (\%)'],[[N[d]]+[f(gv(d,'original_fuzzy')[k],4) for k in ['query_cosine_vs_raw','candidate_cosine_vs_raw','query_rel_l2_vs_raw','candidate_rel_l2_vs_raw']]+[f(float(gv(d,'original_fuzzy')['prediction_agreement_raw'])*100,1)] for d in D])
(ROOT/'minor_revision/revision_notes/table_sources.json').write_text(json.dumps({'inputs_sha256':inputs,'tables':[str(p.relative_to(ROOT)) for d in [OUT,MAIN] for p in sorted(d.glob('*.tex'))]},indent=2)+'\n')
print('Exported integrated revision tables.')
