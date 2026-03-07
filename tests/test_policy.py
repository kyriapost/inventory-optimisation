import pytest 
import numpy as np 
from src.models.policy import simulate_policy, SimulationResult, optimise_ss_policy 
from src.models.baselines import ( 
    compute_heuristic_baseline, 
    compute_normal_baseline, 
    evaluate_on_holdout, 
) 
from src.models.distribution import fit_negative_binomial 
  
  
# ── Fixtures ────────────────────────────────────────────────────── 
@pytest.fixture 
def steady_demand(): 
    """52 weeks of steady demand — easy case for the simulator.""" 
    np.random.seed(42) 
    return np.random.poisson(lam=50, size=52) 
  
@pytest.fixture 
def volatile_demand(): 
    """52 weeks of volatile demand — tests safety stock.""" 
    np.random.seed(0) 
    from scipy.stats import nbinom 
    return nbinom.rvs(n=2, p=0.1, size=52) 
  
  
# ── simulate_policy tests ───────────────────────────────────────── 
  
class TestSimulatePolicy: 
  
    def test_returns_simulation_result(self, steady_demand): 
        result = simulate_policy(steady_demand, 60, 200, 0.5, 50, 5) 
        assert isinstance(result, SimulationResult) 
  
    def test_service_level_between_zero_and_one(self, steady_demand): 
        result = simulate_policy(steady_demand, 60, 200, 0.5, 50, 5) 
        assert 0.0 <= result.service_level <= 1.0 
  
    def test_total_cost_is_sum_of_components(self, steady_demand): 
        result = simulate_policy(steady_demand, 60, 200, 0.5, 50, 5) 
        expected = (result.total_holding_cost + 
                    result.total_ordering_cost + 
                    result.total_stockout_cost) 
        assert abs(result.total_cost - expected) < 0.01 
  
    def test_high_reorder_point_gives_high_service_level(self, 
volatile_demand): 
        low_s  = simulate_policy(volatile_demand, 10,  500, 0.5, 50, 5) 
        high_s = simulate_policy(volatile_demand, 500, 1000, 0.5, 50, 5) 
        assert high_s.service_level >= low_s.service_level 
  
    def test_zero_demand_no_stockouts(self): 
        demand = np.zeros(52, dtype=int) 
        result = simulate_policy(demand, 10, 100, 0.5, 50, 5) 
        assert result.total_stockout_cost == 0.0 
  
    def test_reorder_point_gte_order_up_to_raises(self, steady_demand): 
        with pytest.raises(ValueError, match='reorder_point'): 
            simulate_policy(steady_demand, 100, 100, 0.5, 50, 5) 
  
    def test_num_orders_positive_with_nonzero_demand(self, steady_demand): 
        result = simulate_policy(steady_demand, 60, 200, 0.5, 50, 5) 
        assert result.num_orders > 0 

  
# ── optimise_ss_policy tests ────────────────────────────────────── 
  
class TestOptimiseSSPolicy: 
  
    def test_returns_policy_result(self, steady_demand): 
        from src.models.policy import PolicyResult 
        nb = fit_negative_binomial(steady_demand) 
        result = optimise_ss_policy( 
            'TEST', steady_demand, nb, 0.5, 50, 5 
        ) 
        assert isinstance(result, PolicyResult) 
  
    def test_reorder_point_less_than_order_up_to(self, steady_demand): 
        nb = fit_negative_binomial(steady_demand) 
        result = optimise_ss_policy( 
            'TEST', steady_demand, nb, 0.5, 50, 5 
        ) 
        assert result.reorder_point < result.order_up_to 
  
    def test_safety_stock_non_negative(self, steady_demand): 
        nb = fit_negative_binomial(steady_demand) 
        result = optimise_ss_policy( 
            'TEST', steady_demand, nb, 0.5, 50, 5 
        ) 
        assert result.safety_stock >= 0 
  
  
# ── baseline tests ──────────────────────────────────────────────── 
  
class TestBaselines: 
  
    def test_heuristic_returns_baseline_result(self, steady_demand): 
        from src.models.baselines import BaselineResult 
        result = compute_heuristic_baseline( 
            'TEST', steady_demand, 0.5, 50, 5 
        ) 
        assert isinstance(result, BaselineResult) 
        assert result.policy_name == 'heuristic_6week' 
  
    def test_normal_baseline_returns_result(self, steady_demand): 
        result = compute_normal_baseline( 
            'TEST', steady_demand, 0.5, 50, 5 
        ) 
        assert result.policy_name == 'normal_ss' 
  
    def test_holdout_evaluation_runs(self, steady_demand): 
        nb = fit_negative_binomial(steady_demand) 
        policy = optimise_ss_policy('TEST', steady_demand, nb, 0.5, 50, 5 ) 
        holdout = evaluate_on_holdout( steady_demand, policy, 0.25, 0.5, 50, 5 ) 
        assert 'holdout_cost_per_unit'  in holdout 
        assert 'holdout_service_level'  in holdout 
        assert 0 <= holdout['holdout_service_level'] <= 1 
  
    def test_heuristic_high_stockout_cost_increases_cost(self, volatile_demand): 
        # Higher stockout cost should increase total cost 
        low  = compute_heuristic_baseline('T', volatile_demand, 0.5, 50, 1) 
        high = compute_heuristic_baseline('T', volatile_demand, 0.5, 50, 50) 
        assert high.simulation.total_cost >= low.simulation.total_cost 