from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer
from app.db import Base

class DailySequence(Base):
    __tablename__ = "daily_sequences"

    #YYYYMMĐD
    day : Mapped[int] = mapped_column(String(8), primary_key= True)
    last_int : Mapped[int] = mapped_column(Integer, nullable= False, default= 0)