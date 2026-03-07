import sys, os 
sys.path.insert(0, 
os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
  
import logging 
from datetime import date 
import numpy as np 
import pandas as pd 
from tqdm import tqdm 
from sqlalchemy.dialects.postgresql import insert 

from src.data.loader import load_weekly_demand, load_sku_metadata 
from src.data.database import get_engine 
from src.data.models import PolicyResultDB 
from src.models.policy import run_sku_pipeline 
from src.models.baselines import ( 
    compute_heuristic_baseline, 
    compute_normal_baseline, 
    evaluate_on_holdout, 
) 

  
logging.basicConfig( 
    level=logging.WARNING,  # Suppress INFO during batch run 
    format='%(asctime)s  %(levelname)-8s  %(message)s', 
) 
log = logging.getLogger(__name__) 
  
# ── Configuration ───────────────────────────────────────────────── 
ORDER_COST      = 50.0   # £ per order 
HOLDING_RATE    = 0.20   # 20% annual holding rate 
STOCKOUT_COST   = 5.0    # £ per unit short 
LEAD_TIME_WEEKS = 2      # weeks 
SERVICE_LEVEL   = 0.95   # 95% target 
HOLDOUT_FRAC    = 0.25   # last 25% = Q4 holdout 
DEFAULT_PRICE   = 2.50   # fallback if unit_price is null/zero 
  
  
def run_all_skus() -> pd.DataFrame: 
    """ 
    Runs the pipeline for every SKU and returns a results DataFrame. 
    Failures are caught and logged — one bad SKU does not stop the batch. 
    """ 
    print('Loading demand data...') 
    df       = load_weekly_demand(min_weeks=40) 
    metadata = load_sku_metadata() 
    skus     = df['sku_id'].unique() 
    today    = date.today() 
  
    # Build price lookup 
    price_map = dict(zip(metadata['sku_id'], metadata['unit_price'])) 
  
    results  = [] 
    failures = [] 
  
    print(f'Running pipeline for {len(skus)} SKUs...') 
    for sku in tqdm(skus, desc='Optimising', unit='SKU'): 
        demand = df[df['sku_id'] == sku]['demand'].values 
        price  = float(price_map.get(sku) or DEFAULT_PRICE) 
        if price <= 0: 
            price = DEFAULT_PRICE 
  
        h = HOLDING_RATE * price / 52  # weekly holding cost 
  
        try: 
            # Run NB optimised policy 
            policy = run_sku_pipeline( 
                sku_id=sku, demand=demand, unit_price=price, 
                order_cost=ORDER_COST, holding_rate=HOLDING_RATE, 
                stockout_cost=STOCKOUT_COST, 
                lead_time_weeks=LEAD_TIME_WEEKS, 
                service_level=SERVICE_LEVEL, 
            ) 
  
            # Run baselines 
            heur   = compute_heuristic_baseline(sku, demand, h, ORDER_COST, STOCKOUT_COST) 
            normal = compute_normal_baseline(sku, demand, h, ORDER_COST, STOCKOUT_COST, 
                                             LEAD_TIME_WEEKS, SERVICE_LEVEL) 
  
            # Q4 holdout 
            nb_hout = evaluate_on_holdout(demand, policy,   HOLDOUT_FRAC, h, ORDER_COST, STOCKOUT_COST) 
            h_hout  = evaluate_on_holdout(demand, heur,     HOLDOUT_FRAC, h, ORDER_COST, STOCKOUT_COST) 
  
            results.append({ 
                'sku_id':          sku, 
                'run_date':        today, 
                'reorder_point':   policy.reorder_point, 
                'order_up_to':     policy.order_up_to, 
                'safety_stock':    policy.safety_stock, 
                'cost_per_unit':   policy.cost_per_unit, 
                'service_level':   policy.service_level, 
                'heuristic_cost':  heur.simulation.cost_per_unit, 
                'normal_cost':     normal.simulation.cost_per_unit, 
                'holdout_cost':    nb_hout['holdout_cost_per_unit'], 
                'holdout_sl':      nb_hout['holdout_service_level'], 
                'beats_heuristic': nb_hout['holdout_cost_per_unit'] <= h_hout['holdout_cost_per_unit'], 
                'nb_n':            policy.nb_params.n, 
                'nb_p':            policy.nb_params.p, 
                'nb_vm_ratio':     policy.nb_params.vm_ratio, 
                'nb_ks_pvalue':    policy.nb_params.ks_pvalue, 
                'nb_converged':    policy.nb_params.converged, 
            }) 
  
        except Exception as e: 
            log.warning(f'SKU {sku} failed: {e}') 
            failures.append({'sku_id': sku, 'error': str(e)}) 
  
    print(f'Complete: {len(results)} succeeded, {len(failures)} failed') 
    if failures: 
        print('Failed SKUs:') 
        for f in failures[:10]:  # show first 10 
            print(f'  {f["sku_id"]}: {f["error"]}') 
    return pd.DataFrame(results) 
  
  
def save_results(results_df: pd.DataFrame) -> None: 
    """ 
    Upserts results into policy_results table. 
    Safe to call multiple times — updates existing rows on (sku_id, run_date). 
    """ 
    if results_df.empty: 
        print('No results to save.') 
        return 
  
    engine  = get_engine() 
    records = results_df.to_dict('records') 
  
    with engine.begin() as conn: 
        stmt = insert(PolicyResultDB).values(records) 
        stmt = stmt.on_conflict_do_update( 
            index_elements=['sku_id', 'run_date'], 
            set_={ 
                col: stmt.excluded[col] 
                for col in records[0].keys() 
                if col not in ('sku_id', 'run_date') 
            } 
        ) 
        conn.execute(stmt) 
  
    print(f'Saved {len(records)} results to policy_results table.') 
  
  
if __name__ == '__main__': 
    results_df = run_all_skus() 
    save_results(results_df) 
  
    # Print summary 
    if not results_df.empty: 
        pct_beats = results_df['beats_heuristic'].mean() * 100 
        avg_saving = ( 
            (results_df['heuristic_cost'] - results_df['holdout_cost']) 
            / results_df['heuristic_cost'] * 100 
        ).mean() 
        print(f'\n=== BATCH SUMMARY ===') 
        print(f'SKUs optimised:          {len(results_df)}') 
        print(f'Beats heuristic (Q4):    {pct_beats:.1f}%') 
        print(f'Avg cost saving vs rule: {avg_saving:.1f}%') 
        print(f'Avg service level:       {results_df["service_level"].mean():.3f}') 