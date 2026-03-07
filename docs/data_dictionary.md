# Data Dictionary 
  
All tables live in the `inventory_db` PostgreSQL database. 
Schema version is tracked by Alembic — see `database/migrations/`. 
  --- 
  
## Table: weekly_demand 
  
Weekly demand history per SKU. Grain: one row = one SKU, one calendar week. 
  
| Column | Type | Nullable | Description | 
|--------|------|----------|-------------| 
| id | INTEGER | No | Autoincrement primary key | 
| sku_id | VARCHAR(20) | No | Product identifier from source system | 
| week_start | DATE | No | Monday of the trading week | 
| demand | INTEGER | No | Units sold in this week. 0 = genuine zero demand 
week. | 
  
**Constraints:** 
- UNIQUE(sku_id, week_start) — one row per SKU per week 
- INDEX on sku_id — fast per-SKU queries 
- INDEX on week_start — fast date-range queries 
  
**Source:** scripts/ingest_uci_data.py from UCI Online Retail II dataset 
  --- 
  
## Table: sku_metadata 
  
Product reference data. 
  
| Column | Type | Nullable | Description | 
|--------|------|----------|-------------| 
| sku_id | VARCHAR(20) | No | Primary key — matches weekly_demand.sku_id | 
| description | VARCHAR(255) | Yes | Product description from source data | 
| unit_price | FLOAT | Yes | Most recent observed unit price in £. May be 
null. | 
  
**Note:** unit_price is used to compute the holding cost: h = unit_price * 
0.20 / 52. 
If null or zero, the batch pipeline uses a default of £2.50. 
--- 
  
## Table: policy_results 
  
Output of the (s,S) optimisation pipeline. One row per SKU per run date. 
  
| Column | Type | Description | 
|--------|------|-------------| 
| id | INTEGER | Autoincrement primary key | 
| sku_id | VARCHAR(20) | Product identifier | 
| run_date | DATE | Date the pipeline was run | 
| reorder_point | INTEGER | Optimal reorder point s | 
| order_up_to | INTEGER | Optimal order-up-to level S | 
| safety_stock | INTEGER | s minus expected lead-time demand | 
| cost_per_unit | FLOAT | Optimised cost per unit on training data | 
| service_level | FLOAT | Achieved fill rate on training data | 
| heuristic_cost | FLOAT | 6-week heuristic cost per unit (baseline 1) | 
| normal_cost | FLOAT | Normal-demand (s,S) cost per unit (baseline 2) | 
| holdout_cost | FLOAT | NB (s,S) cost per unit on Q4 holdout | 
| holdout_sl | FLOAT | NB (s,S) service level on Q4 holdout | 
| beats_heuristic | BOOLEAN | holdout_cost <= heuristic_cost | 
| nb_n | FLOAT | Fitted NB dispersion parameter | 
| nb_p | FLOAT | Fitted NB probability parameter | 
| nb_vm_ratio | FLOAT | Variance/mean ratio of demand series | 
| nb_ks_pvalue | FLOAT | KS test p-value (> 0.05 = good fit) | 
| nb_converged | BOOLEAN | Whether MLE optimisation converged | 
  
**Constraints:** 
- UNIQUE(sku_id, run_date) 
- INDEX on sku_id 
- INDEX on run_date 
  
**Usage:** load_policy_results() in src/data/loader.py returns the most 
recent run for each SKU. 