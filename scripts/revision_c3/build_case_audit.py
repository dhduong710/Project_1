"""Select explicit loss/median/retention examples; never use them to tune selectors."""
import argparse
from c3lib import *


def run(args):
    out=Path(args.results).resolve();protocol=read(out/'protocol_cpu.json')
    for path,sha in read(out/'input_hashes.json').items():assert digest(ROOT/path)==sha
    cases=[];text=['# Comment 3 — illustrative path audits',
        'Post-hoc descriptive examples: choose two lowest, one median, one highest original-fuzzy length-3 path retention per dataset, with distinct query IDs. Selection uses this declared structural criterion, not generated accuracy or biological plausibility. Ties use original row index. These are not expert-validated mechanisms.']
    for name in protocol['datasets']:
        rows,contexts=load_dataset(name,'test')
        names={int(k):v for k,v in read(ROOT/MAP_DIRS[name]/'id2entity.json').items()}
        rels={int(k):v for k,v in read(ROOT/MAP_DIRS[name]/'id2relation.json').items()}
        ranked=[]
        for i,(row,ctx) in enumerate(zip(rows,contexts)):
            m=ctx.metrics(ctx.fuzzy,row['gold_entity_id'])
            if m['path3_retention'] is not None:ranked.append((m['path3_retention'],i))
        ranked.sort();selected=[];seen=set()
        for tag,order in [('lowest',ranked),('second_lowest',ranked),('median',ranked[len(ranked)//2:]+ranked[:len(ranked)//2]),('highest',list(reversed(ranked)))]:
            for value,i in order:
                if contexts[i].q not in seen:seen.add(contexts[i].q);selected.append((tag,i));break
        def describe(ctx,p):
            return dict(candidate_id=p[0],candidate_name=names[p[0]],length=p[1],
                walk_nodes=[names[n] for n in [ctx.q]+list(p[4])+[p[0]]],
                original_directed_edges=[dict(head=names[h],relation=rels[r],tail=names[t])
                    for j,(h,r,t) in enumerate(ctx.edges) if p[2]>>j&1])
        for tag,i in selected:
            row,ctx=rows[i],contexts[i];es=set(ctx.fuzzy)
            mask=sum(1<<j for j,e in enumerate(ctx.edges) if e in es)
            paths=[p for p in ctx.paths if p[1]==3]
            retained=[p for p in paths if p[2]&mask==p[2]];lost=[p for p in paths if p[2]&mask!=p[2]]
            baseline=ctx.select(dict(method='shortest_paths',seed=0,budget='native'))
            case=dict(dataset=name,row=i,selection_stratum=tag,query_id=ctx.q,query_name=names[ctx.q],
                gold_name=names[row['gold_entity_id']],gold_used_for_selection=False,
                source_occurrences=len(ctx.raw),source_unique=len(ctx.edges),budget=len(ctx.fuzzy),
                original_metrics=ctx.metrics(ctx.fuzzy,row['gold_entity_id']),
                shortest_path_metrics=ctx.metrics(baseline,row['gold_entity_id']),
                retained_examples=[describe(ctx,p) for p in retained[:3]],lost_examples=[describe(ctx,p) for p in lost[:3]])
            cases.append(case)
            text.extend([f'## {name} — row {i} ({tag})',
                f'Query: **{names[ctx.q]}**. Source occurrences/unique: {len(ctx.raw)}/{len(ctx.edges)}; matched budget: {len(ctx.fuzzy)}.',
                f'Original fuzzy retains {len(retained)}/{len(paths)} exact length-3 path witnesses. Gold is reported only in the JSON diagnostic and does not select these examples.'])
            for label,key in [('Retained','retained_examples'),('Lost','lost_examples')]:
                text.append(f'**{label} examples:**')
                examples=case[key]
                if not examples:text.append('None in this query.')
                for p in examples:
                    text.append('- Undirected walk: '+' → '.join(p['walk_nodes'])+'. Original directed edges: '+
                        '; '.join(f"{e['head']} --[{e['relation']}]→ {e['tail']}" for e in p['original_directed_edges']))
    write(out/'case_audit.json',cases)
    (out/'case_audit.md').write_text('\n\n'.join(text)+'\n')
    print(f'Wrote {len(cases)} case audits',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',default=str(OUT));run(p.parse_args())
