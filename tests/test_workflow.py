import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agent
import store
from report_view import render
from core import evaluate

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = json.loads((ROOT / "data/scenarios.json").read_text(encoding="utf-8"))


class WorkflowTests(unittest.TestCase):
    def test_extracted_note_requires_human_confirmation(self):
        generated = {"name":"RenewMetal","id":"S-D","quote_lakh":61,"lead_days":13,
                     "emissions":180,"emission_unit":"tCO2e","boundary":"cradle-to-gate",
                     "evidence_date":"2026-09-30","source":"EPD-RM-26","ship_from":"India"}
        with patch.dict(os.environ, {"GEMINI_API_KEY":"test-only"}), patch.object(
                agent, "_gemini_call", return_value={"parts":[{"text":json.dumps(generated)}]}):
            draft = agent.extract_supplier_note("A supplier email with a quote and an EPD for a steel order.")
        self.assertEqual(draft["candidate"]["emissions"],180)
        self.assertEqual(draft["needs_review"],[])
        # Extraction alone must not silently change the procurement order.
        self.assertEqual(len(SCENARIOS[0]["suppliers"]),3)

    def test_saved_decision_and_approval_survive_new_connection(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"records.sqlite3"
            order=SCENARIOS[0]
            report=evaluate(order)
            report.update(decision_id="one-run",mode="rules_preview",agent_trace=[])
            store.save(report,order,path)
            self.assertEqual(store.get("one-run",path)["input_order"]["id"],"STEEL-101")
            approval={"action":"approve","role":"procurement_manager","at":store.now(),"note":"Reviewed"}
            store.decide("one-run",approval,path)
            self.assertEqual(store.get("one-run",path)["approval"]["action"],"approve")
            self.assertEqual([x["event"] for x in store.audit(path=path)], ["human_decision","evaluation"])
            with self.assertRaisesRegex(ValueError,"already recorded"):
                store.decide("one-run",approval,path)

    def test_readable_report_escapes_supplier_text(self):
        order=json.loads(json.dumps(SCENARIOS[0]))
        order["suppliers"][0]["name"]="<script>alert(1)</script>"
        report=evaluate(order)
        report.update(input_order=order,created_at=store.now(),mode="rules_preview",agent_trace=[],
                      approval={"action":"approve","role":"procurement_manager","at":store.now(),"note":"Reviewed"})
        page=render(report)
        self.assertIn("Manager approved draft",page)
        self.assertIn("Print or save as PDF",page)
        self.assertNotIn("<script>alert(1)</script>",page)


if __name__ == "__main__":
    unittest.main()
