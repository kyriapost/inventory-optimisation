# CHANGELOG.md 
  
## [Unreleased] 
  
## [0.1.0] — [3/3/2026] 
### Added 
- Initial project structure 
- SCOPE.md: project definition and definition of done 
- GitHub Actions CI configuration 
- Python virtual environment with pinned dependencies 

## [0.2.0] — [5/3/2026] 
### Added 
- Docker + PostgreSQL setup via docker-compose.yml 
- SQLAlchemy models: WeeklyDemand, SKUMetadata 
- Alembic database migrations — schema versioned from day one 
- scripts/ingest_uci_data.py — loads UCI dataset into PostgreSQL 
- src/data/loader.py — data access layer (load_weekly_demand, 
load_sku_metadata) 
- src/data/validation.py — pipeline data contract enforcement 
- tests/conftest.py — SQLite in-memory test fixtures 
- tests/test_validation.py — 9 tests covering all validation paths 
  
### Technical decisions - SQLite used for CI tests (no Docker in CI), PostgreSQL for local dev and production - Upsert logic in ingestion script means it is safe to re-run without duplicates 
  
## [0.3.0] — [7/3/2026] 
### Added - notebooks/00_EDA.ipynb: full EDA notebook loading from PostgreSQL 
  - Q1: Structure — 1028 SKUs, 54879 SKU-weeks, 52-week history confirmed 
  - Q2: Quality — missing values, zero-demand rate, outlier investigation 
  - Q3: Distribution — overdispersion confirmed (median V/M = 141) NB goodness-of-fit pass rate: 72.4% (> 70% target: MET) 
  - Q4: SKU classification — 135 Smooth, 864 Erratic, 0 Intermittent, 29 Lumpy 
  - Q5: Seasonality — [brief finding] 
  
### Key modelling decision 
- Negative Binomial distribution selected based on V/M ratio evidence.This decision is documented in Section 4 of the EDA notebook 

## [0.4.0] — [7/3/2026] 
### Added - src/models/distribution.py 
  - fit_negative_binomial(): MLE via Nelder-Mead, NBParams dataclass 
  - fit_all_skus(): batch fitting with KS pass rate logging - src/models/inventory.py 
  - compute_eoq(): EOQ with analytical verification (ordering=holding at Q*) 
  - compute_reorder_point(): (s,S) policy under NB demand 
  - compute_newsvendor_critical_ratio(): optimal SL from cost parameters - tests/test_distribution.py: 7 tests - tests/test_inventory.py: 13 tests - All 20 model tests passing, CI green 
  
### Technical decisions 
- NBParams dataclass as contract between distribution and inventory modules 
- Lead-time demand: NB(n*L, p) scaling — IID weekly demand assumption documented as known limitation in methodology.md (to be written Stage 6)

## [0.5.0] — [7/3/2026] 
### Added 
- src/models/policy.py 
- simulate_policy(): periodic review (s,S) simulation with full cost tracking 
- optimise_ss_policy(): grid search around analytical NB starting point 
- run_sku_pipeline(): single function end-to-end for one SKU - src/models/baselines.py 
- compute_heuristic_baseline(): 6-week fixed rule 
- compute_normal_baseline(): Normal-assumption (s,S) 
- evaluate_on_holdout(): Q4 held-out evaluation for any policy 
- tests/test_policy.py: 11 tests 