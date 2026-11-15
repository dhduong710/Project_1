#!/usr/bin/env python3
"""Compile the bundled, approved source without regenerating results or figures."""
from pathlib import Path
import argparse, shutil, subprocess, tempfile, re
ROOT=Path(__file__).resolve().parent
MAIN='ESM_1'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--highlighted',action='store_true',help='Show yellow revision highlighting (default: clean).')
p.add_argument('--output',type=Path,help='Destination PDF; default: alongside this script.')
a=p.parse_args()
output=(a.output or ROOT/(MAIN+('_highlighted' if a.highlighted else '_clean')+'.pdf')).resolve()
with tempfile.TemporaryDirectory(prefix='submission_tex_') as tmp:
    work=Path(tmp)/'source'
    shutil.copytree(ROOT,work)
    entry=(r'\def\ShowRevisionHighlights{1}' if a.highlighted else '')+r'\input{'+MAIN+'.tex}'
    cmd=['pdflatex','-interaction=nonstopmode','-halt-on-error','-jobname='+MAIN,entry]
    for _ in range(3):
        result=subprocess.run(cmd,cwd=work,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if result.returncode:
            raise SystemExit(result.stdout[-8000:])
    log=(work/(MAIN+'.log')).read_text(errors='replace')
    problems=[line for line in log.splitlines() if re.search(r'undefined|multiply defined|Overfull \\[hv]box|Float too large|Rerun to get',line)]
    if problems: raise SystemExit('Build checks failed:\n'+'\n'.join(problems))
    output.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(work/(MAIN+'.pdf'),output)
    print(re.findall(r'Output written on.*',log)[-1])
    print(output)
