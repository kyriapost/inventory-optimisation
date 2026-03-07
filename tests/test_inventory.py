import pytest 
import numpy as np 
from src.models.inventory import ( 
    compute_eoq, EOQResult, 
    compute_reorder_point, ReorderResult, 
    compute_newsvendor_critical_ratio, 
) 
from src.models.distribution import NBParams 
  
  
# ── EOQ Tests ───────────────────────────────────────────────────── 
  
class TestComputeEOQ: 
  
    def test_returns_eoq_result(self): 
        result = compute_eoq(1200, 50, 2) 
        assert isinstance(result, EOQResult) 
  
    def test_known_value(self): 
        # D=1200, K=50, h=2 → Q* = sqrt(2*1200*50/2) = sqrt(60000) ≈ 244.9 
        result = compute_eoq(annual_demand=1200, order_cost=50, holding_cost=2) 
        assert abs(result.order_quantity - 244.9) < 1.0 
  
    def test_ordering_cost_equals_holding_cost(self): 
        # Key EOQ property: at Q*, ordering cost == holding cost 
        result = compute_eoq(1200, 50, 2) 
        assert abs(result.annual_ordering_cost - result.annual_holding_cost) < 0.01 
  
    def test_total_cost_is_sum(self): 
        result = compute_eoq(1200, 50, 2) 
        expected = result.annual_ordering_cost + result.annual_holding_cost 
        assert abs(result.total_annual_cost - expected) < 0.01 
  
    def test_higher_order_cost_increases_eoq(self): 
        # More expensive to order → order less frequently → larger Q 
        low  = compute_eoq(1200, 10, 2) 
        high = compute_eoq(1200, 100, 2) 
        assert high.order_quantity > low.order_quantity 
  
    def test_higher_holding_cost_decreases_eoq(self): 
        # More expensive to hold → smaller Q 
        low  = compute_eoq(1200, 50, 1) 
        high = compute_eoq(1200, 50, 10) 
        assert high.order_quantity < low.order_quantity 
  
    def test_zero_demand_raises(self): 
        with pytest.raises(ValueError, match='annual_demand'): 
            compute_eoq(0, 50, 2) 
  
    def test_negative_order_cost_raises(self): 
        with pytest.raises(ValueError, match='order_cost'): 
            compute_eoq(1200, -50, 2) 
  
  
# ── Reorder Point Tests ─────────────────────────────────────────── 
  
@pytest.fixture 
def sample_nb_params(): 
    """Sample NBParams for inventory tests.""" 
    return NBParams( 
        n=5.0, p=0.2, mean=20.0, variance=100.0, 
        vm_ratio=5.0, ks_pvalue=0.15, converged=True 
    ) 
  
@pytest.fixture 
def sample_eoq(): 
    """Sample EOQResult for reorder point tests.""" 
    from src.models.inventory import EOQResult 
    return EOQResult( 
        order_quantity=100.0, 
        annual_ordering_cost=200.0, 
        annual_holding_cost=200.0, 
        total_annual_cost=400.0, 
    ) 
  
class TestComputeReorderPoint: 
  
    def test_returns_reorder_result(self, sample_nb_params, sample_eoq): 
        result = compute_reorder_point(sample_nb_params, 2, 0.95, sample_eoq) 
        assert isinstance(result, ReorderResult) 
  
    def test_reorder_point_above_expected_demand(self, sample_nb_params, sample_eoq): 
        # At 95% service level, s must be >= expected lead-time demand 
        result = compute_reorder_point(sample_nb_params, 2, 0.95, sample_eoq) 
        assert result.reorder_point >= result.expected_lt_demand 
  
    def test_higher_service_level_higher_reorder_point(self, sample_nb_params, sample_eoq): 
        low  = compute_reorder_point(sample_nb_params, 2, 0.80, sample_eoq) 
        high = compute_reorder_point(sample_nb_params, 2, 0.99, sample_eoq) 
        assert high.reorder_point >= low.reorder_point 

    def test_longer_lead_time_higher_reorder_point(self, sample_nb_params, sample_eoq): 
        short = compute_reorder_point(sample_nb_params, 1, 0.95, sample_eoq) 
        long_ = compute_reorder_point(sample_nb_params, 4, 0.95, sample_eoq) 
        assert long_.reorder_point > short.reorder_point 
  
    def test_order_up_to_equals_reorder_plus_eoq(self, sample_nb_params, sample_eoq): 
        result = compute_reorder_point(sample_nb_params, 2, 0.95, sample_eoq) 
        expected_S = result.reorder_point + int(np.ceil(sample_eoq.order_quantity)) 
        assert result.order_up_to == expected_S 
  
    def test_zero_lead_time_raises(self, sample_nb_params, sample_eoq): 
        with pytest.raises(ValueError, match='lead_time_weeks'): 
            compute_reorder_point(sample_nb_params, 0, 0.95, sample_eoq) 
  
    def test_invalid_service_level_raises(self, sample_nb_params, sample_eoq): 
        with pytest.raises(ValueError, match='service_level'): 
            compute_reorder_point(sample_nb_params, 2, 1.5, sample_eoq) 
  
  
# ── Newsvendor Tests ────────────────────────────────────────────── 
  
class TestNewsvendorCriticalRatio: 
  
    def test_symmetric_costs_give_fifty_percent(self): 
        # Equal under/overage costs → 50% service level 
        cr = compute_newsvendor_critical_ratio(10, 10) 
        assert abs(cr - 0.5) < 1e-6 
  
    def test_high_underage_cost_gives_high_service_level(self): 
        # Stockout much more expensive than overstock → high service level 
        cr = compute_newsvendor_critical_ratio(underage_cost=100, overage_cost=1) 
        assert cr > 0.95 
  
    def test_result_between_zero_and_one(self): 
        cr = compute_newsvendor_critical_ratio(50, 10) 
        assert 0 < cr < 1 
  
    def test_zero_underage_raises(self): 
        with pytest.raises(ValueError): 
            compute_newsvendor_critical_ratio(0, 10) 