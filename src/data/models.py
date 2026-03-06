from sqlalchemy import Column, String, Integer, Float, Date, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase

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