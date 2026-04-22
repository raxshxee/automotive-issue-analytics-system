import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path("data")
COMPLAINTS_PATH = OUTPUT_DIR / "raw_complaints.csv"
RECALLS_PATH = OUTPUT_DIR / "raw_recalls.csv"

VEHICLES = [
    {"make": "Toyota", "model": "Camry", "model_year": 2021, "segment": "Midsize sedan"},
    {"make": "Toyota", "model": "Camry", "model_year": 2022, "segment": "Midsize sedan"},
    {"make": "Honda", "model": "Civic", "model_year": 2021, "segment": "Compact sedan"},
    {"make": "Honda", "model": "Civic", "model_year": 2022, "segment": "Compact sedan"},
    {"make": "Chevrolet", "model": "Silverado 1500", "model_year": 2021, "segment": "Pickup truck"},
    {"make": "Chevrolet", "model": "Silverado 1500", "model_year": 2022, "segment": "Pickup truck"},
    {"make": "Tesla", "model": "Model 3", "model_year": 2021, "segment": "Electric sedan"},
    {"make": "Tesla", "model": "Model 3", "model_year": 2022, "segment": "Electric sedan"},
    {"make": "Hyundai", "model": "Tucson", "model_year": 2021, "segment": "Compact SUV"},
    {"make": "Hyundai", "model": "Tucson", "model_year": 2022, "segment": "Compact SUV"},
]

def fetch_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "RecallReadyPortfolio/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def vehicle_query(vehicle):
    return urllib.parse.urlencode({"make": vehicle["make"], "model": vehicle["model"], "modelYear": vehicle["model_year"]})

def fetch_complaints(vehicle):
    url = f"https://api.nhtsa.gov/complaints/complaintsByVehicle?{vehicle_query(vehicle)}"
    payload = fetch_json(url)
    results = payload.get("results") or payload.get("Results") or []
    rows = []
    for item in results:
        row = {str(k).lower(): v for k, v in item.items()}
        rows.append({
            "make": vehicle["make"], "model": vehicle["model"], "model_year": vehicle["model_year"],
            "segment": vehicle["segment"], "source_type": "complaint",
            "nhtsa_id": row.get("odi_number") or row.get("odi_id") or row.get("id") or "",
            "date_received": row.get("date_received") or row.get("dateofincident") or "",
            "component": row.get("components") or row.get("component") or "",
            "summary": row.get("summary") or row.get("description") or "",
            "crash": row.get("crash") or "", "fire": row.get("fire") or "",
            "injury_count": row.get("number_of_injuries") or row.get("injuries") or "0",
            "death_count": row.get("number_of_deaths") or row.get("deaths") or "0",
            "raw_json": json.dumps(item, ensure_ascii=False),
        })
    return rows

def fetch_recalls(vehicle):
    url = f"https://api.nhtsa.gov/recalls/recallsByVehicle?{vehicle_query(vehicle)}"
    payload = fetch_json(url)
    results = payload.get("results") or payload.get("Results") or []
    rows = []
    for item in results:
        row = {str(k).lower(): v for k, v in item.items()}
        rows.append({
            "make": vehicle["make"], "model": vehicle["model"], "model_year": vehicle["model_year"],
            "segment": vehicle["segment"], "source_type": "recall",
            "nhtsa_campaign_number": row.get("nhtsacampaignnumber") or row.get("campaignnumber") or "",
            "report_received_date": row.get("reportreceiveddate") or "",
            "component": row.get("component") or "", "summary": row.get("summary") or "",
            "consequence": row.get("consequence") or "", "remedy": row.get("remedy") or "",
            "manufacturer": row.get("manufacturer") or "", "raw_json": json.dumps(item, ensure_ascii=False),
        })
    return rows

def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    all_complaints = []
    all_recalls = []
    for vehicle in VEHICLES:
        label = f"{vehicle['model_year']} {vehicle['make']} {vehicle['model']}"
        print(f"Collecting {label}")
        try:
            complaints = fetch_complaints(vehicle)
        except Exception as exc:
            print(f"  complaint fetch failed: {exc}")
            complaints = []
        try:
            recalls = fetch_recalls(vehicle)
        except Exception as exc:
            print(f"  recall fetch failed: {exc}")
            recalls = []
        print(f"  complaints: {len(complaints)} | recalls: {len(recalls)}")
        all_complaints.extend(complaints)
        all_recalls.extend(recalls)
        time.sleep(0.25)
    write_csv(COMPLAINTS_PATH, all_complaints, ["make", "model", "model_year", "segment", "source_type", "nhtsa_id", "date_received", "component", "summary", "crash", "fire", "injury_count", "death_count", "raw_json"])
    write_csv(RECALLS_PATH, all_recalls, ["make", "model", "model_year", "segment", "source_type", "nhtsa_campaign_number", "report_received_date", "component", "summary", "consequence", "remedy", "manufacturer", "raw_json"])
    print(f"Wrote {len(all_complaints)} complaints to {COMPLAINTS_PATH}")
    print(f"Wrote {len(all_recalls)} recalls to {RECALLS_PATH}")

if __name__ == "__main__":
    main()


