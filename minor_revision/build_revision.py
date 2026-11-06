#!/usr/bin/env python3
"""Build both highlighted PDFs in fresh temporary directories; preserve source artifacts."""
from pathlib import Path
import subprocess,tempfile,shutil,re,json,hashlib,sys
BASE=Path(__file__).resolve().parent
NEW_REFS={'zhu2026spatialspectral','zhu2026fdmsgl','dong2024connect','he2024gretriever','hu2025grag','li2025subgraphrag'}

def run(cmd,cwd):
 p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if p.returncode:
  print(p.stdout[-7000:]);raise RuntimeError(f'Build failed in {cwd}: {cmd}')
 return p.stdout

run([sys.executable,str(BASE/'export_revision_tables.py')],BASE.parent)
run([sys.executable,str(BASE/'recompute_validation_figure.py')],BASE.parent)
figure_dir=Path(tempfile.mkdtemp(prefix='softfuse_figure_'))
figure_source=BASE/'Main Manuscript/paper'
shutil.copy2(figure_source/'Fig2_revised.tex',figure_dir/'Fig2_revised.tex')
run(['pdflatex','-interaction=nonstopmode','-halt-on-error','Fig2_revised.tex'],figure_dir)
shutil.copy2(figure_dir/'Fig2_revised.pdf',figure_source/'Fig2_revised.pdf')
manifest=[]
for source,name,out in [(BASE/'Main Manuscript/paper','sn-article','Manuscript_revised_highlighted.pdf'),(BASE/'Supplementary Materal/Supplementary Materal','ESM_1','Supplementary_revised_highlighted.pdf')]:
 build=Path(tempfile.mkdtemp(prefix='softfuse_paper_'))
 for p in source.iterdir():
  if p.suffix in {'.tex','.bib','.bst','.cls','.sty','.png','.jpg','.pdf'} and p.name not in {name+'.pdf'}:shutil.copy2(p,build/p.name)
  elif p.is_dir() and p.name in {'revision_tables','revision_figures'}:shutil.copytree(p,build/p.name)
 cmd=['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex']
 run(cmd,build)
 if (build/(name+'.aux')).read_text().find('\\bibdata')>=0:
  run(['bibtex',name],build)
  p=build/(name+'.bbl');s=p.read_text()
  # Omit an unknown publisher location rather than printing the style's ??? placeholder.
  s=s.replace(r', \blocation{???}', '')
  # Highlight whole new bibliography entries while leaving pre-existing references unchanged.
  chunks=re.split(r'(?=\\bibitem)',s)
  for i,ch in enumerate(chunks):
   match=re.search(r'\\bibitem(?:\[[\s\S]*?\])?\{([^}]+)\}',ch)
   if match and match.group(1) in NEW_REFS:
    head=ch[:match.end()];body=ch[match.end():]
    tail=''
    if '\\end{thebibliography}' in body:
     body,tail=body.split('\\end{thebibliography}',1);tail='\\end{thebibliography}'+tail
    chunks[i]=head+'\n\\begin{revisionblock}\n'+body.strip()+'\n\\end{revisionblock}\n'+tail
  p.write_text(''.join(chunks))
 for _ in range(3): run(cmd,build)
 log=(build/(name+'.log')).read_text(errors='replace')
 critical=[line for line in log.splitlines() if re.search(r'undefined|multiply defined|Overfull \\[hv]box|Float too large|Rerun to get',line)]
 print(out,':',re.findall(r'Output written on.*',log)[-1],flush=True)
 print('Build directory:',build,flush=True)
 if critical: raise RuntimeError('Unresolved layout/reference checks: '+ '\n'.join(critical))
 shutil.copy2(build/(name+'.pdf'),BASE/out)
 # Canonical PDF beside edited source, as well as easy-to-find delivery PDFs.
 shutil.copy2(build/(name+'.pdf'),source/(name+'.pdf'))
 (BASE/'revision_notes'/f'{name}_build.log').write_text(log)
 manifest.append({'pdf':out,'sha256':hashlib.sha256((BASE/out).read_bytes()).hexdigest(),'build_directory':str(build),'checks':critical})
(BASE/'revision_notes/build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
