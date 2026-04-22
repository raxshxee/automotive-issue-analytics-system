# Automotive Issue Analytics System

Automotive risk intelligence project built using public vehicle complaint and recall data.

This project analyzes complaint and recall records to identify recurring issue patterns, prioritize service actions, and turn raw operational data into decision-ready insights through an interactive dashboard.

```md id="krv5di"
Note: Dashboard UI is actively being refined; current version reflects the core analytics engine and workflow.
```

## Data Source

Public NHTSA complaint and recall datasets.

## Project Outputs

- `dashboard.html` – Interactive dashboard  
- `summary.json` – Aggregated metrics  
- `service_priority_queue.csv` – Prioritized issue queue  
- Python scripts for data collection and analysis  
- Business analysis documentation  

## Dashboard Features

- KPI overview  
- Complaint trend analysis  
- Recall intelligence  
- Service priority queue  
- Risk segmentation  
- Decision support views  


## How to Run

```bash
python -m pip install -r requirements.txt
python scripts/1_collect_nhtsa_data.py
python scripts/2_analyze_service_risk.py
