import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from run_e2e_stable import import_matching_cache,validate_c3,run
from audit_precision_c2 import encoder_key
from compare_precision import prediction_map


class PrecisionRepairTests(unittest.TestCase):
    def test_cache_import_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source';dest=Path(d)/'dest'
            source.write_text(json.dumps(dict(key='a',prediction='Drug A'))+'\n')
            cache={}
            self.assertEqual(import_matching_cache(dest,source,cache),1)
            self.assertEqual(import_matching_cache(dest,source,cache),0)
            self.assertEqual(len(dest.read_text().splitlines()),1)

    def test_conflicting_cache_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source';dest=Path(d)/'dest'
            source.write_text(json.dumps(dict(key='a',prediction='different'))+'\n')
            with self.assertRaises(ValueError):import_matching_cache(dest,source,{'a':'original'})

    def test_smoke_donor_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/'gpu_complete.json').write_text(json.dumps(dict(status='smoke_only',all_test_rows=False)))
            (p/'protocol_gpu.json').write_text('{}')
            with self.assertRaises(ValueError):validate_c3(p)

    def test_legacy_directory_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'protocol_e2e.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'Legacy output'):
                run(SimpleNamespace(out=d,cpu_results=d))

    def test_edge_order_does_not_change_audit_key(self):
        row=dict(query_entity_id=1,rank_entities_id=[2,3],subgraph=[[1,0,2],[2,0,3]])
        self.assertEqual(encoder_key(row),encoder_key(dict(row,subgraph=list(reversed(row['subgraph'])))))

    def test_duplicate_occurrence_changes_audit_key(self):
        row=dict(query_entity_id=1,rank_entities_id=[2,3],subgraph=[[1,0,2]])
        self.assertNotEqual(encoder_key(row),encoder_key(dict(row,subgraph=row['subgraph']*2)))

    def test_candidate_order_changes_audit_key(self):
        row=dict(query_entity_id=1,rank_entities_id=[2,3],subgraph=[[1,0,2]])
        self.assertNotEqual(encoder_key(row),encoder_key(dict(row,rank_entities_id=[3,2])))

    def test_duplicate_query_gold_is_rejected(self):
        row=dict(query_id=1,gold_id=2)
        with self.assertRaises(ValueError):prediction_map([row,row])


if __name__=='__main__':unittest.main()
