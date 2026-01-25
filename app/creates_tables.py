from sqlalchemy import create_engine
from app.models.base import Base
from app.models.party import Party

engine = create_engine("sqlite:///notary_erp.db")
Base.metadata.create_all(engine)
print("OK: Tables created successfully.")
