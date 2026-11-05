import unittest
from copy import deepcopy
import numpy as np
from c3lib import Context, variants, jsd, ratio
from run_gpu import distance


def example():
    row=dict(query_entity_id=0,rank_entities_id=list(range(1,21)),gold_entity_id=1,
        subgraph=[[1,0,21],[21,1,0],[2,0,22],[22,1,23],[23,1,0],[3,2,0],[1,3,21],[30,0,31]])
    return row,Context(row,row['subgraph'][:4],{tuple(e):float(8-i) for i,e in enumerate(row['subgraph'])},{21:'Gene',22:'Gene',23:'Gene'})


class ProtocolTests(unittest.TestCase):
    def test_all_selectors_budget_and_subset(self):
        r,c=example()
        for v in variants():
            es=c.select(v);self.assertLessEqual(set(es),set(c.edges))
            if v['method'] not in ['source_raw','source_unique','original_fuzzy','empty_graph']:
                budget=c.budget if v['budget']=='native' else round(len(c.edges)*v['budget'])
                self.assertEqual(len(es),budget);self.assertEqual(len(set(es)),len(es))
    def test_full_retention(self):
        r,c=example();m=c.metrics(c.raw,1)
        for key in ['path2_retention','path3_retention','typed_pattern_retention','incoming2_retention','candidate_coverage_retained','gene_path_retention']:self.assertEqual(m[key],1)
        self.assertEqual(m['relation_jsd'],0)
    def test_empty_is_not_full(self):
        r,c=example();m=c.metrics([],1)
        self.assertEqual(m['path2_retention'],0);self.assertEqual(m['candidate_coverage_retained'],0)
        self.assertIsNone(m['relation_jsd']);self.assertEqual(m['encoder_global_fallback'],1)
    def test_edge_labeled_parallel_paths(self):
        r,c=example()
        self.assertEqual(c.metrics(c.raw,1)['source_paths2'],2)
        self.assertEqual(c.metrics([(1,0,21),(21,1,0)],1)['path2_retention'],.5)
    def test_path_direction_recorded(self):
        r,c=example();p=[p for p in c.paths if p[0]==1 and p[1]==2][0]
        self.assertEqual(p[3][0],(1,-1))
    def test_no_paths_undefined(self):
        row=dict(query_entity_id=0,rank_entities_id=list(range(1,21)),subgraph=[[40,1,41]])
        c=Context(row,row['subgraph'],{(40,1,41):1},{})
        m=c.metrics(c.edges,1);self.assertIsNone(m['path2_retention']);self.assertIsNone(m['gold_reach3_retention'])
    def test_duplicate_decomposition(self):
        r,c=example();r['subgraph']+=r['subgraph']
        d=Context(r,c.fuzzy,dict(zip(c.edges,c.scores)),{})
        m=d.metrics(d.edges,1)
        self.assertEqual(m['unique_edge_retention'],1);self.assertEqual(m['occurrence_edge_retention'],.5)
    def test_gold_not_selector_input(self):
        r,c=example();r['gold_entity_id']=999
        other=Context(r,c.fuzzy,dict(zip(c.edges,c.scores)),c.types)
        for v in variants():self.assertEqual(c.select(v),other.select(v))
    def test_random_seed_reproducible(self):
        r,c=example();v=dict(method='random',seed=3,budget='native')
        self.assertEqual(c.select(v),c.select(v))
        self.assertNotEqual(c.ordering('random',3),c.ordering('random',4))
    def test_gene_annotation_not_guessed(self):
        r,c=example();c=Context(r,c.fuzzy,dict(zip(c.edges,c.scores)),{})
        self.assertIsNone(c.metrics(c.edges,1)['gene_path_retention'])
    def test_native_topk(self):
        r,c=example();self.assertEqual(c.select(dict(method='native_topk',seed=0,budget='native')),c.edges[:4])
    def test_coverage_not_assumed(self):
        r,c=example();es=c.select(dict(method='native_coverage',seed=0,budget=.125))
        self.assertLess(c.metrics(es,1)['candidate_coverage_retained'],1)
    def test_empty_source(self):
        r=dict(query_entity_id=0,rank_entities_id=list(range(1,21)),subgraph=[])
        c=Context(r,[],{},{})
        for v in variants():self.assertEqual(c.select(v),[])
    def test_jsd(self):
        self.assertAlmostEqual(jsd([1,0],[0,1]),1)
        self.assertEqual(jsd([2,1],[4,2]),0);self.assertIsNone(ratio(0,0))
    def test_ppr_normalized_with_isolate(self):
        r,c=example();p=c.ppr([0]);self.assertAlmostEqual(sum(p.values()),1,places=8)
    def test_foreign_edge_rejected(self):
        r,c=example()
        with self.assertRaises(AssertionError):c.metrics([(900,1,901)],1)
    def test_representation_identical(self):
        x=np.array([[1.,2.],[3.,4.]])
        cos,rel=distance(x,x)
        np.testing.assert_allclose(cos,[1,1]);np.testing.assert_allclose(rel,[0,0])
    def test_cosine_does_not_hide_scale_in_l2(self):
        x=np.array([[1.,2.]])
        cos,rel=distance(3*x,x)
        self.assertAlmostEqual(cos[0],1);self.assertAlmostEqual(rel[0],2)
    def test_representation_opposite(self):
        x=np.array([[1.,2.]])
        cos,rel=distance(-x,x)
        self.assertAlmostEqual(cos[0],-1);self.assertAlmostEqual(rel[0],2)


if __name__=='__main__':unittest.main()
