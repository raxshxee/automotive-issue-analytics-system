# Requirements, User Stories, and UAT

## Business Requirements

1. The system must ingest public complaint and recall records by vehicle make, model, and year.
2. The system must classify issues by component and service theme.
3. The system must calculate a priority score using severity indicators, recall overlap, and issue volume.
4. The system must assign a suggested owner team and SLA for each priority queue item.
5. The dashboard must allow filtering by make, vehicle, component, priority, and owner.
6. The dashboard must show evidence excerpts behind high-priority items.
7. The output must include a compact evidence workbook for auditability.

## User Stories

- As a service operations manager, I want to see high-priority issue clusters so that I can decide what needs review first.
- As a dealer service lead, I want owner and SLA guidance so that my team knows how quickly to respond.
- As a product quality analyst, I want complaint and recall overlap indicators so that recurring issues can be investigated earlier.
- As a customer support lead, I want clear routing rules so that urgent vehicle issues are not handled like routine tickets.
- As an executive sponsor, I want a high-level view of issue volume and priority mix so that I can understand operational exposure.

## UAT Scenarios

| Test Case | Steps | Expected Result |
|---|---|---|
| Filter high-priority items | Open dashboard, select Priority = High | Only high-priority queue items appear |
| Filter by vehicle | Select one vehicle from Vehicle filter | KPI cards, charts, and queue update together |
| Verify owner routing | Open queue rows | Every row has owner, SLA, and recommended action |
| Validate recall overlap action | Find queue item with recall count > 0 | Recommended action references service action review or remedy readiness |
| Evidence review | Open Evidence Explorer | Real complaint/recall excerpts are visible |
