from sqlalchemy import Column, String, Integer, Float, Date, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Boolean 

class Base(DeclarativeBase):
    pass

class WeeklyDemand(Base):
    ''' Weekly demand history per SKU'''
    __tablename__ = 'weekly_demand'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(String(20), nullable=False)
    week_start = Column(Date, nullable=False)
    demand = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint('sku_id', 'week_start', name='uq_sku_week'),
        Index('ix_sku_id', 'sku_id'),
        Index('ix_week_start', 'week_start'),
    )

    def __repr__(self):
        return f'<WeeklyDemand(sku = {self.sku_id}, week = {self.week_start}, demand = {self.demand})>'
    
class SKUMetadata(Base):
    __tablename__ = 'sku_metadata'

    sku_id      = Column(String(20),  primary_key=True)
    description = Column(String(255), nullable=True)
    unit_price  = Column(Float,       nullable=True)   

    def __repr__(self):
        return f'<SKUMetadata(sku_id = {self.sku_id}, description = {self.description}, unit_price = {self.unit_price})>'
    

  
class PolicyResultDB(Base): 
    """ 
    Persisted output of the (s,S) optimisation pipeline. 
    One row per SKU per optimisation run. 
    Allows Streamlit app to display results without re-running the model. 
    """ 
    __tablename__ = 'policy_results' 
  
    id              = Column(Integer,     primary_key=True, autoincrement=True) 
    sku_id          = Column(String(20),  nullable=False) 
    run_date        = Column(Date,         nullable=False) 
  
    # Optimal policy parameters 
    reorder_point   = Column(Integer,     nullable=False) 
    order_up_to     = Column(Integer,     nullable=False) 
    safety_stock    = Column(Integer,     nullable=False) 
  
    # Simulation performance on training data 
    cost_per_unit   = Column(Float,       nullable=False) 
    service_level   = Column(Float,       nullable=False) 
  
    # Baseline comparisons 
    heuristic_cost  = Column(Float,       nullable=True) 
    normal_cost     = Column(Float,       nullable=True) 
  
    # Q4 holdout performance 
    holdout_cost    = Column(Float,       nullable=True) 
    holdout_sl      = Column(Float,       nullable=True) 
    beats_heuristic = Column(Boolean,     nullable=True) 
  
    # NB distribution diagnostics 
    nb_n            = Column(Float,       nullable=True) 
    nb_p            = Column(Float,       nullable=True) 
    nb_vm_ratio     = Column(Float,       nullable=True) 
    nb_ks_pvalue    = Column(Float,       nullable=True) 
    nb_converged    = Column(Boolean,     nullable=True) 
  
    __table_args__ = ( 
        UniqueConstraint('sku_id', 'run_date', name='uq_policy_sku_date'), 
        Index('ix_policy_results_sku_id',   'sku_id'), 
        Index('ix_policy_results_run_date', 'run_date'),
    )
