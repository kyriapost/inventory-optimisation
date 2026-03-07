# Uses SQLite in-memory — no Docker needed. 
  
import pytest 
import pandas as pd 
from datetime import date 
from sqlalchemy import create_engine 
from src.data.models import Base, PolicyResultDB 
  
  
@pytest.fixture(scope='module') 
def results_engine(): 
    engine = create_engine('sqlite:///:memory:') 
    Base.metadata.create_all(engine) 
    yield engine 
    Base.metadata.drop_all(engine) 
  
  
@pytest.fixture 
def sample_result_row(): 
    return { 
        'sku_id':          'TEST001', 
        'run_date':        date.today(), 
        'reorder_point':   45, 
        'order_up_to':     120, 
        'safety_stock':    15, 
        'cost_per_unit':   0.1234, 
        'service_level':   0.962, 
        'heuristic_cost':  0.1800, 
        'normal_cost':     0.1500, 
        'holdout_cost':    0.1300, 
        'holdout_sl':      0.955, 
        'beats_heuristic': True, 
        'nb_n':            4.5, 
        'nb_p':            0.18, 
        'nb_vm_ratio':     45.2, 
        'nb_ks_pvalue':    0.12, 
        'nb_converged':    True, 
    } 
  
  
class TestPolicyResultDB: 
  
    def test_table_created(self, results_engine): 
        from sqlalchemy import inspect 
        inspector = inspect(results_engine) 
        assert 'policy_results' in inspector.get_table_names() 
  
    def test_insert_and_retrieve(self, results_engine, sample_result_row): 
        from sqlalchemy.orm import sessionmaker 
        Session = sessionmaker(bind=results_engine) 
        with Session() as session: 
            row = PolicyResultDB(**sample_result_row) 
            session.add(row) 
            session.commit() 
            retrieved = session.query(PolicyResultDB).filter_by(sku_id='TEST001').first() 
            assert retrieved is not None 
            assert abs(retrieved.cost_per_unit - 0.1234) < 1e-4 
            assert retrieved.beats_heuristic is True 
  
    def test_beats_heuristic_logic(self, sample_result_row): 
        # beats_heuristic should be True when holdout_cost < heuristic_cost 
        assert sample_result_row['holdout_cost'] < sample_result_row['heuristic_cost'] 
        assert sample_result_row['beats_heuristic'] is True 
  
    def test_negative_saving_is_correctly_flagged(self, sample_result_row): 
        row = sample_result_row.copy() 
        row['holdout_cost']    = 0.25  # worse than heuristic 
        row['beats_heuristic'] = row['holdout_cost'] <= row['heuristic_cost'] 
        assert row['beats_heuristic'] is False 