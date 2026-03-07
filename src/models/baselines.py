from __future__ import annotations 
import numpy as np 
from dataclasses import dataclass 
from scipy.stats import norm 
from src.models.policy import simulate_policy, SimulationResult 
  
  
@dataclass 
class BaselineResult: 
    """ 
    Result of a baseline policy evaluation. 
  
    Attributes 
    ---------- 
    sku_id        : str   — product identifier 
    policy_name   : str   — 'heuristic_6week' or 'normal_ss' 
    reorder_point : int   — s used 
    order_up_to   : int   — S used 
    simulation    : SimulationResult — full simulation metrics 
    """ 
    sku_id:        str 
    policy_name:   str 
    reorder_point: int 
    order_up_to:   int 
    simulation:    SimulationResult 
  
  
def compute_heuristic_baseline( 
    sku_id:        str, 
    demand:        np.ndarray, 
    holding_cost:  float, 
    order_cost:    float, 
    stockout_cost: float, 
    weeks:         int = 6, 
) -> BaselineResult: 
    """ 
    Evaluates the fixed weeks-of-supply heuristic. 
  
    Reorder point = weeks * mean_weekly_demand 
    Order up to   = 2 * weeks * mean_weekly_demand 
  
    This represents the policy most SME retailers use today. 
    It ignores demand variability entirely. 
  
    Parameters 
    ---------- 
    sku_id       : str      — product identifier 
    demand       : ndarray  — weekly demand series 
    holding_cost : float    — h (£ per unit per week) 
    order_cost   : float    — K (£ per order) 
    stockout_cost: float    — p (£ per unit short) 
    weeks        : int      — weeks of supply (default 6)
  
    Returns 
    ------- 
    BaselineResult 
    """ 
    mean_demand   = float(np.mean(demand)) 
    reorder_point = max(1, int(np.ceil(weeks * mean_demand))) 
    order_up_to   = max(reorder_point + 1, int(np.ceil(2 * weeks * mean_demand))) 
  
    sim = simulate_policy( 
        demand=demand, 
        reorder_point=reorder_point, 
        order_up_to=order_up_to, 
        holding_cost=holding_cost, 
        order_cost=order_cost, 
        stockout_cost=stockout_cost, 
    ) 
  
    return BaselineResult( 
        sku_id=sku_id, 
        policy_name='heuristic_6week', 
        reorder_point=reorder_point, 
        order_up_to=order_up_to, 
        simulation=sim, 
    ) 
  
def compute_normal_baseline( 
    sku_id:          str, 
    demand:          np.ndarray, 
    holding_cost:    float, 
    order_cost:      float, 
    stockout_cost:   float, 
    lead_time_weeks: int   = 2, 
    service_level:   float = 0.95, 
) -> BaselineResult: 
    """ 
    Evaluates the (s,S) policy assuming Normal demand distribution. 
  
    This baseline isolates the value of the NB distribution choice. 
    Parameters are computed analytically from the Normal distribution 
    rather than fitted via MLE. 
  
    Reorder point = mu_lt + z * sigma_lt 
    Where mu_lt and sigma_lt are mean and std of lead-time demand, 
    and z is the Normal service-level factor. 
    """ 
    from src.models.inventory import compute_eoq 
  
    mean_w  = float(np.mean(demand)) 
    std_w   = float(np.std(demand)) 
  
    # Lead-time demand statistics under Normal assumption 
    mu_lt    = mean_w  * lead_time_weeks 
    sigma_lt = std_w   * np.sqrt(lead_time_weeks) 
  
    # Service-level factor z 
    z = norm.ppf(service_level) 
  
    reorder_point = max(0, int(np.ceil(mu_lt + z * sigma_lt))) 
  
    # EOQ for order-up-to level 
    annual_demand = mean_w * 52 
    eoq = compute_eoq( 
        annual_demand=max(annual_demand, 1), 
        order_cost=order_cost, 
        holding_cost=holding_cost * 52, 
    ) 
    order_up_to = reorder_point + int(np.ceil(eoq.order_quantity)) 
  
    sim = simulate_policy( 
        demand=demand, 
        reorder_point=reorder_point, 
        order_up_to=order_up_to, 
        holding_cost=holding_cost, 
        order_cost=order_cost, 
        stockout_cost=stockout_cost, 
    )
  
    return BaselineResult( 
        sku_id=sku_id, 
        policy_name='normal_ss', 
        reorder_point=reorder_point, 
        order_up_to=order_up_to, 
        simulation=sim, 
    ) 
  
  
def evaluate_on_holdout( 
    demand_full:     np.ndarray, 
    policy_result, 
    holdout_fraction: float = 0.25, 
    holding_cost:    float  = 0.5, 
    order_cost:      float  = 50.0, 
    stockout_cost:   float  = 5.0, 
) -> dict: 
    """ 
    Evaluates a fitted policy on held-out demand (Q4 test). 
  
    Splits demand into training (75%) and holdout (25%) periods. 
    The policy was fitted on training data. We evaluate its cost 
    on holdout data to test out-of-sample performance. 
  
    Parameters 
    ---------- 
    demand_full      : full demand series 
    policy_result    : PolicyResult or BaselineResult with s and S 
    holdout_fraction : fraction of demand reserved for holdout 
  
    Returns 
    ------- 
    dict with keys: holdout_cost_per_unit, holdout_service_level, 
                    holdout_weeks, policy_name 
    """ 
    n_holdout   = max(1, int(len(demand_full) * holdout_fraction)) 
    holdout     = demand_full[-n_holdout:] 
  
    # Extract s and S from either PolicyResult or BaselineResult 
    if hasattr(policy_result, 'reorder_point'): 
        s = policy_result.reorder_point 
        S = policy_result.order_up_to 
    else: 
        raise ValueError('policy_result must have reorder_point and order_up_to') 
  
    sim = simulate_policy( 
        demand=holdout, 
        reorder_point=s, 
        order_up_to=S, 
        holding_cost=holding_cost, 
        order_cost=order_cost, 
        stockout_cost=stockout_cost, 
    ) 
  
    policy_name = getattr(policy_result, 'policy_name', 
                  getattr(policy_result, 'sku_id', 'unknown')) 
  
    return { 
        'holdout_cost_per_unit':  sim.cost_per_unit, 
        'holdout_service_level':  sim.service_level, 
        'holdout_weeks':          n_holdout, 
        'policy_name':            policy_name, 
    } 