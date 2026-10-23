# EcoPulse Enterprise — AgentOps 2026 MVP

A local procurement decision agent for **Manufacturing**. It ingests an order and supplier offers, checks delivery/price and carbon evidence, screens rule relevance, ranks comparable offers, drafts a purchase order, and records a human decision. **All supplied quotes and footprints are synthetic.** The internal carbon price is a planning assumption, not a tax or predicted fine.

## Run in under two minutes

Requires Python 3.10+; no Python packages to install.

```bash
cd ecopulse-mvp
python server.py
```

Open <http://127.0.0.1:8765>. On Ananya's Windows laptop, run `& "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe" server.py` from PowerShell in the extracted `ecopulse-mvp` folder. Select a scenario, edit supplier rows, and click **Run agent**. Without an API key the app labels itself **rules preview** and runs real deterministic validation/ranking without claiming an LLM call.

For actual model-directed tool calls, set your own OpenAI API key *locally* before launching:

```bash
export OPENAI_API_KEY='your-key-here' # macOS/Linux; do not commit it
export OPENAI_MODEL='gpt-4o-mini'     # optional; use a model available to your account
python server.py
```

An API account with credits and network access is required. The key is read on the server and never embedded in the webpage. This local prototype has no secure user authentication; only run it on localhost with synthetic or appropriately sanitized data. No live ERP, supplier, purchase-order, or legal feed is connected.

**Free-tier alternative:** EcoPulse also supports the Gemini Developer API. Create a key at [Google AI Studio](https://aistudio.google.com/app/apikey), then set `GEMINI_API_KEY` in your terminal. The default is `gemini-3.5-flash-lite` and Google lists a limited free tier; availability and rate limits depend on your account/region. If both keys are present, Gemini is selected. In PowerShell, use `$env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'Paste Gemini key' -AsSecureString)).Password` before starting the server. Never put a key in the repository or a screen recording. With either provider, inspect the displayed mode to confirm real tool calls.

## Five-minute live demo

1. **Before update:** STEEL-101: GreenForge has 18-day lead, misses the 16-day deadline; Ironcrest is selected. SwiftSteel has no footprint and is excluded from carbon ranking.
2. **Agent action:** Click **Apply live update**; GreenForge changes to 14 days. Rerun. It is selected with 90 tCO₂e less than Ironcrest for ₹2.5 lakh more. Internal planning score: GreenForge ₹68.5 lakh vs Ironcrest ₹69.6 lakh. Show model tool trace if configured.
3. **Messy data:** Change GreenForge's boundary to `gate-to-gate`, rerun, and show why its low footprint cannot be compared. Restore or switch scenarios.
4. **Second case:** AL-204 converts Nova's `520000 kgCO2e` to `520 tCO₂e`, excludes ReLoop's boundary mismatch, and flags potential EU CBAM scope for expert review. CircularMet is eligible and selected. The steel/India order does **not** flag EU CBAM.
5. **Human control:** Show draft, manager approve/reject, audit record. It never sends a purchase order.

## Architecture and governance

`index.html` is the local dashboard. `server.py` exposes the HTTP endpoints. `agent.py` asks Gemini or OpenAI to call four tools in a dependent loop when a key is present; every tool result is shown in the trace. `core.py` validates data, converts units, checks evidence date/source/boundary, screens a small sourced rule catalog, and ranks eligible offers. The final decision is recomputed by deterministic code, so model prose cannot override arithmetic. Approval is a local role demonstration, **not** production RBAC or authentication. The audit log is in memory and resets on restart. A deployed system would need real identity, persistent append-only audit, verified supplier feeds, policy versioning, and ERP approval integrations.

### API

- `GET /api/fixtures` — synthetic scenarios.
- `POST /api/evaluate` — `{"order": <scenario object>, "use_model": true}`; returns decision, evidence, rule screen, model mode, tool trace.
- `POST /api/decision` — `{"decision_id":"...","role":"procurement_manager","action":"approve","note":"..."}` or `reject`. Local approval only.
- `GET /api/audit` — in-memory event trace.

## Test

```bash
python -m unittest discover -s tests -v
```

The six tests cover reranking on updated lead time, unit normalization, scope checks, incompatible boundaries, missing evidence, duplicate IDs, and keeping an incorrect model rationale out of the displayed summary. Tests use no API credits.

## Impact and expansion

For the synthetic steel order, the recommendation shifts from 240 to 150 tCO₂e after the delivery update. The quote premium is ₹2.5 lakh; 90 tCO₂e is a **scenario comparison**, not verified abatement. Reuse the same workflow for multiple materials, sites, suppliers, and rule cards. A production pilot would measure decision time, evidence completeness, exceptions, realized purchase cost, and verified emissions versus a baseline over many orders.

## Hackathon handoff

Domain: Manufacturing. Team: EcoPulse (HX-4PTE), Ananya Shenoy M. Complete repository upload, final commit SHA, final PPT/PPTX, and demo video **before 6:00 PM IST on 24 October**. The portal details will arrive separately. Keep the submitted commit and files frozen after the deadline. Selected CGI finalists pitch in person on 27 October at 10:00 AM.
