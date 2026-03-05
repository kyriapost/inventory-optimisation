import sys
import logging
from pathlib import Path
import pandas as pd
from sqlalchemy.dialects.postgresql import insert

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import get_engine
from src.data.models import WeeklyDemand, SKUMetadata, Base

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

RAW_PATH = Path(__file__).parents[1] / 'data' / 'raw' / 'Online Retail.xlsx'
MIN_WEEKS = 40

def load_and_clean_raw():
    ''''Load and clean the raw data from the UCI repository.
    '''
    log.info(f'Loading raw data from {RAW_PATH}')
    df = pd.read_excel(RAW_PATH, dtype={'StockCode': str})
    log.info(f'Raw rows: {len(df)}')

    df = df[
        (df['Country'] == 'United Kingdom') &
        (df['Quantity'] > 0) &
        (df['StockCode'].str.match(r'^[0-9]{5}[A-Z]?$', na=False))
    ].copy()
    log.info(f'After filtering: {len(df):,} rows')

    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['week_start'] = df['InvoiceDate'].dt.to_period('W').dt.start_time.dt.date
    return df

def aggregate_to_weekly(df):
    '''Aggregates transactions to weekly demand per SKU.'''
    weekly = (df.groupby(['StockCode', 'week_start'])['Quantity'].sum().reset_index().rename(columns={'StockCode': 'sku_id', 'Quantity' : 'demand'}))
    counts = weekly.groupby('sku_id')['week_start'].count()
    valid = counts[counts >= MIN_WEEKS].index
    weekly = weekly[weekly['sku_id'].isin(valid)].copy()

    log.info(f'Weekly demand: {weekly["sku_id"].nunique():,} SKUs, {len(weekly):,} SKU-weeks')
    return weekly

def build_sku_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts SKU reference data (description, median unit price)."""
    return (
        df.groupby('StockCode').agg(
            description=('Description', 'first'),
            unit_price=('UnitPrice', 'median')
        ).reset_index()
        .rename(columns={'StockCode': 'sku_id'})
        .fillna({'description': 'Unknown', 'unit_price': 0.0})  # add this line
    )

def ingest_to_postgres(weekly: pd.DataFrame, metadata: pd.DataFrame):
    '''Ingests the weekly demand and SKU metadata into PostgreSQL.'''
    engine = get_engine()

    with engine.begin() as conn: 
        log.info('Ingesting weekly demand...') 
        for batch_start in range(0, len(weekly), 1000): 
            batch = weekly.iloc[batch_start:batch_start + 1000] 
            stmt = insert(WeeklyDemand).values(batch.to_dict('records')) 
            stmt = stmt.on_conflict_do_update( 
                index_elements=['sku_id', 'week_start'], 
                set_={'demand': stmt.excluded.demand} 
            ) 
            conn.execute(stmt) 
        log.info(f'Ingested {len(weekly):,} rows into weekly_demand') 
  
        log.info('Ingesting SKU metadata...') 
        for _, row in metadata.iterrows(): 
            stmt = insert(SKUMetadata).values(row.to_dict()) 
            stmt = stmt.on_conflict_do_update( 
                index_elements=['sku_id'], 
                set_={'description': stmt.excluded.description, 
                      'unit_price': stmt.excluded.unit_price} 
            ) 
            conn.execute(stmt) 
        log.info(f'Ingested {len(metadata):,} rows into sku_metadata')


if __name__ == '__main__':
    df_raw = load_and_clean_raw()
    weekly  = aggregate_to_weekly(df_raw)
    metadata = build_sku_metadata(df_raw)
    ingest_to_postgres(weekly, metadata)
    log.info('Ingestion complete')

