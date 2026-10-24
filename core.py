"""Auditable procurement calculations. All prices and footprints in fixtures are illustrative."""
from datetime import date
from decimal import Decimal, InvalidOperation
import copy
import hashlib
import json
from pathlib import Path

RULES = json.loads((Path(__file__).resolve().parent / "data" / "rules.json").read_text(encoding="utf-8"))

def number(v, label):
    try:
        d = Decimal(str(v))
        if not d.is_finite() or d < 0: raise ValueError()
        return d
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Invalid non-negative {label}")

def tool_validate_order(order):
    if not isinstance(order, dict) or not isinstance(order.get("suppliers"), list): raise ValueError("Order and supplier list required")
    if not order.get("id") or not order.get("material") or not order.get("suppliers"): raise ValueError("Order ID, material, and suppliers required")
    for field in ("quantity_t","max_days","budget_lakh","internal_carbon_price_inr_t"):
        number(order.get(field), field)
    if order.get("max_carbon_intensity_kg_t") not in (None, ""):
        number(order["max_carbon_intensity_kg_t"], "carbon intensity limit")
    if number(order["quantity_t"],"quantity") == 0: raise ValueError("Quantity must exceed zero")
    ids = [str(s.get("id", "")) for s in order["suppliers"]]
    if any(not i for i in ids) or len(set(ids)) != len(ids): raise ValueError("Supplier IDs must be unique and present")
    return {"order_id":order["id"],"supplier_count":len(ids),"required_boundary":order.get("required_boundary","cradle-to-gate")}

def tool_screen_rules(order):
    return [{"id":r["id"],"title":r["title"],"relevant":str(order.get("material","")).lower() in r["materials"] and (r["destination"] == "any" or str(order.get("destination","")).upper() == r["destination"]),"reason":f"material={order.get('material')}; destination={order.get('destination')}; scope={r['materials']}→{r['destination']}","source_url":r["source_url"],"note":r["note"]} for r in RULES]

def tool_normalize_and_check(order):
    rows=[]
    quantity=number(order["quantity_t"],"quantity")
    carbon_limit=(number(order["max_carbon_intensity_kg_t"],"carbon intensity limit")
                  if order.get("max_carbon_intensity_kg_t") not in (None, "") else None)
    for s in order["suppliers"]:
        issues=[]; emissions_t=None
        q=number(s.get("quote_lakh"),"supplier quote")
        lead=number(s.get("lead_days"),"supplier lead time")
        if q > number(order["budget_lakh"],"budget"): issues.append("Over quote budget")
        if lead > number(order["max_days"],"deadline"): issues.append("Misses delivery deadline")
        raw=s.get("emissions")
        if raw is None or raw == "": issues.append("Missing emissions evidence")
        else:
            e=number(raw,"emissions")
            if s.get("emission_unit") == "kgCO2e": emissions_t=e/Decimal(1000)
            elif s.get("emission_unit") == "tCO2e": emissions_t=e
            else: issues.append("Unknown emissions unit")
            if not s.get("source"): issues.append("Missing source reference")
            try:
                age=(date.today()-date.fromisoformat(s.get("evidence_date",""))).days
                if age < 0 or age > 365: issues.append("Emission evidence outside valid date window")
            except ValueError: issues.append("Missing or invalid evidence date")
            if s.get("boundary") != order.get("required_boundary","cradle-to-gate"): issues.append("Incomparable footprint boundary")
            if emissions_t is not None and carbon_limit is not None and emissions_t*Decimal(1000)/quantity > carbon_limit:
                issues.append("Exceeds carbon intensity limit")
        commercial_ok=not any(i in issues for i in ("Over quote budget","Misses delivery deadline"))
        carbon_ok=emissions_t is not None and not any(i in issues for i in ("Missing emissions evidence","Unknown emissions unit","Missing source reference","Emission evidence outside valid date window","Missing or invalid evidence date","Incomparable footprint boundary","Exceeds carbon intensity limit"))
        score=q+emissions_t*number(order["internal_carbon_price_inr_t"],"carbon price")/Decimal(100000) if carbon_ok else None
        rows.append({"id":s["id"],"name":s.get("name",s["id"]),"quote_lakh":float(q),"lead_days":float(lead),"emissions_t":float(emissions_t) if emissions_t is not None else None,"carbon_intensity_kg_t":round(float(emissions_t*Decimal(1000)/quantity),2) if emissions_t is not None else None,"boundary":s.get("boundary"),"source":s.get("source"),"evidence_date":s.get("evidence_date"),"ship_from":s.get("ship_from"),"commercial_ok":commercial_ok,"carbon_ok":carbon_ok,"issues":issues,"planning_score_lakh":round(float(score),2) if score is not None else None})
    return rows

def tool_rank_and_draft(order, rows, rules):
    eligible=[r for r in rows if r["commercial_ok"] and r["carbon_ok"]]
    eligible.sort(key=lambda r:(r["planning_score_lakh"],r["quote_lakh"],r["id"]))
    selected=eligible[0] if eligible else None
    baseline=next((r for r in rows if r["id"]==order.get("baseline_supplier_id")), None) or next((r for r in rows if r["id"]==order["suppliers"][0]["id"]),None)
    delta=None
    if selected and baseline and baseline["emissions_t"] is not None and baseline["carbon_ok"]:
        delta={"vs":baseline["name"],"quote_difference_lakh":round(selected["quote_lakh"]-baseline["quote_lakh"],2),"emission_difference_t":round(selected["emissions_t"]-baseline["emissions_t"],2)}
    relevant=[r["title"] for r in rules if r["relevant"]]
    return {"status":"draft_pending_approval" if selected else "needs_evidence","selected":selected,"ranked_ids":[r["id"] for r in eligible],"comparison":delta,"rule_flags":relevant,"draft_po":{"order_id":order["id"],"supplier_id":selected["id"],"material":order["material"],"quantity_t":order["quantity_t"],"quote_lakh":selected["quote_lakh"],"status":"DRAFT — manager approval required"} if selected else None,"explanation":(f"{selected['name']} meets the budget and deadline with comparable, cited emissions evidence; lowest illustrative planning score among eligible offers." if selected else "No offer passes commercial and comparable-emissions checks. Request evidence or revise the order before creating a draft.")}

def evaluate(order):
    order=copy.deepcopy(order)
    validation=tool_validate_order(order)
    rules=tool_screen_rules(order)
    rows=tool_normalize_and_check(order)
    result=tool_rank_and_draft(order,rows,rules)
    result.update({"validation":validation,"rules":rules,"suppliers":rows,"assumptions":{"internal_carbon_price_inr_t":order["internal_carbon_price_inr_t"],"currency":"INR; quotes in lakh","data":"synthetic supplier offers; not live tax or supplier feeds"}})
    result["decision_id"]=hashlib.sha256(json.dumps(order,sort_keys=True).encode()).hexdigest()[:12]
    return result
