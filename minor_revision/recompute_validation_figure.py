#!/usr/bin/env python3
"""Align existing PrimeKG validation diagnostics with the paper's absent-gold rule."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];out=R/'minor_revision/revision_notes'
paths={'raw':'dataset/setting_a/23_noinj_source/valid_top20_raw.json','ontology':'dataset/setting_a/24_noinj_ontology/valid_top20_ontology_raw.json','bcap':'dataset/setting_a/26_n2_soft_support/valid_top20_soft_support_bcap.json','soft':'dataset/setting_a/26_n2_soft_support/valid_top20_soft_support_b050.json','probe':'dataset/setting_a/28_n2_fuzzy_encoder/valid_fuzzy_encoder_probe_v0.json'}
res={}
for key,path in paths.items():
 p=R/path;rows=json.loads(p.read_text());ranks=[]
 for row in rows:
  ids=row['candidate_entity_ids_probe_ordered' if key=='probe' else 'candidate_entity_ids'];gold=row['gold_entity_id'];ranks.append(ids.index(gold)+1 if gold in ids else 21)
 res[key]={'source':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'n':len(rows),'gold':sum(r<=20 for r in ranks)/len(rows),'mrr':sum(1/r if r<=20 else 0 for r in ranks)/len(rows),**{f'hits{k}':sum(r<=k for r in ranks)/len(rows) for k in [1,3,10]}}
(out/'validation_metric_check.json').write_text(json.dumps(res,indent=2)+'\n')
# Regenerate Fig. 2 from audited metrics, with legends below the plotting areas.
source=R/'minor_revision/Main Manuscript/paper'
text=r'''\documentclass[tikz,border=3pt]{standalone}
\usepackage{pgfplots}
\usepgfplotslibrary{groupplots}
\pgfplotsset{compat=1.18}
\begin{document}
\begin{tikzpicture}
\begin{groupplot}[group style={group size=2 by 1,horizontal sep=1.4cm},width=8cm,height=6cm,xmin=-.15,xmax=3.15,xtick={0,1,2,3},xticklabels={Backbone,Ontology,{bcap\\contrast},{Soft support\\b050}},xticklabel style={align=center,font=\small},ylabel={Score},ymin=0,grid=major,grid style={gray!20},legend style={at={(0.5,-0.32)},anchor=north,font=\small,draw=none,fill=none,cells={anchor=west},column sep=6pt},tick label style={font=\small},title style={font=\bfseries\small}]
\nextgroupplot[title={(a) Candidate-ranking metrics},ymax=.205,legend columns=2]
'''
for field,legend,color,mark in [('mrr','MRR@20','blue','*'),('hits1','Hits@1','orange','square*'),('hits3','Hits@3','green!50!black','triangle*'),('hits10','Hits@10','red','diamond*')]:
 coords=' '.join(f'({i},{res[k][field]:.8f})' for i,k in enumerate(['raw','ontology','bcap','soft']))
 text+='\\addplot[color='+color+',mark='+mark+',thick] coordinates {'+coords+'};\n\\addlegendentry{'+legend+'}\n'
text+=r'''\nextgroupplot[title={(b) Shortcut exposure},ylabel={Rate},ymax=.6,legend columns=1]
\addplot[color=blue,mark=*,thick] coordinates {(0,.2408) (1,.5296) (2,.2452) (3,.0072)};
\addlegendentry{Top-5 direct-link rate}
\end{groupplot}
\end{tikzpicture}
\end{document}
'''
(source/'Fig2_revised.tex').write_text(text)
print(json.dumps({k:{m:round(v,6) for m,v in row.items() if m in ['mrr','gold']} for k,row in res.items()},indent=2))
