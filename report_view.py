"""Readable, printable executive decision record. Values are escaped and remain illustrative."""
from html import escape


def h(value):
    return escape(str(value if value is not None else "—"), quote=True)


def render(report):
    order = report["input_order"]
    selected = report.get("selected")
    approval = report.get("approval")
    state = ("Manager approved draft · not transmitted" if approval and approval["action"] == "approve"
             else "Manager rejected draft · revision requested" if approval else
             "Draft pending manager approval" if selected else "No eligible draft")
    original = {s["id"]:s for s in order["suppliers"]}
    rows = []
    for s in report["suppliers"]:
        raw = original.get(s["id"], {})
        issues = ", ".join(s["issues"]) or "Eligible"
        is_sel = selected and s["id"] == selected["id"]
        row_class = ' class="winner"' if is_sel else ""
        badge_class = "badge-good" if is_sel else ("badge-bad" if s["issues"] else "badge-neutral")
        rows.append(f'<tr{row_class}><td><strong>{h(s["name"])}</strong><br><small style="color:#64748b">{h(s["id"])}</small></td>'
                    f'<td>₹{h(s["quote_lakh"])} lakh</td>'
                    f'<td>{h(s["lead_days"])} days</td>'
                    f'<td>{h(s["emissions_t"])} tCO₂e<br><small style="color:#64748b">{h(s.get("carbon_intensity_kg_t"))} kgCO₂e/t (raw: {h(raw.get("emissions"))} {h(raw.get("emission_unit"))})</small></td>'
                    f'<td>{h(s["boundary"])}<br><small style="color:#64748b">{h(s["source"] or "No source")} · {h(s["evidence_date"] or "No date")}</small></td>'
                    f'<td><span class="{badge_class}">{h(issues)}</span></td></tr>')

    rules = "".join(f'<li><strong>{h(r["title"])}:</strong> <span class="{"badge-warn" if r["relevant"] else "badge-neutral"}">{"Flagged for expert review" if r["relevant"] else "Out of scope"}</span>. {h(r["note"])} <small style="color:#64748b">({h(r["source_url"])})</small></li>' for r in report["rules"])
    comparison = report.get("comparison")
    tradeoff = (f"<strong>Trade-off vs Baseline ({h(comparison['vs'])}):</strong> Quote delta ₹{h(comparison['quote_difference_lakh'])} lakh; "
                f"Scope 3 emissions avoided: {h(comparison['emission_difference_t'])} tCO₂e."
                if comparison else "No comparable baseline available.")
    chosen = (f'<h2 style="color:#091224;margin:6px 0 10px">{h(selected["name"])}</h2>'
              f'<div style="display:flex;gap:16px;flex-wrap:wrap;margin:12px 0">'
              f'<div class="kpi"><span>Total Quote</span><strong>₹{h(selected["quote_lakh"])} lakh</strong></div>'
              f'<div class="kpi"><span>Lead Delivery</span><strong>{h(selected["lead_days"])} days</strong></div>'
              f'<div class="kpi"><span>Scope 3 Footprint</span><strong>{h(selected["emissions_t"])} tCO₂e</strong></div>'
              f'<div class="kpi"><span>Planning Score</span><strong>₹{h(selected["planning_score_lakh"])} lakh</strong></div>'
              f'</div>'
              if selected else "<h2>Evidence or constraints need review</h2>")
    eligible = sum(s["commercial_ok"] and s["carbon_ok"] for s in report["suppliers"])
    evidenced = sum(s["carbon_ok"] for s in report["suppliers"])
    manager = (f'<strong style="color:#047857">{h(approval["action"]).title()}</strong> by simulated role <code>{h(approval["role"])}</code> at '
               f'<b>{h(approval["at"])}</b>.<br><strong>Rationale:</strong> <em>{h(approval["note"] or "No manager note provided")}</em>' if approval else
               "Manager approval action pending. No purchase order has been transmitted.")
    trace = " ➔ ".join(h(step["tool"]) for step in report.get("agent_trace", []))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EcoPulse Enterprise Decision Record — {h(report['decision_id'])}</title>
