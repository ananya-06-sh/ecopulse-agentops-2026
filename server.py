"""Dependency-free local demo server. Run on localhost; never expose to a public network."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json
import os
from datetime import datetime, timezone
from agent import run

ROOT=Path(__file__).resolve().parent
FIXTURES=json.loads((ROOT/'data/scenarios.json').read_text(encoding='utf-8'))
DECISIONS={}
AUDIT=[]

def record(event, detail):
    AUDIT.append({"at":datetime.now(timezone.utc).isoformat(),"event":event,"detail":detail})
    del AUDIT[:-100]

class Handler(BaseHTTPRequestHandler):
    def send(self, status, data, mime='application/json'):
        raw=(json.dumps(data,ensure_ascii=False) if mime=='application/json' else data).encode()
        self.send_response(status); self.send_header('Content-Type',mime+'; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path=='/': return self.send(200,(ROOT/'index.html').read_text(encoding='utf-8'),'text/html')
        if self.path=='/api/fixtures': return self.send(200,FIXTURES)
        if self.path=='/api/audit': return self.send(200,AUDIT)
        self.send(404,{"error":"Not found"})
    def do_POST(self):
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size>100000: return self.send(413,{"error":"Request too large"})
            body=json.loads(self.rfile.read(size))
            if self.path=='/api/evaluate':
                report=run(body['order'],bool(body.get('use_model',True)))
                DECISIONS[report['decision_id']]=report
                record('evaluation',{'decision_id':report['decision_id'],'order_id':body['order']['id'],'mode':report['mode'],'status':report['status']})
                return self.send(200,report)
            if self.path=='/api/decision':
                did=body.get('decision_id'); report=DECISIONS.get(did)
                if not report: return self.send(404,{"error":"Evaluate the current order first"})
                if body.get('role')!='procurement_manager': return self.send(403,{"error":"Demo role must be procurement_manager. This is not production authentication."})
                if body.get('action') not in ('approve','reject'): return self.send(400,{"error":"Action must be approve or reject"})
                if body['action']=='approve' and not report['draft_po']: return self.send(409,{"error":"No eligible draft to approve"})
                if report.get('approval'): return self.send(409,{"error":"Decision already recorded"})
                report['approval']={'action':body['action'],'role':body['role'],'at':datetime.now(timezone.utc).isoformat(),'note':str(body.get('note',''))[:300]}
                record('human_decision',{'decision_id':did,**report['approval']})
                return self.send(200,report['approval'])
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
