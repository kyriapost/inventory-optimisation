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