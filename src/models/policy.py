from __future__ import annotations 
import logging 
import numpy as np 
from dataclasses import dataclass 
from src.models.distribution import NBParams 
  
log = logging.getLogger(__name__) 
  
  
@dataclass 
class SimulationResult: 
    """ 
    Result of simulating an (s,S) policy over a demand series. 
  
    Attributes 
    ---------- 
    total_holding_cost  : float — sum of h * on_hand over all periods 
    total_ordering_cost : float — sum of K per order placed 
    total_stockout_cost : float — sum of p * units_short over all periods 
    total_cost          : float — sum of all three 
    cost_per_unit       : float — total_cost / total_demand 
    service_level       : float — fraction of demand met from stock 
    num_orders          : int   — total orders placed 
    total_demand        : float — sum of demand series 
    """ 
    total_holding_cost:  float 
    total_ordering_cost: float 
    total_stockout_cost: float 
    total_cost:          float 
    cost_per_unit:       float 
    service_level:       float 
    num_orders:          int 
    total_demand:        float 
  
  
def simulate_policy( 
    demand:         np.ndarray, 
    reorder_point:  int, 
    order_up_to:    int, 
    holding_cost:   float, 
    order_cost:     float, 
    stockout_cost:  float, 
    initial_stock:  int | None = None, 
) -> SimulationResult: 
    """ 
    Simulates an (s,S) inventory policy over a demand series. 
  
    At each period: 
      1. If stock <= s, place order to bring stock up to S 
      2. Receive demand 
      3. Accumulate holding, ordering, and stockout costs 
  
    Parameters 
    ---------- 
    demand        : np.ndarray — weekly demand observations 
    reorder_point : int        — reorder when stock <= s 
      order_up_to   : int        — order up to S 
    holding_cost  : float      — cost per unit on hand per period (h) 
    order_cost    : float      — fixed cost per order placed (K) 
    stockout_cost : float      — penalty per unit short per period (p) 
    initial_stock : int        — starting inventory; defaults to order_up_to 
  
    Returns 
    ------- 
    SimulationResult dataclass 
  
    Raises 
    ------ 
    ValueError : if reorder_point >= order_up_to 
    """ 
    if reorder_point >= order_up_to: 
        raise ValueError( 
            f'reorder_point ({reorder_point}) must be < order_up_to ({order_up_to})' 
        ) 
  
    stock = int(order_up_to if initial_stock is None else initial_stock) 
  
    total_holding  = 0.0 
    total_ordering = 0.0 
    total_stockout = 0.0 
    total_demand   = 0.0 
    units_met      = 0.0 
    num_orders     = 0 
  
    for d in demand: 
        d = int(d) 
  
        # Step 1: Review and order if needed 
        if stock <= reorder_point: 
            order_qty    = order_up_to - stock 
            stock       += order_qty 
            total_ordering += order_cost 
            num_orders   += 1 
  
        # Step 2: Meet demand 
        units_short = max(0, d - stock) 
        units_sold  = min(d, stock) 
        stock       = max(0, stock - d) 
  
        # Step 3: Accumulate costs 
        total_holding  += holding_cost  * stock 
        total_stockout += stockout_cost * units_short 
        total_demand   += d 
        units_met      += units_sold 
  
    total_cost  = total_holding + total_ordering + total_stockout 
    cost_per_unit = total_cost / total_demand if total_demand > 0 else 0.0 
    service_level = units_met  / total_demand if total_demand > 0 else 0.0 
  
    return SimulationResult( 
        total_holding_cost=round(total_holding,  2), 
        total_ordering_cost=round(total_ordering, 2), 
        total_stockout_cost=round(total_stockout, 2), 
        total_cost=round(total_cost, 2), 
        cost_per_unit=round(cost_per_unit, 4), 
        service_level=round(service_level, 4), 
        num_orders=num_orders, 
        total_demand=total_demand, 
    ) 

@dataclass 
class PolicyResult: 
    """ 
    Result of (s,S) policy optimisation for one SKU. 
  
    Attributes 
    ---------- 
    sku_id          : str   — product identifier 
    reorder_point   : int   — optimal s 
    order_up_to     : int   — optimal S 
    safety_stock    : int   — s minus expected lead-time demand 
    cost_per_unit   : float — optimised total cost per unit 
    service_level   : float — achieved service level in simulation 
    nb_params       : NBParams — fitted distribution parameters 
    """ 
    sku_id:          str 
    reorder_point:   int 
    order_up_to:     int 
    safety_stock:    int 
    cost_per_unit:   float 
    service_level:   float 
    nb_params:       NBParams 
  
  
