# Sentinel Quant Agent — Documentation Overview

Welcome to the Sentinel Quant Agent documentation. This site is generated via **MkDocs** and contains all operational, analytical, and architectural details of the betting system.

## Folder Architecture
- **`docs/`**: Contains all documentation files, session logs, and performance reports.
- **`src/`**: The main source code directory containing all business logic, mathematical models, and data extraction tools.
- **`data/`**: (Auto-generated) Stores temporary JSON payloads from the casino API for debugging and parsing.
- **`.venv/`**: Python virtual environment for dependency isolation.

## Core Files
- **`main.py`**: A dry-run orchestrator. Scans leagues and displays +EV bets in the console but does **not** log them to the database or update reports. Use this for quick market checks.
- **`run_session.py`**: The primary daily entry point. Checks for finished match results, runs a full league scan, logs bets to the database, and regenerates the performance report in `docs/`.
- **`requirements.txt`**: Lists all Python dependencies (Playwright, Scipy, NumPy, etc.) required to run the agent.
- **`bets.db`**: SQLite database containing all historical raw odds and the `simulated_bets` track record for performance attribution.
- **`mkdocs.yml`**: Configuration for this documentation site.

## Navigation
- [Operational Guide](human.md) — How to use the system.
- [Performance Segmentation](PERFORMANCE_SEGMENTATION.md) — ROI and Model Accuracy.
- [Session Log](SESSION_LOG.md) — History of automated runs.
- [Architecture](src/SRC_DEBUG.md) — Deep dive into the codebase.

