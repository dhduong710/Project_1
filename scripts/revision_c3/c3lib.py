"""Selection and retention primitives. Selection receives no held-out labels.

Graph information is operationalized as several separate structural proxies;
none is a claim of preserved biological mechanism or Shannon mutual information.
"""
from __future__ import annotations
import sys
import math
from pathlib import Path
from collections import Counter, defaultdict, deque
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'revision_c2'))
from common import ROOT, DATASETS, read, write, csv_write, freeze, digest, object_digest, align, load_rows, reorder_row, cluster_bootstrap
from run_e2e import Generator, score_prediction, normalize

OUT=ROOT/'results/revision_c3'
FEATURE_PATHS={
 'primekg':'dataset/setting_a/27_n2_fuzzy_retrieval/{split}_path_features.json',
 'pharmkg':'dataset/setting_c_pharmkg/11_fuzzy_retrieval/{split}_path_features.json',
 'hetionet':'dataset/setting_d_hetionet/10_fuzzy_retrieval/{split}_fuzzy_retrieval_main.json',
 'drkg':'dataset/setting_e_drkg/10_fuzzy_retrieval/rgcn/{split}_fuzzy_retrieval_main.json',
 'repodb':'dataset/setting_f_repodb/10_fuzzy_retrieval/rgcn/{split}_fuzzy_retrieval_main.json',
}
MAP_DIRS={
 'primekg':'dataset/setting_a/04_drkgc_json',
 'pharmkg':'dataset/setting_c_pharmkg/06_fograg_ready',
 'hetionet':'dataset/setting_d_hetionet/06_fograg_ready',
 'drkg':'dataset/setting_e_drkg/06_fograg_ready/rgcn',
 'repodb':'dataset/setting_f_repodb/06_fograg_ready/rgcn',
}
HET_META='dataset/setting_d_hetionet/03_graph/node_metadata.json'
METHODS=['native_topk','native_coverage','degree_topk','query_bfs','ppr_query','ppr_terminals','shortest_paths','relation_diverse']
PRIMARY_METRICS=['candidate_coverage_retained','reach2_retention','reach3_retention','path2_retention','path3_retention','typed_pattern_retention','relation_retention','relation_jsd','incoming2_retention','gold_reach3_retention']


def variants(seeds=5,ratios=(.2,.35,.55,.75,.9)):
    out=[dict(key=k,method=k,budget='native',seed=0) for k in ['source_raw','source_unique','original_fuzzy','empty_graph']+METHODS]
    for m in ['random','random_coverage']:
        out += [dict(key=f'{m}_s{s}',method=m,budget='native',seed=s) for s in range(seeds)]
    for ratio in ratios:
        for m in ['native_coverage','native_topk','ppr_terminals','shortest_paths','relation_diverse','random']:
            for s in range(min(seeds,3) if m=='random' else 1):
                out.append(dict(key=f'{m}_r{int(round(100*ratio)):02d}_s{s}',method=m,budget=float(ratio),seed=s))
    return out


def gpu_variants(plan):
    # Freeze these criteria before seeing results: all matched controls plus
    # two common-budget operating points for three different selectors.
    return [v for v in plan if v['budget']=='native' or
            (v['budget'] in [.35,.75] and v['method'] in ['native_coverage','ppr_terminals','random'] and v['seed']==0)]


def input_paths(name,split):
    paths=[ROOT/DATASETS[name][k]/f'{split}.json' for k in ['raw','fuzzy']]
    paths += [ROOT/FEATURE_PATHS[name].format(split=split),ROOT/MAP_DIRS[name]/'id2entity.json',ROOT/MAP_DIRS[name]/'id2relation.json']
    if name=='primekg':paths.append(ROOT/'configs/week16/retrieval_tight.json')
    if name=='hetionet':paths.append(ROOT/HET_META)
    return paths


def node_types(name):
    entities={int(k):v for k,v in read(ROOT/MAP_DIRS[name]/'id2entity.json').items()}
    if name in ['drkg','repodb']:
        return {i:n.split('::')[0] for i,n in entities.items() if '::' in n}
    if name=='hetionet':
        lookup=defaultdict(set)
        for r in read(ROOT/HET_META).values():
            for k in ['name','display_name']:lookup[r[k]].add(r['kind'])
        return {i:next(iter(lookup[n])) for i,n in entities.items() if len(lookup[n])==1}
    return {}  # Do not guess types from gene-like names in PrimeKG/PharmKG.


