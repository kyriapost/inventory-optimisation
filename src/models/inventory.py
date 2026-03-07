from __future__ import annotations 
import logging 
import numpy as np 
from dataclasses import dataclass 
from scipy.stats import nbinom 
from src.models.distribution import NBParams 

log = logging.getLogger(__name__) 
  
  
@dataclass 
class EOQResult: 
    """ 
    Result of EOQ calculation. 
  
    Attributes 
    ---------- 
    order_quantity       : float — optimal order quantity Q* (units) 
    annual_ordering_cost : float — D/Q* * K (£/year) 
    annual_holding_cost  : float — Q*/2 * h (£/year) 
    total_annual_cost    : float — sum of above (£/year) 
    """ 
    order_quantity:       float 
    annual_ordering_cost: float 
    annual_holding_cost:  float 
    total_annual_cost:    float 
  
  
def compute_eoq( 
    annual_demand:  float, 
    order_cost:     float, 
    holding_cost:   float, 
) -> EOQResult: 
    """ 
    Computes the Economic Order Quantity (EOQ). 
  
    The EOQ minimises the sum of annual ordering cost and annual 
    holding cost. At Q*, both costs are equal (the square-root rule). 
  
    Parameters 
    ---------- 
    annual_demand : float — expected annual demand in units (D) 
    order_cost    : float — fixed cost per order placed in £ (K) 
    holding_cost  : float — cost to hold one unit for one year in £ (h) 
                           typically: unit_price * holding_rate 
                           e.g. £10 item * 20% rate = £2/unit/year 
  
    Returns 
    ------- 
    EOQResult dataclass 
  
    Raises 
    ------ 
    ValueError : if any parameter is <= 0 
    """ 
    if annual_demand <= 0: 
        raise ValueError(f'annual_demand must be > 0, got {annual_demand}') 
    if order_cost <= 0: 
        raise ValueError(f'order_cost must be > 0, got {order_cost}') 
    if holding_cost <= 0: 
        raise ValueError(f'holding_cost must be > 0, got {holding_cost}') 
  
    Q_star = np.sqrt(2 * annual_demand * order_cost / holding_cost) 
  
    annual_ordering = (annual_demand / Q_star) * order_cost 
    annual_holding  = (Q_star / 2) * holding_cost 
    total           = annual_ordering + annual_holding 
  
    return EOQResult( 
        order_quantity=round(Q_star, 2), 
        annual_ordering_cost=round(annual_ordering, 2), 
        annual_holding_cost=round(annual_holding, 2), 
        total_annual_cost=round(total, 2), 
    ) 
  
@dataclass 
class ReorderResult: 
    """ 
    Result of reorder point calculation. 
  
    Attributes 
    ---------- 
    reorder_point     : int   — order when stock falls to this level (s) 
    order_up_to       : int   — order up to this level (S = s + Q*) 
    safety_stock      : int   — buffer above expected lead-time demand 
    expected_lt_demand: float — mean demand over lead time 
    service_level     : float — target service level used 
    lead_time_weeks   : int   — lead time in weeks 
    """ 
    reorder_point:      int 
    order_up_to:        int 
    safety_stock:       int 
    expected_lt_demand: float 
    service_level:      float 
    lead_time_weeks:    int 
  
  
def compute_reorder_point( 
    nb_params:      NBParams, 
    lead_time_weeks: int, 
    service_level:  float, 
    eoq_result:     EOQResult, 
) -> ReorderResult: 
    """ 
    Computes the reorder point s and order-up-to level S for an 
    (s, S) inventory policy under Negative Binomial demand. 
  
    The reorder point is the service-level quantile of the lead-time 
    demand distribution. Lead-time demand is modelled as NB with the 
    same p parameter but n scaled by lead time. 
  
    Parameters 
    ---------- 
    nb_params       : NBParams — fitted NB distribution for this SKU 
    lead_time_weeks : int      — supplier lead time in weeks (>= 1) 
    service_level   : float    — target fill rate, e.g. 0.95 for 95% 
    eoq_result      : EOQResult — from compute_eoq(), provides Q* 
  
    Returns 
    ------- 
    ReorderResult dataclass 
  
    Raises 
    ------ 
    ValueError : if lead_time_weeks < 1 or service_level not in (0, 1) 
    """ 
    if lead_time_weeks < 1: 
        raise ValueError(f'lead_time_weeks must be >= 1, got {lead_time_weeks}') 
    if not 0 < service_level < 1: 
        raise ValueError(f'service_level must be in (0, 1), got {service_level}') 
  
    # Scale NB parameters over lead time 
    # For NB(n, p): mean scales linearly, p stays constant, n scales 
    n_lt = nb_params.n * lead_time_weeks 
    p_lt = nb_params.p 
  
    # Expected lead-time demand 
    expected_lt_demand = n_lt * (1 - p_lt) / p_lt 
  
    # Reorder point: service-level quantile of lead-time demand 
    reorder_point = int(nbinom.ppf(service_level, n_lt, p_lt)) 
  
    # Safety stock: buffer above expected lead-time demand 
    safety_stock = max(0, reorder_point - int(np.ceil(expected_lt_demand))) 
  
    # Order-up-to level: reorder point + EOQ 
    order_up_to = reorder_point + int(np.ceil(eoq_result.order_quantity)) 
  
    return ReorderResult( 
        reorder_point=reorder_point, 
        order_up_to=order_up_to, 
        safety_stock=safety_stock, 
        expected_lt_demand=round(expected_lt_demand, 2), 
        service_level=service_level, 
        lead_time_weeks=lead_time_weeks, 
    ) 
  
  
def compute_newsvendor_critical_ratio( 
    underage_cost: float, 
    overage_cost:  float, 
) -> float: 
    """ 
    Computes the newsvendor critical ratio. 
    The critical ratio is the optimal service level when underage 
    and overage costs are known explicitly. 
  
    Parameters 
    ---------- 
    underage_cost : float — cost per unit of unmet demand (c_u) 
                           e.g. lost margin, contractual penalty 
    overage_cost  : float — cost per unit of excess inventory (c_o) 
                           e.g. holding cost, obsolescence risk 
  
    Returns 
    ------- 
    float : optimal service level in (0, 1) 
  
    Raises 
    ------ 
    ValueError : if either cost is <= 0 
    """ 
    if underage_cost <= 0: 
        raise ValueError(f'underage_cost must be > 0, got {underage_cost}') 
    if overage_cost <= 0: 
        raise ValueError(f'overage_cost must be > 0, got {overage_cost}') 
  
    return underage_cost / (underage_cost + overage_cost)