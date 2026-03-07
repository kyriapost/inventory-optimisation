import pytest 
import pandas as pd 
import numpy as np 
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker 
from src.data.models import Base 
from src.data.database import get_engine 

@pytest.fixture(scope='session') 
def test_engine(): 
    """ 
    Creates a SQLite in-memory database for testing. 
    Faster than PostgreSQL and requires no Docker for CI. 
    Schema is identical to production (same SQLAlchemy models). 
    """ 
    engine = create_engine('sqlite:///:memory:') 
    Base.metadata.create_all(engine) 
    yield engine 
    Base.metadata.drop_all(engine)

@pytest.fixture(scope='function') 
def db_session(test_engine): 
    """ 
    Provides a clean database session for each test. 
    Rolls back all changes after each test so tests are isolated. 
    """ 
    connection  = test_engine.connect() 
    transaction = connection.begin() 
    Session     = sessionmaker(bind=connection) 
    session     = Session() 
  
    yield session 
  
    session.close() 
    transaction.rollback() 
    connection.close() 
  
@pytest.fixture 
def sample_demand_df(): 
    """ 
    Synthetic weekly demand DataFrame for testing. 
    Properties: 3 SKUs, 52 weeks each, Poisson-distributed demand. 
    """ 
    np.random.seed(42) 
    records = [] 
    for sku in ['SKU_001', 'SKU_002', 'SKU_003']: 
        for i in range(52): 
            records.append({ 
                'sku_id':     sku, 
                'week_start': pd.Timestamp('2023-01-02') + 
pd.Timedelta(weeks=i), 
                'demand':     int(np.random.poisson(lam=50)) 
            }) 
    df = pd.DataFrame(records) 
    df['week_start'] = pd.to_datetime(df['week_start']) 
    return df 
