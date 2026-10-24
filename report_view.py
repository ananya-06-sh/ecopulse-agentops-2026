"""Readable, printable decision record. Values are escaped and remain illustrative."""
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
        rows.append("<tr><td><strong>{name}</strong><br><small>{sid}</small></td><td>₹{quote} lakh</td>"
                    "<td>{lead} days</td><td>{normalized} tCO₂e<br><small>Input: {value} {unit}</small></td>"
                    "<td>{boundary}<br><small>{source} · {date}</small></td><td>{checks}</td></tr>".format(
                        name=h(s["name"]), sid=h(s["id"]), quote=h(s["quote_lakh"]), lead=h(s["lead_days"]),
                        normalized=h(s["emissions_t"]), value=h(raw.get("emissions")),unit=h(raw.get("emission_unit")),
                        boundary=h(s["boundary"]),source=h(s["source"] or "No source"),
                        date=h(s["evidence_date"] or "No date"),checks=h(issues)))
    rules = "".join("<li><strong>{title}:</strong> {status}. {note} <small>{source}</small></li>".format(
        title=h(r["title"]),status="Flagged for expert review" if r["relevant"] else "Out of scope",
        note=h(r["note"]),source=h(r["source_url"])) for r in report["rules"])
    comparison = report.get("comparison")
    tradeoff = (f"Against {h(comparison['vs'])}: quote change ₹{h(comparison['quote_difference_lakh'])} lakh; "
                f"reported emissions change {h(comparison['emission_difference_t'])} tCO₂e."
                if comparison else "No comparable baseline available.")
    chosen = (f"<h2>{h(selected['name'])}</h2><p>Quote <strong>₹{h(selected['quote_lakh'])} lakh</strong> · "
              f"Delivery <strong>{h(selected['lead_days'])} days</strong> · "
              f"Footprint <strong>{h(selected['emissions_t'])} tCO₂e</strong> · "
              f"Illustrative planning score <strong>₹{h(selected['planning_score_lakh'])} lakh</strong></p>"
              if selected else "<h2>Evidence or constraints need review</h2>")
    eligible = sum(s["commercial_ok"] and s["carbon_ok"] for s in report["suppliers"])
    evidenced = sum(s["carbon_ok"] for s in report["suppliers"])
    manager = (f"<strong>{h(approval['action']).title()}</strong> by demo role {h(approval['role'])} at "
               f"{h(approval['at'])}. Note: {h(approval['note'] or 'No note')}" if approval else
               "Manager action pending. No purchase order has been sent.")
    trace = " → ".join(h(step["tool"]) for step in report.get("agent_trace", []))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>EcoPulse decision {h(report['decision_id'])}</title><style>
    :root{{font-family:Arial,system-ui,sans-serif;color:#15352d}}*{{box-sizing:border-box}}body{{max-width:960px;margin:25px auto;padding:0 24px;background:#f5f8f5}}
    header{{background:#0e302b;color:white;padding:28px;border-radius:12px}}header small{{color:#bce5c8}}h1{{margin:6px 0;font-size:30px}}h2{{margin:8px 0}}.card{{background:white;border:1px solid #d9e6dc;border-radius:10px;padding:20px;margin:15px 0}}
    .state{{font-weight:700;color:#126347}}.fine{{font-size:13px;color:#597168}}.stat{{display:flex;gap:25px;flex-wrap:wrap}}.stat span{{background:#e7f3e9;padding:10px;border-radius:6px}}
    table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{text-align:left;border-bottom:1px solid #dfe9e1;padding:9px;vertical-align:top}}th{{background:#e8f1e8}}li{{margin:9px 0}}
    button{{border:0;background:#126347;color:white;border-radius:6px;padding:10px 14px;cursor:pointer}}@media print{{body{{background:white;margin:0;max-width:none}}button{{display:none}}.card{{break-inside:avoid}}}}
    </style></head><body><header><small>ECOPULSE ENTERPRISE · MANUFACTURING · SYNTHETIC SANDBOX</small><h1>Procurement decision record</h1>
    <div>Order {h(order['id'])} · Decision {h(report['decision_id'])} · {h(report['created_at'])}</div></header>
    <p><button onclick="window.print()">Print or save as PDF</button></p>
    <section class="card"><div class="state">{h(state)}</div>{chosen}<p>{h(report['explanation'])}</p><p>{tradeoff}</p>
    <p class="fine">Quote budget ₹{h(order['budget_lakh'])} lakh · Deadline {h(order['max_days'])} days · Internal carbon price ₹{h(order['internal_carbon_price_inr_t'])}/tCO₂e. The planning score is an internal comparison, not a purchase quote or tax.</p></section>
    <section class="card"><h2>Decision coverage</h2><div class="stat"><span>{evidenced}/{len(report['suppliers'])} comparable evidence</span><span>{eligible} eligible offers</span><span>{h(report.get('run_seconds','—'))} s evaluation time</span></div><p class="fine">Time saved and real emissions impact need a measured client pilot.</p></section>
    <section class="card"><h2>Supplier checks</h2><table><thead><tr><th>Supplier</th><th>Quote</th><th>Delivery</th><th>Footprint</th><th>Boundary and evidence</th><th>Outcome</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>
    <section class="card"><h2>Rule scope</h2><ul>{rules}</ul><p class="fine">Scope screening only. A specialist must verify legal applicability and obligations.</p></section>
    <section class="card"><h2>Manager decision</h2><p>{manager}</p><p class="fine">The role is a demo control, not secure authentication. No order is transmitted.</p></section>
    <section class="card"><h2>Audit trace</h2><p>{trace}</p><p class="fine">Mode: {h(report['mode'])} · Input fingerprint: {h(report.get('input_fingerprint','—'))}. The full machine-readable JSON remains available at /api/record?id={h(report['decision_id'])}.</p></section>
    </body></html>"""
