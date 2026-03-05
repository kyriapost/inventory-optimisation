import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from src.data.models import Base

load_dotenv()

def get_engine():
    '''Create SQLAlchemy engine from DATABASE_URL environment variable'''
    url = os.getenv('DATABASE_URL')
    if not url:
        raise EnvironmentError('DATABASE_URL not set in environment variables')
    return create_engine(url, pool_pre_ping=True)

def get_session() -> Session:
    '''Create a new SQLAlchemy session'''
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def create_tables():
    '''Create database tables based on SQLAlchemy models'''
    engine = get_engine()
    Base.metadata.create_all(engine)