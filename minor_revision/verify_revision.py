#!/usr/bin/env python3
"""Check delivered document hashes, labels, citations, and result provenance."""
from pathlib import Path
import json,hashlib,re,csv,subprocess
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'minor_revision';checks=[]
for item in json.loads((BASE/'revision_notes/build_manifest.json').read_text()):
 p=BASE/item['pdf'];assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'];assert not item['checks']
 checks.append(f"PASS PDF hash and clean layout/reference checks: {p.name}")
 b=Path(item['build_directory']);name='sn-article' if item['pdf'].startswith('Manuscript') else 'ESM_1'
 aux=(b/(name+'.aux')).read_text()
 if name=='sn-article':
  for key,number in [('tab:module_results','3'),('tab:calibration_main','4'),('tab:retention_main','5')]:assert r'\newlabel{'+key+'}{{'+number+'}' in aux,key
  text=(b/'sn-article.bbl').read_text();assert text.count(r'\begin{revisionblock}')==6
  page4=re.search(r'\\newlabel\{tab:calibration_main\}\{\{4\}\{(\d+)\}',aux).group(1)
  page5=re.search(r'\\newlabel\{tab:retention_main\}\{\{5\}\{(\d+)\}',aux).group(1)
  assert page4==page5, 'Tables 4 and 5 must share a page'
  source=(BASE/'Main Manuscript/paper/sn-article.tex').read_text()
  assert r'\url{https://github.com/dhduong710/SoftFuse-KGC}' in source
  assert 'Project_1' not in source
  related=source.split(r'\section{Related Work}',1)[1].split(r'\section{Methods}',1)[0]
  assert r'\softfuse' not in related and 'SoftFuse-KGC' not in related
  for key in ['zhu2026spatialspectral','zhu2026fdmsgl']:
   assert key in related and key in source.split(r'\section{Discussion}',1)[1]
  results=(BASE/'Main Manuscript/paper/revision_results.tex').read_text()
  gap=results.split(r'\input{revision_tables/calibration_main}',1)[1].split(r'\captionof{table}',1)[0]
  assert not re.search('[A-Za-z]{3}', re.sub(r'\\[A-Za-z]+|[{}]|linewidth|par|medskip|minipage|centering|small', '',gap)), 'Prose between Tables 4 and 5'
 else:
  assert r'\newlabel{sec:repodb_alignment}{{S11.1}' in aux
  for i in range(16,30):assert re.search(r'\\newlabel\{tab:s'+str(i)+r'[^}]*\}\{\{S'+str(i)+r'\}',aux),i
  for n in ['S12','S13','S4','S5','S6']:assert '{{'+n+'}' in aux,n
 text=subprocess.check_output(['gs','-q','-dSAFER','-dBATCH','-dNOPAUSE','-sDEVICE=txtwrite','-sOutputFile=-',str(p)],text=True)
 assert not re.search(r'FP16|FP32|BF16|nonfinite|\?\?',text),p
checks.append('PASS Tables 4 and 5 are adjacent on the same page; Code availability uses SoftFuse-KGC')
checks.append('PASS Related Work omits SoftFuse-KGC; both requested references appear in Related Work and Discussion; S11.1 alignment section resolves')
checks.append('PASS main Tables 3/4/5; supplementary S12/S13, Tables S16–S29 and Figs. S4–S6; six new bibliography entries highlighted')
for source,h in json.loads((BASE/'revision_notes/table_sources.json').read_text())['inputs_sha256'].items():assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==h,source
checks.append('PASS current result input hashes for all exported tables')
alignment=json.loads((BASE/'revision_notes/comment5_alignment_audit.json').read_text())
for source,h in alignment['inputs_sha256'].items():assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==h,source
assert alignment['graph']['num_kept_edges']==90804 and alignment['heldout_exact_target_edges_in_graph']==0
checks.append('PASS repoDB audit input hashes: normalization, exact-ID mapping, coverage-safe split and all 90,804 graph edges reproduced')
s=(BASE/'Main Manuscript/paper/sn-article.tex').read_text()
rows=list(csv.DictReader((ROOT/'results/revision_c2/e2e_stable/e2e_metrics.csv').open(encoding='utf-8-sig')))
for v in ['raw','original_soft','original_fuzzy']:
 expected=[f"{float(next(x['adjusted_rr'] for x in rows if x['dataset']==d and x['variant']==v)):.4f}" for d in ['primekg','pharmkg','hetionet','drkg','repodb']]
 lines=[line for line in s.splitlines() if line.startswith('& E2E MRR@20')]
 actual=lines[['raw','original_soft','original_fuzzy'].index(v)]
 assert re.findall(r'(?<!\d)\d\.\d{4}(?!\d)',actual)==expected,(v,actual,expected)
checks.append('PASS manuscript module E2E table agrees with all 15 current stable metrics')
for item in json.loads((BASE/'revision_notes/validation_metric_check.json').read_text()).values():
 assert item['mrr']<=item['gold'];assert hashlib.sha256((ROOT/item['source']).read_bytes()).hexdigest()==item['sha256']
checks.append('PASS validation metric inputs and absent-gold bounds')
checks.append('PASS PDF text contains no unresolved-reference placeholders or precision-debug narrative')
(BASE/'revision_notes/verification.txt').write_text('\n'.join(checks)+'\n');print('\n'.join(checks))
