"""Dependency-free local demo server. Run on localhost; never expose to a public network."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json
import os
import uuid
from time import perf_counter
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
from agent import run, extract_supplier_note
import store
from report_view import render as render_report

ROOT=Path(__file__).resolve().parent
FIXTURES=json.loads((ROOT/'data/scenarios.json').read_text(encoding='utf-8'))
class Handler(BaseHTTPRequestHandler):
    def send(self, status, data, mime='application/json'):
        raw=(json.dumps(data,ensure_ascii=False) if mime=='application/json' else data).encode()
        self.send_response(status); self.send_header('Content-Type',mime+'; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        parsed=urlsplit(self.path)
        if parsed.path=='/': return self.send(200,(ROOT/'index.html').read_text(encoding='utf-8'),'text/html')
        if parsed.path=='/api/fixtures': return self.send(200,FIXTURES)
        if parsed.path=='/api/audit': return self.send(200,store.audit())
        if parsed.path=='/api/record':
            did=parse_qs(parsed.query).get('id',[''])[0]
            report=store.get(did)
            return self.send(200,report) if report else self.send(404,{"error":"Decision not found"})
        if parsed.path=='/report':
            did=parse_qs(parsed.query).get('id',[''])[0]
            report=store.get(did)
            return self.send(200,render_report(report),'text/html') if report else self.send(404,{"error":"Decision not found"})
        self.send(404,{"error":"Not found"})
    def do_POST(self):
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size>100000: return self.send(413,{"error":"Request too large"})
            body=json.loads(self.rfile.read(size))
            if self.path=='/api/extract':
                return self.send(200,extract_supplier_note(body.get('text')))
            if self.path=='/api/evaluate':
                started=perf_counter()
                report=run(body['order'],bool(body.get('use_model',True)))
                report['run_seconds']=round(perf_counter()-started,2)
                report['input_fingerprint']=report['decision_id']
                report['decision_id']=uuid.uuid4().hex[:12]
                return self.send(200,store.save(report,body['order']))
            if self.path=='/api/decision':
                did=body.get('decision_id'); report=store.get(did)
                if not report: return self.send(404,{"error":"Evaluate the current order first"})
                if body.get('role')!='procurement_manager': return self.send(403,{"error":"Demo role must be procurement_manager. This is not production authentication."})
                if body.get('action') not in ('approve','reject'): return self.send(400,{"error":"Action must be approve or reject"})
                if body['action']=='approve' and not report['draft_po']: return self.send(409,{"error":"No eligible draft to approve"})
                if report.get('approval'): return self.send(409,{"error":"Decision already recorded"})
                approval={'action':body['action'],'role':body['role'],'at':datetime.now(timezone.utc).isoformat(),'note':str(body.get('note',''))[:300]}
                return self.send(200,store.decide(did,approval))
            self.send(404,{"error":"Not found"})
        except (ValueError,KeyError,TypeError) as exc: self.send(400,{"error":str(exc)})
        except RuntimeError as exc: self.send(502,{"error":str(exc)})
        except Exception:
            self.send(500,{"error":"Unexpected error; inspect server log locally"}); raise

if __name__=='__main__':
    host='127.0.0.1'; port=int(os.getenv('PORT','8765'))
    provider='Gemini' if os.getenv('GEMINI_API_KEY') else 'OpenAI' if os.getenv('OPENAI_API_KEY') else 'none'
    print(f'EcoPulse at http://{host}:{port} | model provider: {provider}',flush=True)
    ThreadingHTTPServer((host,port),Handler).serve_forever()