def optimise_ss_policy( 
    sku_id:          str, 
    demand:          np.ndarray, 
    nb_params:       NBParams, 
    holding_cost:    float, 
    order_cost:      float, 
    stockout_cost:   float, 
    lead_time_weeks: int   = 2, 
    service_level:   float = 0.95, 
    s_range:         int   = 3, 
    S_range:         int   = 3, 
) -> PolicyResult: 
    """ 
    Finds the cost-minimising (s,S) policy for a single SKU. 
  
    Strategy: analytical starting point + local grid search. 
    The analytical reorder point (from nbinom.ppf) gives the 
    service-level optimal s. The grid search explores s_range 
    steps above and below to find the cost-minimising s. 
    S is set to s + EOQ with similar grid search around it. 
  
    Parameters 
    ---------- 
    sku_id          : str      — identifier for logging 
    demand          : ndarray  — full demand history (training set) 
    nb_params       : NBParams — fitted NB parameters 
    holding_cost    : float    — h (£ per unit per week) 
    order_cost      : float    — K (£ per order) 
    stockout_cost   : float    — p (£ per unit short) 
    lead_time_weeks : int      — supplier lead time 
    service_level   : float    — target fill rate 
    s_range         : int      — grid search steps above/below analytical s 
    S_range         : int      — grid search steps above/below analytical S 
  
    Returns 
    ------- 
    PolicyResult with optimal (s,S) and simulation metrics 
    """ 
    from src.models.inventory import compute_eoq 
    from scipy.stats import nbinom as nb_dist 
  
    # Analytical starting point 
    annual_demand = float(demand.mean()) * 52 
    eoq = compute_eoq( 
        annual_demand=max(annual_demand, 1), 
        order_cost=order_cost, 
        holding_cost=holding_cost * 52, 
    ) 
  
    n_lt = nb_params.n * lead_time_weeks 
    p_lt = nb_params.p 
    s_analytical = int(nb_dist.ppf(service_level, n_lt, p_lt)) 
    S_analytical = s_analytical + int(np.ceil(eoq.order_quantity)) 
  
    # Grid search around analytical starting point 
    best_cost = np.inf 
    best_s, best_S = s_analytical, S_analytical 
  
    for s_delta in range(-s_range, s_range + 1): 
        s = max(0, s_analytical + s_delta) 
        for S_delta in range(-S_range, S_range + 1): 
            S = max(s + 1, S_analytical + S_delta) 
            try: 
                result = simulate_policy( 
                    demand=demand, 
                    reorder_point=s, 
                    order_up_to=S, 
                    holding_cost=holding_cost, 
                    order_cost=order_cost, 
                    stockout_cost=stockout_cost, 
                ) 
                if result.cost_per_unit < best_cost: 
                    best_cost = result.cost_per_unit 
                    best_s, best_S = s, S 
            except ValueError: 
                continue 
  
    # Final simulation with best parameters 
    final = simulate_policy( 
        demand=demand, 
        reorder_point=best_s, 
        order_up_to=best_S, 
        holding_cost=holding_cost, 
        order_cost=order_cost, 
        stockout_cost=stockout_cost, 
    ) 
  
    expected_lt_demand = nb_params.n * lead_time_weeks * (1 - nb_params.p) / nb_params.p 
    safety_stock = max(0, best_s - int(np.ceil(expected_lt_demand))) 
  
    log.debug(f'SKU {sku_id}: s={best_s}, S={best_S}, ' f'cost/unit={final.cost_per_unit:.4f}, SL={final.service_level:.3f}') 
  
    return PolicyResult( 
        sku_id=sku_id, 
        reorder_point=best_s, 
        order_up_to=best_S, 
        safety_stock=safety_stock, 
        cost_per_unit=final.cost_per_unit, 
        service_level=final.service_level, 
        nb_params=nb_params, 
    ) 

  
def run_sku_pipeline( 
    sku_id:          str, 
    demand:          np.ndarray, 
    unit_price:      float, 
    order_cost:      float    = 50.0, 
    holding_rate:    float    = 0.20, 
    stockout_cost:   float    = 5.0, 
    lead_time_weeks: int      = 2, 
    service_level:   float    = 0.95, 
) -> PolicyResult: 
    """ 
    Runs the complete inventory optimisation pipeline for one SKU. 
  
    Steps: 
      1. Fit Negative Binomial distribution to demand 
      2. Compute EOQ 
      3. Optimise (s,S) policy via grid search 
      4. Return PolicyResult 
  
    This is the function called by the Streamlit app. 
    All parameters have sensible defaults for the UCI dataset. 
  
    Parameters 
    ---------- 
    sku_id          : str   — product identifier 
    demand          : ndarray — weekly demand history 
    unit_price      : float — price per unit in £ (for holding cost) 
    order_cost      : float — fixed cost per order in £ (default £50) 
    holding_rate    : float — annual holding rate as fraction (default 20%) 
    stockout_cost   : float — penalty per unit short in £ (default £5) 
    lead_time_weeks : int   — supplier lead time in weeks (default 2) 
    service_level   : float — target fill rate (default 95%) 
    Returns 
    ------- 
    PolicyResult dataclass 
    """ 
    from src.models.distribution import fit_negative_binomial 
  
    # Holding cost: weekly rate = annual_rate * unit_price / 52 
    holding_cost = holding_rate * unit_price / 52 
  
    nb_params = fit_negative_binomial(demand) 
  
    return optimise_ss_policy( 
        sku_id=sku_id, 
        demand=demand, 
        nb_params=nb_params, 
        holding_cost=holding_cost, 
        order_cost=order_cost, 
        stockout_cost=stockout_cost, 
        lead_time_weeks=lead_time_weeks, 
        service_level=service_level, 
    ) 