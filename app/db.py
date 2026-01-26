from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.base import Base

DB_URL = "sqlite:///notary_erp.db"

engine = create_engine(DB_URL, future = True)
SessionLocal = sessionmaker(bind = engine, future = True, autoflush= True, autocommit = False)

def init_db() -> None:
    Base.metadata.create_all(bind = engine)

def get_db():
    db : Session = SessionLocal()
    try: 
        yield db
    finally:
        db.close()