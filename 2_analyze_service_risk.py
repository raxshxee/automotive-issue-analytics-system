import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

DATA_DIR = Path("data")
COMPLAINTS_PATH = DATA_DIR / "raw_complaints.csv"
RECALLS_PATH = DATA_DIR / "raw_recalls.csv"
ENRICHED_PATH = DATA_DIR / "enriched_vehicle_issues.csv"
QUEUE_PATH = DATA_DIR / "service_priority_queue.csv"
PROOF_XLSX_PATH = DATA_DIR / "recallready_evidence_log.xlsx"
SUMMARY_PATH = DATA_DIR / "summary.json"
DASHBOARD_TEMPLATE_PATH = Path("dashboard_template.html")
DASHBOARD_PATH = Path("dashboard.html")

COMPONENT_OWNERS = {
    "AIR BAGS": "Safety & Compliance",
    "SERVICE BRAKES": "Dealer Service + Product Quality",
    "STEERING": "Dealer Service + Product Quality",
    "ENGINE": "Product Quality",
    "POWER TRAIN": "Product Quality",
    "ELECTRICAL SYSTEM": "Product Quality + Dealer Service",
    "SEAT BELTS": "Safety & Compliance",
    "FUEL": "Safety & Compliance + Parts Planning",
    "WHEELS": "Dealer Service",
    "TIRES": "Dealer Service + Parts Planning",
    "UNKNOWN": "Customer Support Intake",
}

CRITICAL_WORDS = ["crash", "fire", "injury", "death", "stall", "brake", "airbag", "air bag", "steering", "loss of power", "fuel leak", "seat belt"]
SERVICE_WORDS = ["dealer", "repair", "replace", "service", "appointment", "part", "parts", "warranty", "backorder", "software update"]


