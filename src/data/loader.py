from __future__ import annotations
import logging
import pandas as pd
from sqlalchemy import text
from src.data.database import get_engine

log = logging.getLogger(__name__)

def load_weekly_demand(sku_ids: list[str] | None = None, min_weeks: int = 40) -> pd.DataFrame:
    """ 
    Loads weekly demand history from the database. 
  
    Parameters 
    ---------- 
    sku_ids   : list of SKU IDs to load; None = all SKUs 
    min_weeks : minimum weeks of history required per SKU 
  
    Returns 
    ------- 
    DataFrame with columns: sku_id (str), week_start (datetime), demand (int) 
    Sorted by sku_id, week_start ascending. 
  
    Raises 
    ------ 
    ValueError : if no data found for the given parameters 
    """ 
    engine = get_engine() 
  
    query = ''' 
        SELECT sku_id, week_start, demand 
        FROM weekly_demand 
        WHERE (:sku_filter IS NULL OR sku_id = ANY(:sku_filter)) 
        ORDER BY sku_id, week_start 
    '''
      
    with engine.connect() as conn: 
        df = pd.read_sql( 
            text(query), conn, 
            params={'sku_filter': sku_ids} 
        ) 
  
    if df.empty: 
        raise ValueError('No demand data found. Check database is populated.') 
  
    df['week_start'] = pd.to_datetime(df['week_start']) 
  
    # Filter to SKUs with sufficient history 
    if min_weeks > 0: 
        counts    = df.groupby('sku_id')['week_start'].count() 
        valid     = counts[counts >= min_weeks].index 
        df        = df[df['sku_id'].isin(valid)] 
        log.info(f'Loaded {df["sku_id"].nunique()} SKUs with >= {min_weeks} weeks') 
  
    return df.reset_index(drop=True) 

  
def load_sku_metadata( 
    sku_ids: list[str] | None = None 
) -> pd.DataFrame: 
    """ 
    Loads SKU reference data (description, unit price). 
  
    Returns 
    ------- 
    DataFrame with columns: sku_id (str), description (str), unit_price 
(float) 
    """ 
    engine = get_engine() 
  
    query = ''' 
        SELECT sku_id, description, unit_price 
        FROM sku_metadata 
        WHERE (:sku_filter IS NULL OR sku_id = ANY(:sku_filter)) 
        ORDER BY sku_id 
    ''' 
  
    with engine.connect() as conn: 
        df = pd.read_sql(text(query), conn, params={'sku_filter': sku_ids}) 
  
    return df 

def get_sku_list(min_weeks: int = 40) -> list[str]: 
    """ 
    Returns sorted list of SKU IDs with sufficient demand history.
    Used to populate SKU selector in the Streamlit app. 
    """ 
    df = load_weekly_demand(min_weeks=min_weeks) 
    return sorted(df['sku_id'].unique().tolist()) 