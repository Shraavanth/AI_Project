# Legacy files (reference only)

These are the original scripts from the first version of the project. They are
kept so the history of the project is visible, but **they are not used by the
current application** and several of them no longer run against the new code
(for example they assume the old 20x20 grid and `MonitoringAgent(x, y, ...)`).

| Folder | What it was |
|---|---|
| `agents_scripts/` | Original grid-based agent, consensus, communication and print-style test scripts |
| `ai_scripts/` | Print-style checks for the anomaly model |
| `network_scripts/` | Original Manhattan-distance network manager |
| `simulation_scripts/` | Original grid environment model and matplotlib visualisations |
| `verify_scripts/` | Scripts that needed a live server; replaced by `tests/` (pytest) |
| `streamlit_dashboard/` | Early Streamlit dashboard, replaced by the Next.js frontend |
| `original_backend/` | The previous FastAPI service/routes/models before the rewrite |
