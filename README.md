# Inventory Optimisation Dashboard 
  
[![CI](https://github.com/kyriapost/inventory-optimisation/actions/workflows/ci.yml/badge.svg)](https://github.com/kyriapost/inventory-optimisation/actions) 
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://inventory-optimisation-rvgur38xeffzphhdgbgsdu.streamlit.app/)
  
**Live demo:** https://inventory-optimisation-rvgur38xeffzphhdgbgsdu.streamlit.app/

[![Python 3.11](https://img.shields.io/badge/python-3.11
blue.svg)](https://www.python.org/downloads/release/python-3110/) 
[![License: MIT](https://img.shields.io/badge/License-MIT
yellow.svg)](LICENSE) 
  
A data-driven (s,S) inventory optimisation tool for SME retailers. 
Fits a Negative Binomial demand distribution per SKU and computes 
cost-minimising reorder points and order-up-to levels. 
  
**Result:** NB (s,S) policy reduces inventory cost by [X]% vs the 
6-week heuristic on Q4 held-out data across [N] SKUs. 
  --- 
  
## Quick Start 
  
**Prerequisites:** Python 3.11, Docker Desktop 
  
```bash 
# 1. Clone and enter the project 
git clone https://github.com/kyriapost/inventory-optimisation.git 
cd inventory-optimisation 
  
# 2. Create virtual environment 
python -m venv .venv 
source .venv/bin/activate        # macOS/Linux 
# .venv\Scripts\Activate.ps1    # Windows PowerShell 
  
# 3. Install dependencies 
pip install -r requirements.txt 
  
# 4. Set up environment 
cp .env.example .env 
# Edit .env and fill in your credentials 
  
# 5. Start the database 
docker-compose up -d 
docker-compose ps   # confirm: inventory_db Up (healthy) 
  
# 6. Apply schema migrations 
alembic upgrade head 
  
# 7. Ingest the UCI dataset 
# Download Online Retail.xlsx from https://doi.org/10.24432/C5CG6D 
# Place it in data/raw/ 
python scripts/ingest_uci_data.py 
  
# 8. Run the optimisation pipeline 
python scripts/run_batch_pipeline.py 
  
# 9. Launch the app 
streamlit run app/streamlit_app.py 
``` 
  
Expected setup time: under 15 minutes on a clean machine. 
  --- 
  
## What this does 
  
Given weekly demand history per SKU, the tool: 
  
1. Fits a **Negative Binomial distribution** via MLE (justified by per-SKU variance/mean ratio analysis — 100% of SKUs overdispersed) 
2. Computes the **Economic Order Quantity** (EOQ) as the order-size baseline 
3. Optimises the **(s,S) reorder policy** — reorder when stock ≤ s, 
   order up to S — via grid search around the analytical starting point 
4. Compares against two baselines: 6-week heuristic and Normal-demand (s,S) 
5. Evaluates out-of-sample performance on Q4 held-out data 
  --- 
  
## Project structure 
  
``` 
inventory-optimisation/ 
├── app/                    # Streamlit presentation layer 
├── src/ 
│   ├── data/               # Data access layer (loader, models, validation) 
│   ├── features/           # Feature engineering 
│   └── models/             # Inventory model (distribution, policy, 
baselines) 
├── tests/                  # Full test suite (~40 tests) 
├── scripts/                # Ingestion and batch pipeline 
├── notebooks/              # EDA (00) and Validation (01) 
├── docs/                   # Methodology, data dictionary, case study 
├── database/migrations/    # Alembic schema version history 
└── docker-compose.yml      # PostgreSQL database 
``` 
  --- 
  
## Documentation 
  
| Document | Description | 
|----------|-------------| 
| [Methodology](docs/methodology.md) | Full mathematical derivation of the model | 
| [Data Dictionary](docs/data_dictionary.md) | Schema for all database tables| 
| [Case Study](docs/case_study.md) | Business interpretation of validation results | 
| [SCOPE.md](SCOPE.md) | Project definition and success metrics | 
| [CHANGELOG.md](CHANGELOG.md) | Complete decision log | 
  --- 
  
## Results 
  
Evaluated on UCI Online Retail dataset (1028 SKUs, Dec 2010 – Dec 2011): 
  
| Metric | Result | Target | 
|--------|--------|--------| 
| NB goodness-of-fit (KS pass rate) | 72.4% | ≥ 70% | 
| SKUs beating 6-week heuristic (Q4) | 88% | > 50% | 
| Mean Q4 service level | 0.997 | ≥ 0.90 | 
| 50 SKUs processed in | 1.5s | < 60s | 
  --- 
  
## Running tests 
  
```bash 
pytest tests/ -v 
# ~55 tests, no Docker required (SQLite in-memory for CI) 
``` 
  --- 
  
## Built with 
  
Python 3.11 · PostgreSQL 16 · SQLAlchemy · Alembic · Streamlit 
scipy · pandas · numpy · Docker · GitHub Actions 
