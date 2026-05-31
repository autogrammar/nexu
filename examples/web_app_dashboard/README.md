# Web App Dashboard Nexu Capsule Example

This example demonstrates how to use `nexu` to safely evolve a Web Application Dashboard (Baseline) into a more complex dashboard with active notification lists (Target), while verifying Intent Contracts and generating an interactive HTML preview mock for each iteration.

## Structure
- `src/dashboard.py`: Contains the dashboard logic with `@intract.v1` intent contract annotations.
- `fixtures/dashboard_data.json`: Static telemetry mock data.
- `run.py`: Script simulating the nexu lifecycle (Initialize -> Freeze -> Capsule Create -> Iterate S1 -> Iterate S2 -> Build Runtime -> Promote).
