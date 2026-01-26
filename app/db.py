from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.base import Base

from app.models.base import Base

# 👇 add đoạn này (để đăng ký tất cả model vào Base.metadata)
from app.models.case import Case  # noqa
from app.models.party import Party  # noqa
from app.models.case_party import CaseParty  # noqa
from app.models.property import Property  # noqa
from app.models.document import Document  # noqa


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