<style>
:root {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #0f172a;
  background: #f8fafc;
}}
* {{ box-sizing: border-box; }}
body {{
  max-width: 1040px;
  margin: 30px auto;
  padding: 0 24px;
  font-size: 13.5px;
  line-height: 1.55;
}}
header {{
  background: linear-gradient(135deg, #091224 0%, #101d36 100%);
  color: #ffffff;
  padding: 30px 32px;
  border-radius: 12px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.15);
}}
.header-sub {{
  color: #34d399;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 6px;
}}
header h1 {{
  margin: 4px 0 8px;
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.02em;
}}
.header-meta {{
  font-size: 12.5px;
  color: #94a3b8;
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
}}
.card {{
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 22px 26px;
  margin: 16px 0;
  box-shadow: 0 1px 3px rgba(15,23,42,0.05);
}}
.card h2 {{
  font-size: 16px;
  font-weight: 750;
  margin: 0 0 12px;
  color: #091224;
}}
.state {{
  font-weight: 800;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #059669;
  display: inline-block;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  padding: 4px 10px;
  border-radius: 6px;
  margin-bottom: 12px;
}}
.kpi {{
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 16px;
  min-width: 140px;
}}
.kpi span {{
  font-size: 11px;
  color: #64748b;
  text-transform: uppercase;
  font-weight: 600;
  display: block;
}}
.kpi strong {{
  font-size: 17px;
  font-weight: 800;
  color: #091224;
}}
.stat {{
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin: 10px 0;
}}
.stat span {{
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  font-weight: 700;
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 13px;
}}
table {{
  border-collapse: collapse;
  width: 100%;
  font-size: 12.5px;
  margin-top: 10px;
}}
th, td {{
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
  padding: 10px 12px;
  vertical-align: top;
}}
th {{
  background: #f8fafc;
  color: #475569;
  font-size: 11.5px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}
tr.winner {{
  background: #ecfdf5;
}}
.badge-good {{
  background: #ecfdf5;
  color: #065f46;
  border: 1px solid #a7f3d0;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}}
.badge-warn {{
  background: #fffbeb;
  color: #92400e;
  border: 1px solid #fde68a;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}}
.badge-bad {{
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}}
.badge-neutral {{
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}}
.fine {{
  font-size: 11.5px;
  color: #64748b;
  margin-top: 10px;
  line-height: 1.45;
}}
ul {{
  padding-left: 20px;
  margin: 8px 0;
}}
li {{
  margin: 6px 0;
}}
.print-bar {{
  margin: 16px 0;
  display: flex;
  justify-content: flex-end;
}}
button.print-btn {{
  background: #059669;
  color: #ffffff;
  border: 1px solid #047857;
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(4,120,87,0.3);
}}
button.print-btn:hover {{
  background: #047857;
}}
@media print {{
  body {{
    background: #ffffff;
    margin: 0;
    max-width: none;
    padding: 10px;
  }}
  .print-bar {{
    display: none;
  }}
  .card {{
    border: 1px solid #cbd5e1;
    box-shadow: none;
    break-inside: avoid;
  }}
  header {{
    background: #091224 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
}}
</style>
</head>
<body>
<div class="print-bar">
  <button class="print-btn" onclick="window.print()">Print or save as PDF</button>
</div>

<header>
  <div class="header-sub">EcoPulse Enterprise · CGI Manufacturing Accelerator · Official Decision Record</div>
  <h1>Sustainable Procurement Decision Audit</h1>
  <div class="header-meta">
    <span><b>Order ID:</b> {h(order['id'])} ({h(order['material'])})</span>
    <span><b>Decision ID:</b> {h(report['decision_id'])}</span>
    <span><b>Timestamp:</b> {h(report['created_at'])}</span>
  </div>
</header>

<section class="card">
  <div class="state">{h(state)}</div>
  {chosen}
  <p style="font-size:13.5px;margin:10px 0">{h(report['explanation'])}</p>
  <p>{tradeoff}</p>
  <p class="fine">Constraints Applied: Quote budget ₹{h(order['budget_lakh'])} lakh · Lead deadline {h(order['max_days'])} days · Carbon intensity ceiling {h(order.get('max_carbon_intensity_kg_t'))} kgCO₂e/t · Internal shadow carbon price ₹{h(order['internal_carbon_price_inr_t'])}/tCO₂e. Internal planning score is an evaluative index, not an invoice price.</p>
</section>

<section class="card">
  <h2>Compliance & Coverage Metrics</h2>
  <div class="stat">
    <span>✓ {evidenced}/{len(report['suppliers'])} Audited Carbon Footprints</span>
    <span>✓ {eligible} Fully Eligible Suppliers</span>
    <span>⚡ {h(report.get('run_seconds','—'))} s Agent Execution Time</span>
  </div>
  <p class="fine">Prototype evaluation cycle time excludes human confirmation and review stages. Realized organizational ROI is validated in client pilots.</p>
</section>

<section class="card">
  <h2>Supplier Evaluation Matrix</h2>
  <table>
    <thead>
      <tr>
        <th>Supplier</th>
        <th>Total Quote</th>
        <th>Lead Time</th>
        <th>Scope 3 Footprint</th>
        <th>LCA Boundary & Provenance</th>
        <th>Outcome</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</section>

<section class="card">
  <h2>Policy & Regulatory Scope Screening</h2>
  <ul>
    {rules}
  </ul>
  <p class="fine">Rule screening flags potential reporting triggers (e.g. EU CBAM Regulation). Legal liability and customs obligations require expert trade verification.</p>
</section>

<section class="card">
  <h2>Human Oversight & Manager Sign-Off</h2>
  <p>{manager}</p>
  <p class="fine">Enterprise role-based controls demonstrate workflow governance. Production implementations connect with corporate Identity Providers (Okta/Azure AD) and ERP release strategies.</p>
</section>

<section class="card">
  <h2>Audit Provenance & Tool Execution Trace</h2>
  <p style="font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12px;color:#334155">{trace}</p>
  <p class="fine">Execution Mode: <b>{h(report['mode'])}</b> · Input Fingerprint: <code>{h(report.get('input_fingerprint','—'))}</code>. Machine-readable audit payload available at <code>/api/record?id={h(report['decision_id'])}</code>.</p>
</section>

</body>
</html>"""