def load_dataset(name,split):
    raw=load_rows(name,split);fz=align(raw,load_rows(name,split,'fuzzy'))
    feats=align(raw,read(ROOT/FEATURE_PATHS[name].format(split=split)))
    rows=[];contexts=[];types=node_types(name)
    cfg=read(ROOT/'configs/week16/retrieval_tight.json') if name=='primekg' else None
    for r,f,feat in zip(raw,fz,feats):
        ids=r['rank_entities_id'];order=[ids.index(c) for c in f['rank_entities_id']]
        row=reorder_row(r,order)
        if name in ['primekg','pharmkg']:
            assert feat['candidate_entity_ids']==row['rank_entities_id']
            scored=feat['triple_feature_rows']
        else:
            assert feat['rank_entities_id']==row['rank_entities_id']
            scored=feat['triple_score_rows']
        score_map={}
        for tr in scored:
            edge=tuple(tr.get('triple') or [tr['head_id'],tr['relation_id'],tr['tail_id']])
            if name=='primekg':
                band=max((1. if p<5 else .6 if p<10 else .25 for p in tr['touched_candidate_positions']),default=0.)
                score=round(band+cfg['touch_candidate']*tr['touches_candidate']+cfg['touch_query']*tr['touches_query']+
                    cfg['direct_shortcut']*tr['direct_candidate_query_flag']+cfg['contra']*tr['contra_flag']+
                    cfg['density']*min(float(tr['local_density_hint']),10.)/10.,6)
            else:score=float(tr['triple_score'] if name=='pharmkg' else tr['score'])
            if edge in score_map:assert abs(score_map[edge]-score)<1e-8
            score_map[edge]=score
        assert set(score_map)=={tuple(e) for e in row['subgraph']},f'Native score/source mismatch: {name}'
        ctx=Context(row,f['subgraph'],score_map,types)
        rows.append(row);contexts.append(ctx)
    return rows,contexts


def bfs(adj,start):
    dist={start:0};todo=deque([start])
    while todo:
        u=todo.popleft()
        for v in sorted(adj.get(u,())):
            if v not in dist:dist[v]=dist[u]+1;todo.append(v)
    return dist


def jsd(a,b):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
    if not a.sum() or not b.sum():return None
    a=a/a.sum();b=b/b.sum();m=(a+b)/2
    return float(.5*sum(float(np.sum(x[x>0]*np.log2(x[x>0]/m[x>0]))) for x in [a,b]))


def ratio(n,d):return float(n/d) if d else None


