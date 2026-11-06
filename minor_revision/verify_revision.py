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
 else:
  for i in range(16,30):assert re.search(r'\\newlabel\{tab:s'+str(i)+r'[^}]*\}\{\{S'+str(i)+r'\}',aux),i
  for n in ['S12','S13','S4','S5','S6']:assert '{{'+n+'}' in aux,n
 text=subprocess.check_output(['gs','-q','-dSAFER','-dBATCH','-dNOPAUSE','-sDEVICE=txtwrite','-sOutputFile=-',str(p)],text=True)
 assert not re.search(r'FP16|FP32|BF16|nonfinite|\?\?',text),p
checks.append('PASS main Tables 3/4/5; supplementary S12/S13, Tables S16–S29 and Figs. S4–S6; six new bibliography entries highlighted')
for source,h in json.loads((BASE/'revision_notes/table_sources.json').read_text())['inputs_sha256'].items():assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==h,source
checks.append('PASS current result input hashes for all exported tables')
s=(BASE/'Main Manuscript/paper/sn-article.tex').read_text()
rows=list(csv.DictReader((ROOT/'results/revision_c2/e2e_stable/e2e_metrics.csv').open(encoding='utf-8-sig')))
for v in ['raw','original_soft','original_fuzzy']:
 expected=[f"{float(next(x['adjusted_rr'] for x in rows if x['dataset']==d and x['variant']==v)):.4f}" for d in ['primekg','pharmkg','hetionet','drkg','repodb']]
 lines=[line for line in s.splitlines() if 'revisioncell{E2E MRR' in line]
 actual=lines[['raw','original_soft','original_fuzzy'].index(v)]
 assert all(num in actual for num in expected),(v,actual,expected)
checks.append('PASS manuscript module E2E table agrees with all 15 current stable metrics')
for item in json.loads((BASE/'revision_notes/validation_metric_check.json').read_text()).values():
 assert item['mrr']<=item['gold'];assert hashlib.sha256((ROOT/item['source']).read_bytes()).hexdigest()==item['sha256']
checks.append('PASS validation metric inputs and absent-gold bounds')
checks.append('PASS PDF text contains no unresolved-reference placeholders or precision-debug narrative')
(BASE/'revision_notes/verification.txt').write_text('\n'.join(checks)+'\n');print('\n'.join(checks))
