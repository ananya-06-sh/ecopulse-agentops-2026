# EcoPulse presentation and submission card

## 5-minute pitch

- **0:00–0:45 — Problem:** Manufacturing procurement teams must compare cost, lead time, and comparable emissions evidence when suppliers change their offers. A cheap quote can have missing evidence; an efficient supplier can miss the deadline.
- **0:45–1:30 — Agent:** Ingest → validate → screen relevant rules → normalize evidence → rank offers → draft PO → manager decision → outcome and audit. Gemini calls tools and can extract fields from messy supplier text; deterministic checks own the math and hard constraints.
- **1:30–2:30 — Scenario:** 100 t steel, ₹64 lakh budget, 16 days. GreenForge initially 18 days, then updates to 14. It becomes eligible; 90 tCO₂e lower than Ironcrest at ₹2.5 lakh quote premium. Planning score uses illustrative internal ₹4,000/tCO₂e, not a tax.
- **2:30–3:30 — Differentiation:** Paste the sample supplier note, show Gemini's draft extraction and human confirmation. Then show missing footprints, kg→t conversion, boundary mismatch, second aluminium order and EU-import scope flag.
- **3:30–4:15 — Governance:** Evidence source/date, assumptions, rule relevance, persistent local decision record and human approval. Clearly identify demo-only role and synthetic feeds.
- **4:15–5:00 — ROI and reuse:** Show measured scenario trade-offs, then propose a pilot measuring time per decision, evidence completeness, cost, and verified emissions over many purchase orders. Same workflow extends across plants/materials.

## 5-minute demo

Follow README's five steps. Keep model key tested and ready before the event. If API access fails, openly label **rules preview** and show the deterministic engine; do not call it an LLM run. Record a clean screen capture after confirming the live workflow.

## Q&A answers

- **Are these real supplier feeds?** No, synthetic offers with provenance fields. Production integrations would ingest ERP and supplier EPDs and validate them.
- **Is ₹4,000 a carbon tax?** No. It is an explicitly labeled internal scenario price. EU CBAM is only flagged for expert review when material and destination match.
- **Why agentic if arithmetic is simple?** The value is choosing tools, handling changing/messy evidence and exceptions, and routing a documented draft through approval. Hard constraints and arithmetic remain deterministic.
- **Is the approval secure?** This prototype demonstrates workflow, not secure RBAC. SQLite persists local events but is not tamper-evident. Production requires identity, authorization, tamper-evident audit, and ERP integration.
- **How does it generalize?** Edit orders and suppliers in the UI, use the aluminium second case, and inspect the same pipeline. No recommendation is hardcoded to a specific supplier.

## Deadline checklist

- [ ] Confirm portal link and upload limits from official group.
- [ ] Test live model API and backup rules preview on event laptop.
- [ ] Push accessible GitHub repo containing code and README.
- [ ] Copy **final commit SHA** from `git rev-parse HEAD` after final commit/push.
- [ ] Export final 5-minute PPT/PPTX and record demo video.
- [ ] Upload all four items before **18:00 IST, 24 Oct**; no further changes after cutoff.
- [ ] Be ready for review from 15:00 and, if selected, in-person CGI finals on 27 Oct.
