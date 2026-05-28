# Auto Trace Prep

Prepare the evidence needed for analysis.

Public-safe contract:

- Start from a synthetic or approved evaluation CSV.
- Produce runner output, optional trace JSON, and a manifest describing what was collected.
- Do not store credentials, private endpoints, real trace exports, or private user data.

Expected artifacts:

- `input.csv`
- `agent_output.csv`
- `trace.clean.json`
- `analysis_manifest.json`
