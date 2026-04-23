# Automotive Issue Analytics System

Search-first business analysis project built on real NHTSA vehicle complaint and recall data.

## Overview

The project analyzes recurring vehicle issues across selected 2021-2022 models, classifies complaint language into functional-impact signals, and converts the results into an action queue with owner routing, SLA logic, and evidence review.

## Dataset

- 4,214 combined complaint and recall records
- 4,152 complaint records
- 62 recall records
- 10 vehicle make/model/year combinations

Vehicles included:

- Toyota Camry
- Honda Civic
- Chevrolet Silverado 1500
- Tesla Model 3
- Hyundai Tucson


## Data Sources

- NHTSA Complaints API
- NHTSA Recalls API

## Run

```bash
python -m pip install -r requirements.txt
python scripts/1_collect_nhtsa_data.py
python scripts/2_analyze_service_risk.py
```

Open `dashboard.html` in a browser.

```bash
python -m pip install -r requirements.txt
python scripts/1_collect_nhtsa_data.py
python scripts/2_analyze_service_risk.py
