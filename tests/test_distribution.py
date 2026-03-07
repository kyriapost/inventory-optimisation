import pytest 
import numpy as np 
from scipy.stats import nbinom 
from src.models.distribution import fit_negative_binomial, NBParams 
  
  
class TestFitNegativeBinomial: 
  
    def test_returns_nbparams(self): 
        demand = np.array([10, 20, 15, 8, 25, 12, 30, 18]) 
        result = fit_negative_binomial(demand) 
        assert isinstance(result, NBParams) 
  
    def test_params_in_valid_range(self): 
        np.random.seed(42) 
        demand = nbinom.rvs(n=5, p=0.3, size=100) 
        result = fit_negative_binomial(demand) 
        assert result.n > 0 
        assert 0 < result.p < 1 
  
    def test_fitted_mean_close_to_sample_mean(self): 
        # Fitted mean should be within 20% of sample mean for large samples 
        np.random.seed(0) 
        demand = nbinom.rvs(n=3, p=0.2, size=200) 
        result = fit_negative_binomial(demand) 
        sample_mean = demand.mean() 
        assert abs(result.mean - sample_mean) / sample_mean < 0.20 
  
    def test_overdispersed_data_has_high_vm(self): 
        np.random.seed(1) 
        # NB with small n = very overdispersed 
        demand = nbinom.rvs(n=1, p=0.1, size=100) 
        result = fit_negative_binomial(demand) 
        assert result.vm_ratio > 5.0 
  
    def test_empty_array_raises(self): 
        with pytest.raises(ValueError, match='empty'): 
            fit_negative_binomial(np.array([])) 
  
    def test_negative_values_raise(self): 
        with pytest.raises(ValueError, match='negative'): 
            fit_negative_binomial(np.array([1, -1, 3])) 
  
    def test_all_zeros_does_not_crash(self): 
        # Edge case: all zeros — should return params, not crash 
        demand = np.zeros(50, dtype=int) 
        result = fit_negative_binomial(demand)  # Should not raise 
        assert isinstance(result, NBParams) 