from __future__ import annotations 
import logging 
import numpy as np 
from dataclasses import dataclass 
from scipy.stats import nbinom, kstest 
from scipy.optimize import minimize 

 
log = logging.getLogger(__name__) 
  
  
@dataclass 
class NBParams: 
    """ 
    Fitted parameters for a Negative Binomial distribution. 
  
    Attributes 
    ---------- 
    n  : float  — dispersion parameter (r in some textbooks) 
                  larger n = less overdispersion 
    p  : float  — success probability (0 < p < 1) 
    mean      : float  — fitted mean (n * (1-p) / p) 
    variance  : float  — fitted variance (mean / p) 
    vm_ratio  : float  — variance/mean ratio (overdispersion measure) 
    ks_pvalue : float  — KS test p-value (> 0.05 = good fit) 
    converged : bool   — whether MLE optimisation converged 
    """ 
    n:         float 
    p:         float 
    mean:      float 
    variance:  float 
    vm_ratio:  float 
    ks_pvalue: float 
    converged: bool 
  
  
def fit_negative_binomial(demand: np.ndarray) -> NBParams: 
    """ 
    Fits a Negative Binomial distribution to demand data via MLE. 
  
    Uses method-of-moments estimates as starting values for the 
    Nelder-Mead optimiser. Falls back to Poisson parameters if 
    variance <= mean (underdispersed edge case). 
  
    Parameters 
    ---------- 
    demand : np.ndarray of non-negative integers 
  
    Returns 
    ------- 
    NBParams dataclass with fitted parameters and diagnostics 
  
    Raises 
    ------ 
    ValueError : if demand array is empty or contains negative values 
    """ 
    if len(demand) == 0:
        raise ValueError('demand array is empty')
    if np.any(demand < 0):
        raise ValueError('demand array contains negative values')

    mean = float(np.mean(demand))
    var  = float(np.var(demand))

    # Handle all-zeros edge case
    if mean == 0:
        return NBParams(
            n=1e-6, p=0.999,
            mean=0.0, variance=0.0,
            vm_ratio=0.0, ks_pvalue=0.0,
            converged=False,
        )

    # Handle underdispersed edge case
    if var <= mean:
        var = mean * 1.1

    # Method of moments starting values
    n0 = mean ** 2 / (var - mean)
    p0 = mean / var
    n0 = max(n0, 0.1)
    p0 = max(min(p0, 0.999), 0.001)
  
    def neg_log_likelihood(params: list) -> float: 
        n, p = params 
        if n <= 0 or p <= 0 or p >= 1: 
            return 1e10 
        ll = nbinom.logpmf(demand, n, p) 
        if np.any(np.isnan(ll)) or np.any(np.isinf(ll)): 
            return 1e10 
        return -np.sum(ll) 
  
    result = minimize( 
        neg_log_likelihood, 
        x0=[n0, p0], 
        method='Nelder-Mead', 
        options={'xatol': 1e-6, 'fatol': 1e-6, 'maxiter': 5000} 
    ) 
  
    n_fit, p_fit = result.x 
    converged    = result.success 
  
    # Clamp fitted params to valid range 
    n_fit = max(n_fit, 1e-6) 
    p_fit = max(min(p_fit, 1 - 1e-6), 1e-6) 
  
    # KS goodness-of-fit test 
    ks        = kstest(demand, 'nbinom', args=(n_fit, p_fit)) 
    fitted_mean = n_fit * (1 - p_fit) / p_fit 
    fitted_var  = fitted_mean / p_fit 
  
    if not converged: 
        log.warning(f'NB MLE did not converge. V/M={var/mean:.1f}. ' 
                    f'Parameters may be unreliable.') 
  
    return NBParams( 
        n=n_fit, 
        p=p_fit, 
        mean=fitted_mean, 
        variance=fitted_var, 
        vm_ratio=var / mean if mean > 0 else 0.0, 
        ks_pvalue=float(ks.pvalue), 
        converged=converged, 
    ) 
  
  
def fit_all_skus( 
    df, 
    sku_col:    str = 'sku_id', 
    demand_col: str = 'demand', 
    min_obs:    int = 20, 
) -> dict[str, NBParams]: 
    """ 
    Fits NB distribution to every SKU in a demand DataFrame. 
  
    Parameters 
    ---------- 
    df         : DataFrame with sku_id and demand columns 
    sku_col    : name of the SKU identifier column 
    demand_col : name of the demand column 
    min_obs    : minimum observations required to attempt fitting 
  
    Returns 
    ------- 
    dict mapping sku_id -> NBParams 
    SKUs with fewer than min_obs observations are skipped. 
    """ 
    results = {} 
    skus    = df[sku_col].unique() 
    log.info(f'Fitting NB distribution to {len(skus)} SKUs') 
  
    for sku in skus: 
        demand = df[df[sku_col] == sku][demand_col].values 
        if len(demand) < min_obs: 
            log.debug(f'SKU {sku}: skipped ({len(demand)} obs < {min_obs})') 
            continue 
        try: 
            results[sku] = fit_negative_binomial(demand) 
        except Exception as e: 
            log.warning(f'SKU {sku}: fitting failed — {e}') 
  
    pass_rate = np.mean([p.ks_pvalue > 0.05 for p in results.values()]) * 100 
    log.info(f'Fitting complete. KS pass rate: {pass_rate:.1f}% across {len(results)} SKUs') 
    return results 