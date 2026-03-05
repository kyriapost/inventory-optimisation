import pytest 
import pandas as pd 
import numpy as np 
from src.data.validation import validate_demand_dataframe, validate_sku_has_sufficient_data

class TestValidateDemandDataframe: 
  
    def test_valid_dataframe_passes(self, sample_demand_df): 
        validate_demand_dataframe(sample_demand_df)  # Should not raise
    def test_missing_columns_raises(self, sample_demand_df): 
        df = sample_demand_df.drop(columns=['demand']) 
        with pytest.raises(ValueError, match='Missing required columns'): 
            validate_demand_dataframe(df) 
  
    def test_negative_demand_raises(self, sample_demand_df): 
        df = sample_demand_df.copy() 
        df.loc[0, 'demand'] = -1 
        with pytest.raises(ValueError, match='negative demand'): 
            validate_demand_dataframe(df) 
  
    def test_null_demand_raises(self, sample_demand_df): 
        df = sample_demand_df.copy() 
        df.loc[0, 'demand'] = None 
        with pytest.raises(ValueError, match='missing demand'): 
            validate_demand_dataframe(df) 
  
    def test_non_datetime_week_raises(self, sample_demand_df): 
        df = sample_demand_df.copy() 
        df['week_start'] = df['week_start'].astype(str)  # Convert to string 
        with pytest.raises(ValueError, match='datetime'): 
            validate_demand_dataframe(df) 
  
    def test_duplicate_sku_week_raises(self, sample_demand_df): 
        df = pd.concat([sample_demand_df, sample_demand_df.iloc[:1]]) 
        with pytest.raises(ValueError, match='duplicate'): 
            validate_demand_dataframe(df) 
  
    def test_empty_dataframe_raises(self): 
        df = pd.DataFrame(columns=['sku_id', 'week_start', 'demand']) 
        with pytest.raises(ValueError, match='empty'): 
            validate_demand_dataframe(df) 

class TestValidateSkuSufficientData: 
  
    def test_sufficient_data_passes(self): 
        series = pd.Series([10] * 25) 
        validate_sku_has_sufficient_data(series, 'SKU_001', 
min_observations=20) 
  
    def test_insufficient_data_raises(self): 
        series = pd.Series([10] * 5) 
        with pytest.raises(ValueError, match='SKU_001'): 
            validate_sku_has_sufficient_data(series, 'SKU_001', 
min_observations=20) 
  
    def test_counts_only_non_zero_observations(self): 
        # 25 total weeks but only 10 non-zero — should fail min_obs=20 
        series = pd.Series([10] * 10 + [0] * 15) 
        with pytest.raises(ValueError): 
            validate_sku_has_sufficient_data(series, 'SKU_001', 
min_observations=20) 