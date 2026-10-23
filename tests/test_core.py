import json
import sys
import unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core import evaluate
from agent import run
FIX=json.loads((ROOT/'data/scenarios.json').read_text())
class CoreTests(unittest.TestCase):
    def test_supplier_update_changes_decision(self):
        o=json.loads(json.dumps(FIX[0]));before=evaluate(o)
        self.assertEqual(before['selected']['id'],'S-A')
        o['suppliers'][1]['lead_days']=14
        after=evaluate(o)
        self.assertEqual(after['selected']['id'],'S-B')
        self.assertEqual(after['comparison']['emission_difference_t'],-90)
        self.assertEqual(after['comparison']['quote_difference_lakh'],2.5)
        self.assertEqual(after['suppliers'][2]['issues'],['Missing emissions evidence'])
    def test_messy_evidence_and_rule_scope(self):
        r=evaluate(FIX[1]);self.assertEqual(r['selected']['id'],'A-F')
        self.assertEqual(r['suppliers'][0]['emissions_t'],520)
        self.assertIn('Incomparable footprint boundary',r['suppliers'][1]['issues'])
        self.assertTrue(r['rules'][0]['relevant'])
        self.assertFalse(evaluate(FIX[0])['rules'][0]['relevant'])
    def test_missing_evidence_blocks_draft(self):
        o=json.loads(json.dumps(FIX[0]))
        for s in o['suppliers']: s['emissions']=None
        r=evaluate(o);self.assertIsNone(r['draft_po']);self.assertEqual(r['status'],'needs_evidence')
    def test_rejects_duplicate_ids(self):
        o=json.loads(json.dumps(FIX[0]));o['suppliers'][1]['id']=o['suppliers'][0]['id']
        with self.assertRaisesRegex(ValueError,'unique'): evaluate(o)
    def test_preview_trace_contains_actual_tool_results(self):
        r=run(FIX[0],use_model=False)
        self.assertEqual(r['agent_trace'][2]['tool'],'normalize_supplier_evidence')
        self.assertEqual(r['agent_trace'][2]['result'][1]['issues'],['Misses delivery deadline'])
    def test_gemini_tool_loop_executes_and_keeps_deterministic_decision(self):
        calls=iter(['validate_order','normalize_supplier_evidence','screen_rule_relevance','rank_and_draft'])
        def fake_call(contents, available=None):
            if not available: return {'role':'model','parts':[{'text':'Approval is required because the planning score exceeds the quote budget.'}]}
            name=next(calls)
            self.assertIn(name,available)
            return {'role':'model','parts':[{'functionCall':{'name':name,'args':{}}}]}
        with patch.dict('os.environ',{'GEMINI_API_KEY':'test-key'}), patch('agent._gemini_call',side_effect=fake_call):
            r=run(FIX[0])
        self.assertEqual(r['mode'],'gemini_tool_calls')
        self.assertEqual(r['selected']['id'],'S-A')
        self.assertEqual([t['tool'] for t in r['agent_trace']],['validate_order','normalize_supplier_evidence','screen_rule_relevance','rank_and_draft'])
        self.assertIn('Every draft requires manager approval',r['agent_note'])
        self.assertNotIn('because the planning score exceeds',r['agent_note'])
        self.assertIn('because the planning score exceeds',r['model_draft_note'])
if __name__=='__main__':unittest.main()