class Context:
    def __init__(self,row,fuzzy,scores,types):
        self.q=int(row['query_entity_id']);self.candidates=list(map(int,row['rank_entities_id']))
        self.raw=[tuple(map(int,e)) for e in row['subgraph']]
        self.edges=list(dict.fromkeys(self.raw));self.index={e:i for i,e in enumerate(self.edges)}
        self.fuzzy=[tuple(map(int,e)) for e in fuzzy]
        assert set(self.fuzzy)<=set(self.edges)
        assert len(set(self.fuzzy))==len(self.fuzzy),'Native fuzzy contains duplicates: budget requires audit'
        self.budget=len(self.fuzzy);self.types=types
        self.scores=[scores[e] for e in self.edges]
        self.adj=defaultdict(set);self.walk=defaultdict(list);self.incident=defaultdict(set);self.incoming=defaultdict(set)
        self.rel=Counter();self.deg=Counter()
        for i,(h,r,t) in enumerate(self.edges):
            self.adj[h].add(t);self.adj[t].add(h)
            self.walk[h].append((t,i,1));self.walk[t].append((h,i,-1))
            self.incident[h].add(i);self.incident[t].add(i);self.incoming[t].add(i)
            self.rel[r]+=1;self.deg[h]+=1;self.deg[t]+=1
        self.nodes=set(self.incident);self.dist=bfs(self.adj,self.q)
        self.source_covered=set(self.candidates)&self.nodes
        self.native_order=sorted(range(len(self.edges)),key=lambda i:(-self.scores[i],i))
        self.native_rank={i:j for j,i in enumerate(self.native_order)}
        # Exact edge-labeled simple path witnesses, length 1..3, traversable
        # undirected; stored signs retain the orientation of each original edge.
        self.paths=[]
        def walk(u,visited,mask,pattern):
            if len(pattern) and u in self.candidates:
                self.paths.append((u,len(pattern),mask,tuple(pattern),tuple(visited[1:-1])))
            if len(pattern)==3:return
            for v,i,direction in self.walk.get(u,[]):
                if v not in visited:
                    walk(v,visited+[v],mask|(1<<i),pattern+[(self.edges[i][1],direction)])
        walk(self.q,[self.q],0,[])
        self.paths.sort(key=lambda p:(p[1],self.candidates.index(p[0]),p[2]))
        self.patterns={p[3] for p in self.paths if p[1]>=2}
        self.gene_paths=[p for p in self.paths if p[1]>=2 and all(types.get(n)=='Gene' for n in p[4])]
        self.receptive={}
        for a in [self.q]+self.candidates:
            first=set(self.incoming.get(a,()))
            self.receptive[a]=first|{j for i in first for j in self.incoming.get(self.edges[i][0],())}
        self.orders={}
        self.seed_key=object_digest(dict(q=self.q,c=self.candidates,edges=self.edges))
        self._metric_cache={}

    def ppr(self,terminals):
        nodes=sorted(self.nodes|{self.q});ix={n:i for i,n in enumerate(nodes)}
        teleport=np.zeros(len(nodes))
        anchors=[a for a in terminals if a in ix]
        for a in anchors:teleport[ix[a]]+=1/len(anchors)
        src=[];dst=[]
        for u in nodes:
            for v in self.adj.get(u,()):src.append(ix[u]);dst.append(ix[v])
        src=np.asarray(src,dtype=int);dst=np.asarray(dst,dtype=int)
        degree=np.array([len(self.adj.get(u,())) for u in nodes],dtype=float)
        x=teleport.copy()
        for _ in range(200):
            y=.15*teleport+.85*(np.bincount(dst,weights=x[src]/degree[src],minlength=len(nodes))+x[degree==0].sum()*teleport)
            if np.abs(y-x).sum()<1e-10:x=y;break
            x=y
        return {n:float(x[ix[n]]) for n in nodes}

    def ordering(self,method,seed):
        key=(method,seed)
        if key in self.orders:return self.orders[key]
        n=len(self.edges)
        if method.startswith('random'):
            rng=np.random.default_rng(int(self.seed_key[:16],16)^int(seed))
            order=rng.permutation(n).tolist()
        elif method.startswith('native') or method=='shortest_paths':order=list(self.native_order)
        elif method=='degree_topk':order=sorted(range(n),key=lambda i:(-sum(self.deg[v] for v in [self.edges[i][0],self.edges[i][2]]),i))
        elif method=='query_bfs':order=sorted(range(n),key=lambda i:(min(self.dist.get(self.edges[i][0],10**6),self.dist.get(self.edges[i][2],10**6)),i))
        elif method.startswith('ppr_'):
            p=self.ppr([self.q] if method=='ppr_query' else [self.q]+self.candidates)
            order=sorted(range(n),key=lambda i:(-p[self.edges[i][0]]-p[self.edges[i][2]],i))
        elif method=='relation_diverse':
            # Round-robin relation strata; native score ranks inside each stratum.
            groups=defaultdict(deque)
            for i in self.native_order:groups[self.edges[i][1]].append(i)
            order=[]
            while any(groups.values()):
                for rel in sorted(groups):
                    if groups[rel]:order.append(groups[rel].popleft())
        else:raise ValueError(method)
        self.orders[key]=order
        return order

    def select(self,v):
        m=v['method']
        if m=='source_raw':return list(self.raw)
        if m=='source_unique':return list(self.edges)
        if m=='original_fuzzy':return list(self.fuzzy)
        if m=='empty_graph':return []
        budget=self.budget if v['budget']=='native' else int(round(len(self.edges)*float(v['budget'])))
        budget=max(0,min(len(self.edges),budget));order=self.ordering(m,v['seed']);chosen=set()
        if m in ['native_coverage','random_coverage']:
            for a in self.candidates+[self.q]:
                if len(chosen)>=budget:break
                if self.incident.get(a,set())&chosen:continue
                for i in order:
                    if i in self.incident.get(a,set()):chosen.add(i);break
        if m=='shortest_paths':
            # At most one shortest <=3-edge path per candidate, in candidate order;
            # add only complete paths that fit, then score-ordered fill.
            for c in self.candidates:
                options=[p for p in self.paths if p[0]==c]
                if not options:continue
                shortest=min(p[1] for p in options)
                candidates=[{i for i in range(len(self.edges)) if p[2]>>i&1} for p in options if p[1]==shortest]
                candidates.sort(key=lambda ids:(len(ids-chosen),-sum(self.scores[i] for i in ids),sorted(ids)))
                for ids in candidates:
                    if len(chosen|ids)<=budget:chosen|=ids;break
        for i in order:
            if len(chosen)>=budget:break
            chosen.add(i)
        assert len(chosen)==budget
        return [self.edges[i] for i in sorted(chosen)]

    def metrics(self,selected,gold):
        es=set(selected);assert es<=set(self.edges)
        key=tuple(sorted(es))
        if key not in self._metric_cache:
            selected_ids={self.index[e] for e in es};mask=sum(1<<i for i in selected_ids)
            nodes={n for h,r,t in es for n in [h,t]};covered=set(self.candidates)&nodes
            rel=Counter(r for h,r,t in es);deg=Counter(n for h,r,t in es for n in [h,t])
            kept=[p for p in self.paths if p[2]&mask==p[2]]
            patterns={p[3] for p in kept if p[1]>=2}
            gpaths=[p for p in self.gene_paths if p[2]&mask==p[2]]
            incoming_union=set().union(*self.receptive.values())
            result=dict(source_unique_edges=len(self.edges),selected_unique_edges=len(es),
                unique_edge_retention=ratio(len(es),len(self.edges)),node_retention=ratio(len(nodes),len(self.nodes)),
                candidate_coverage_absolute=len(covered)/20.,candidate_coverage_retained=ratio(len(covered),len(self.source_covered)),
                query_present=int(self.q in nodes),query_coverage_retained=int(self.q in nodes) if self.q in self.nodes else None,
                relation_retention=ratio(len(rel),len(self.rel)),relation_jsd=jsd([self.rel[r] for r in self.rel],[rel[r] for r in self.rel]),
                degree_mass_jsd=jsd([self.deg[n] for n in self.nodes],[deg[n] for n in self.nodes]),
                typed_pattern_retention=ratio(len(patterns),len(self.patterns)),source_typed_patterns=len(self.patterns),
                gene_path_retention=ratio(len(gpaths),len(self.gene_paths)),source_gene_paths=len(self.gene_paths),
                node_type_annotation_rate=ratio(sum(n in self.types for n in self.nodes),len(self.nodes)),
                incoming2_retention=ratio(len(incoming_union&selected_ids),len(incoming_union)),
                source_incoming2_edges=len(incoming_union),
                source_candidates_without_incoming=sum(not self.incoming.get(c) for c in self.candidates)/20.)
            for lo,hi,tag in [(0,5,'top5'),(5,10,'mid5'),(10,20,'tail10')]:
                group=set(self.candidates[lo:hi])
                result[tag+'_coverage_retained']=ratio(len(group&covered),len(group&self.source_covered))
            for k in [2,3]:
                src=[p for p in self.paths if p[1]==k];dst=[p for p in kept if p[1]==k]
                result[f'path{k}_retention']=ratio(len(dst),len(src));result[f'source_paths{k}']=len(src)
                before={p[0] for p in self.paths if p[1]<=k};after={p[0] for p in kept if p[1]<=k}
                result[f'reach{k}_retention']=ratio(len(after),len(before));result[f'source_reach{k}']=len(before)
            direct={i for i,(h,r,t) in enumerate(self.edges) if self.q in [h,t] and (h in self.candidates or t in self.candidates)}
            result['direct_edge_retention']=ratio(len(direct&selected_ids),len(direct))
            result['direct_edge_share']=ratio(len(direct&selected_ids),len(es))
            rare={r for r,n in self.rel.items() if n<=np.median(list(self.rel.values()))} if self.rel else set()
            result['rare_relation_edge_retention']=ratio(sum(rel[r] for r in rare),sum(self.rel[r] for r in rare))
            self._metric_cache[key]=(result,kept)
        result,kept=self._metric_cache[key];result=dict(result)
        result.update(source_edge_occurrences=len(self.raw),selected_edge_occurrences=len(selected),
            occurrence_edge_retention=ratio(len(selected),len(self.raw)),
            source_duplicate_fraction=1-len(self.edges)/len(self.raw) if self.raw else None,
            encoder_global_fallback=int(len(selected)<=10),gold_in_candidates=int(gold in self.candidates))
        before={p[0] for p in self.paths};after={p[0] for p in kept}
        result['gold_reach3_retention']=int(gold in after) if gold in self.candidates and gold in before else None
        result['gold_incident_retention']=ratio(sum(gold in [h,t] for h,r,t in es),len(self.incident.get(gold,()))) if gold in self.candidates else None
        return result


def aggregate(rows):
    out={'n':len(rows)}
    for key in rows[0]:
        if key in ['row','query_id','gold_id','dataset','split','variant','method','budget','seed']:continue
        vals=[r[key] for r in rows if isinstance(r.get(key),(int,float)) and math.isfinite(r[key])]
        if vals:out[key]=float(np.mean(vals));out[key+'_eligible']=len(vals)
    return out


def paired(rows,reference,metrics,repetitions=2000):
    lookup={(r['query_id'],r['gold_id']):r for r in reference}
    assert len(lookup)==len(reference)==len(rows)
    out=[]
    for metric in metrics:
        selected=[r for r in rows if r.get(metric) is not None and lookup[(r['query_id'],r['gold_id'])].get(metric) is not None]
        if not selected:continue
        delta=np.array([r[metric]-lookup[(r['query_id'],r['gold_id'])][metric] for r in selected])
        groups=np.array([r['query_id'] for r in selected])
        ci=cluster_bootstrap(delta,groups,repetitions)
        out.append(dict(metric=metric,n_eligible=len(selected),delta_mean=ci['delta_mrr'],ci95_low=ci['ci95_low'],ci95_high=ci['ci95_high'],clusters=ci['clusters']))
    return out
