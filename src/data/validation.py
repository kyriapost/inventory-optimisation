import pandas as pd 
  
  
def validate_demand_dataframe(df: pd.DataFrame) -> None: 
    """ 
    Validates that a demand DataFrame meets the pipeline contract. 
  
    Expected schema: 
      sku_id     : str — product identifier 
      week_start : datetime — Monday of the trading week 
      demand     : int >= 0 — units sold that week 
  
    Raises 
    ------ 
    ValueError with specific message if any check fails. 
    """ 
    required = {'sku_id', 'week_start', 'demand'} 
    missing  = required - set(df.columns) 
    if missing: 
        raise ValueError( 
            f'Missing required columns: {missing}. ' 
            f'Expected columns: sku_id, week_start, demand.' 
        ) 
  
    if df.empty: 
        raise ValueError('DataFrame is empty — no data to process.') 
  
    if not pd.api.types.is_datetime64_any_dtype(df['week_start']): 
        raise ValueError( 
            'week_start must be datetime dtype. ' 
            'Call pd.to_datetime(df["week_start"]) before passing to pipeline.' 
        )
    neg_demand = df['demand'].lt(0).sum() 
    if neg_demand > 0: 
        raise ValueError( 
            f'{neg_demand} rows have negative demand values. ' 
            f'Check your data source for returns or corrections.' 
        ) 
  
    null_demand = df['demand'].isna().sum() 
    if null_demand > 0: 
        raise ValueError( 
            f'{null_demand} rows have missing demand values. ' 
            f'Impute or drop missing values before calling the pipeline.' 
        ) 
  
    dupes = df.duplicated(subset=['sku_id', 'week_start']).sum() 
    if dupes > 0: 
        raise ValueError( 
            f'{dupes} duplicate (sku_id, week_start) combinations found. ' 
            f'Each SKU should have at most one row per week.' 
        ) 
  
  
def validate_sku_has_sufficient_data( 
    series: pd.Series, 
    sku_id: str, 
    min_observations: int = 20 
) -> None: 
    """ 
    Validates that a single SKU's demand series has enough data 
    to fit a distribution reliably. 
  
    Parameters 
    ---------- 
    series           : demand values for one SKU 
    sku_id           : SKU identifier (for error message) 
    min_observations : minimum non-zero observations required 
  
    Raises 
    ------ 
    ValueError if fewer than min_observations non-zero weeks exist. 
    """ 
    non_zero = series[series > 0] 
    if len(non_zero) < min_observations: 
        raise ValueError( 
            f'SKU {sku_id}: only {len(non_zero)} non-zero demand weeks ' 
            f'(minimum {min_observations} required for distribution fitting).' 
            f'Consider reducing min_observations or excluding this SKU.' 
        ) 