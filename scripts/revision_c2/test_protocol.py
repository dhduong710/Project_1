"""Scientific invariants; run with python -m unittest discover -s scripts/revision_c2."""
import unittest
import numpy as np
from common import (graph_features,select_graph,graph_stats,grouped_folds,fit_pairwise,
    ranks,metrics,order_of,native_score,align,reorder_row,cluster_bootstrap)
from run_e2e import score_prediction,select_calibration


def fixture():
    return dict(query_entity_id=100,gold_entity_id=2,query_entity='disease',output='c2',
        rank_entities_id=list(range(20)),rank_entities=[f'c{i}' for i in range(20)],
        subgraph=[[i,0,100] for i in range(20)]+[[i,1,i+200] for i in range(20)],
        input='Question: What drug treats disease?\nAnswer: ')


class ProtocolTests(unittest.TestCase):
    def test_e2e_promote_to_front(self):
        r=fixture()
        self.assertEqual(score_prediction(r,'c2')['adjusted_rank'],1)
        self.assertEqual(score_prediction(r,'c0')['adjusted_rank'],3)
        self.assertEqual(score_prediction(r,'c9')['adjusted_rank'],4)
        self.assertEqual(score_prediction(r,'unmatched')['adjusted_rank'],4)
        self.assertEqual(score_prediction(r,'unmatched')['exact_match'],0)

    def test_e2e_absent_gold_even_if_output_matches(self):
        r=fixture();r['gold_entity_id']=999;r['output']='unknown'
        self.assertEqual(score_prediction(r,'unknown')['adjusted_rr'],0.)

    def test_no_substring_candidate_matching(self):
        self.assertEqual(score_prediction(fixture(),'c2, c3, c4')['invalid'],1)

    def test_duplicate_display_name_ambiguous(self):
        r=fixture();r['rank_entities'][3]='c2'
        self.assertEqual(score_prediction(r,'c2')['invalid'],1)

    def test_validation_subset_keeps_query_groups(self):
        rows=[dict(query_entity_id=i//3) for i in range(30)]
        ix=select_calibration(rows,5,1)
        groups={rows[i]['query_entity_id'] for i in ix}
        self.assertEqual(len(ix),3*len(groups))

    def test_absent_gold_zero(self):
        order=np.tile(np.arange(20),(2,1)); gold=np.array([-1,0])
        self.assertEqual(metrics(order,gold)['mrr_at20'],.5)
        self.assertEqual(ranks(order,gold).tolist(),[21,1])

    def test_ties_preserve_original_order(self):
        self.assertEqual(order_of(np.zeros((1,20))).tolist(),[list(range(20))])

    def test_feature_labels_are_not_inputs(self):
        a=fixture();b=dict(a,gold_entity_id=999,output='other')
        np.testing.assert_array_equal(graph_features(a),graph_features(b))

    def test_group_cv_disjoint(self):
        g=np.repeat(np.arange(10),3)
        seen=[]
        for tr,va in grouped_folds(g,5,9):
            self.assertFalse(set(g[tr])&set(g[va]));seen.extend(va)
        self.assertEqual(sorted(seen),list(range(len(g))))

    def test_selection_budget_membership_and_order(self):
        row=fixture();original=list(row['rank_entities_id'])
        edges=select_graph(row,budget=7)
        self.assertEqual(len(edges),7)
        self.assertTrue({tuple(e) for e in edges}<={tuple(e) for e in row['subgraph']})
        self.assertEqual(row['rank_entities_id'],original)
        self.assertEqual(select_graph(row,budget=0),[])

    def test_empty_graph(self):
        r=fixture();r['subgraph']=[]
        self.assertEqual(select_graph(r),[])
        self.assertTrue(np.isfinite(graph_features(r)).all())

    def test_coverage_is_measured_not_assumed(self):
        r=fixture();s=graph_stats(r,select_graph(r,budget=2))
        self.assertLess(s['candidate_coverage_retained'],1)

    def test_reorder_prompt_alignment(self):
        row=fixture();r=reorder_row(row,list(reversed(range(20))))
        self.assertEqual(r['rank'],18)
        self.assertEqual(r['rank_entities'][0],'c19')
        self.assertEqual(r['input'].count('[ENTITY]'),20)
        self.assertEqual(r['input'].count('[QUERY]'),1)
        self.assertEqual(row['rank_entities'][0],'c0')

    def test_alignment_rejects_duplicate_keys(self):
        row=fixture()
        with self.assertRaises(ValueError):align([row,row],[row,row])

    def test_learning_nonnegative_and_improves_signal(self):
        x=np.zeros((3,20,2));x[:,3,1]=1
        a=dict(x=x,gold=np.array([3,3,3]),groups=np.array([1,2,3]),ids=np.tile(np.arange(20),(3,1)))
        w=fit_pairwise(a)
        self.assertTrue((w>=0).all())
        self.assertEqual(metrics(order_of(x@w),a['gold'])['mrr_at20'],1.)

    def test_missing_gold_learning_fallback(self):
        a=dict(x=np.zeros((2,20,5)),gold=np.array([-1,-1]),groups=np.array([1,2]))
        np.testing.assert_array_equal(fit_pairwise(a),[1,0,0,0,0])

    def test_same_query_known_positive_not_negative(self):
        x=np.zeros((2,20,2));x[:,0,1]=1
        # Every candidate is a known positive: there must be no training pairs.
        a=dict(x=np.tile(x[:1],(20,1,1)),gold=np.arange(20),groups=np.zeros(20),ids=np.tile(np.arange(20),(20,1)))
        np.testing.assert_array_equal(fit_pairwise(a),[1,0])

    def test_constant_native_features_finite(self):
        a=dict(native=np.ones((1,20,3)),x=np.zeros((1,20,5)))
        self.assertTrue(np.isfinite(native_score(a,.5,.1,.8)).all())

    def test_paired_bootstrap_identical_zero(self):
        ci=cluster_bootstrap(np.zeros(4),np.array([1,1,2,3]),100)
        self.assertEqual(ci['ci95_low'],0.)
        self.assertEqual(ci['ci95_high'],0.)


if __name__=='__main__':unittest.main()