def clean(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def primary_component(component):
    text = clean(component).upper()
    if not text:
        return "UNKNOWN"
    first = re.split(r"[,;/]", text)[0].strip()
    return first or "UNKNOWN"


def yes(value):
    return str(value).strip().upper() in {"Y", "YES", "TRUE", "1"}


def number(value):
    try:
        return int(float(value))
    except Exception:
        return 0


def severity_score(row, recall_overlap):
    text = f"{row.get('summary', '')} {row.get('consequence', '')}".lower()
    score = 20
    if row["source_type"] == "recall":
        score += 25
    if recall_overlap:
        score += 20
    if yes(row.get("crash")):
        score += 20
    if yes(row.get("fire")):
        score += 20
    if number(row.get("injury_count")) > 0:
        score += 25
    if number(row.get("death_count")) > 0:
        score += 35
    score += min(20, sum(word in text for word in CRITICAL_WORDS) * 5)
    return min(100, score)


def priority(score):
    if score >= 75:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


def owner_for(component):
    upper = component.upper()
    for key, owner in COMPONENT_OWNERS.items():
        if key in upper:
            return owner
    return "Customer Support Intake"


def action_for(priority_level, component, recall_overlap, source_type):
    if priority_level == "High" and recall_overlap:
        return "Open 24-hour service action review; confirm customer messaging, dealer readiness, and repair/parts path."
    if priority_level == "High":
        return "Escalate to product quality and service operations for pattern review within 24 hours."
    if priority_level == "Medium" and source_type == "recall":
        return "Monitor remedy readiness and prepare dealer/customer support talking points."
    if priority_level == "Medium":
        return "Track trend weekly and create support macro or service bulletin candidate if volume grows."
    return "Log for trend monitoring; route to standard customer support/service workflow."


def sla_for(priority_level):
    return {"High": "24 hours", "Medium": "3 business days", "Low": "7 business days"}[priority_level]


def service_theme(text, component):
    haystack = f"{text} {component}".lower()
    if any(w in haystack for w in ["brake", "steering", "airbag", "air bag", "seat belt", "crash"]):
        return "Safety-critical control issue"
    if any(w in haystack for w in ["engine", "stall", "power train", "loss of power", "transmission"]):
        return "Driveability / power issue"
    if any(w in haystack for w in ["battery", "electrical", "screen", "software", "camera", "warning light"]):
        return "Electrical / software issue"
    if any(w in haystack for w in ["dealer", "repair", "replace", "parts", "warranty", "service"]):
        return "Service experience issue"
    return "General vehicle issue"


def build_records(complaints, recalls):
    recall_keys = set(zip(recalls["make"], recalls["model"], recalls["model_year"], recalls["component_primary"]))
    records = []
    for _, row in pd.concat([complaints, recalls], ignore_index=True).iterrows():
        component = row["component_primary"]
        key = (row["make"], row["model"], row["model_year"], component)
        overlap = key in recall_keys and row["source_type"] == "complaint"
        score = severity_score(row, overlap)
        priority_level = priority(score)
        text = clean(row.get("summary", ""))
        records.append({
            "make": row["make"],
            "model": row["model"],
            "model_year": int(row["model_year"]),
            "vehicle": f"{int(row['model_year'])} {row['make']} {row['model']}",
            "segment": row["segment"],
            "source_type": row["source_type"],
            "component": component,
            "service_theme": service_theme(text, component),
            "summary": text[:600],
            "recall_overlap": bool(overlap),
            "priority_score": score,
            "priority": priority_level,
            "suggested_owner": owner_for(component),
            "recommended_action": action_for(priority_level, component, overlap, row["source_type"]),
            "sla": sla_for(priority_level),
            "crash": clean(row.get("crash", "")),
            "fire": clean(row.get("fire", "")),
            "injury_count": number(row.get("injury_count")),
            "death_count": number(row.get("death_count")),
        })
    return pd.DataFrame(records)


def count_dict(series):
    return {str(k): int(v) for k, v in Counter(series).most_common()}


def build_queue(enriched):
    grouped = enriched.groupby(["vehicle", "make", "model", "model_year", "component", "service_theme", "suggested_owner"], dropna=False)
    rows = []
    for keys, group in grouped:
        vehicle, make, model, model_year, component, theme, owner = keys
        complaints = int((group["source_type"] == "complaint").sum())
        recalls = int((group["source_type"] == "recall").sum())
        max_score = int(group["priority_score"].max())
        score = min(100, max_score + min(15, complaints // 5) + min(10, recalls * 5))
        priority_level = priority(score)
        rows.append({
            "vehicle": vehicle,
            "make": make,
            "model": model,
            "model_year": int(model_year),
            "component": component,
            "service_theme": theme,
            "complaint_count": complaints,
            "recall_count": recalls,
            "priority_score": score,
            "priority": priority_level,
            "suggested_owner": owner,
            "sla": sla_for(priority_level),
            "recommended_action": action_for(priority_level, component, recalls > 0, "complaint"),
            "evidence_sample": group["summary"].dropna().astype(str).head(1).iloc[0] if len(group) else "",
        })
    return pd.DataFrame(rows).sort_values(["priority_score", "complaint_count"], ascending=False)


def write_outputs(enriched, queue):
    enriched.to_csv(ENRICHED_PATH, index=False, encoding="utf-8")
    queue.to_csv(QUEUE_PATH, index=False, encoding="utf-8")
    with pd.ExcelWriter(PROOF_XLSX_PATH) as writer:
        enriched[["vehicle", "source_type", "component", "service_theme", "priority", "priority_score", "suggested_owner", "summary"]].to_excel(writer, sheet_name="issue_evidence", index=False)
        queue.to_excel(writer, sheet_name="priority_queue", index=False)


def build_summary(enriched, queue):
    high_queue = queue[queue["priority"] == "High"]
    summary = {
        "project": "RecallReady Intelligence",
        "total_records": int(len(enriched)),
        "complaint_records": int((enriched["source_type"] == "complaint").sum()),
        "recall_records": int((enriched["source_type"] == "recall").sum()),
        "vehicles_analyzed": int(enriched["vehicle"].nunique()),
        "high_priority_queue_items": int(len(high_queue)),
        "priority_counts": count_dict(queue["priority"]),
        "component_counts": count_dict(enriched["component"]),
        "theme_counts": count_dict(enriched["service_theme"]),
        "owner_counts": count_dict(queue["suggested_owner"]),
        "vehicle_counts": count_dict(enriched["vehicle"]),
        "queue": queue.head(50).to_dict(orient="records"),
        "evidence": enriched.sort_values(["priority_score"], ascending=False).head(40).to_dict(orient="records"),
        "requirements": [
            "The system must ingest public complaint and recall records by vehicle make, model, and year.",
            "The system must classify issues by component and service theme.",
            "The system must calculate a priority score using severity indicators, recall overlap, and issue volume.",
            "The system must assign a suggested owner team and SLA for each priority queue item.",
            "The dashboard must allow filtering by make, vehicle, component, priority, and owner.",
        ],
        "user_stories": [
            "As a service operations manager, I want to see high-priority issue clusters so that I can decide what needs review first.",
            "As a dealer service lead, I want owner and SLA guidance so that my team knows how quickly to respond.",
            "As a product quality analyst, I want complaint and recall overlap indicators so that recurring issues can be investigated earlier.",
            "As a customer support lead, I want clear routing rules so that urgent vehicle issues are not handled like routine tickets.",
        ],
        "uat_cases": [
            "Filter by High priority and verify that only high-priority queue items appear.",
            "Select a vehicle and confirm KPI cards, component charts, and queue rows update together.",
            "Open an issue with recall overlap and verify the suggested action includes service action review.",
            "Check that every queue item has a suggested owner, SLA, and recommended action.",
        ],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main():
    if not COMPLAINTS_PATH.exists() or not RECALLS_PATH.exists():
        raise FileNotFoundError("Run scripts/1_collect_nhtsa_data.py first.")
    complaints = pd.read_csv(COMPLAINTS_PATH).fillna("")
    recalls = pd.read_csv(RECALLS_PATH).fillna("")
    complaints["component_primary"] = complaints["component"].apply(primary_component)
    recalls["component_primary"] = recalls["component"].apply(primary_component)
    enriched = build_records(complaints, recalls)
    queue = build_queue(enriched)
    write_outputs(enriched, queue)
    summary = build_summary(enriched, queue)
    template = DASHBOARD_TEMPLATE_PATH.read_text(encoding="utf-8")
    DASHBOARD_PATH.write_text(template.replace("__DATA_JSON__", json.dumps(summary, ensure_ascii=False)), encoding="utf-8")
    print(f"Wrote {ENRICHED_PATH}")
    print(f"Wrote {QUEUE_PATH}")
    print(f"Wrote {PROOF_XLSX_PATH}")
    print(f"Wrote {SUMMARY_PATH}")
    print(f"Wrote {DASHBOARD_PATH}")

if __name__ == "__main__":
    main()
