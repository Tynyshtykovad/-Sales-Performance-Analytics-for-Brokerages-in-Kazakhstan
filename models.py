from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text
from database import Base

class Manager(Base):
    __tablename__ = "managers"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    last_name = Column(String)
    is_admin = Column(Boolean)

class Deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    type_id = Column(String)
    stage_id = Column(String)
    currency_id = Column(String)
    opportunity = Column(Float)
    begindate = Column(String)
    closedate = Column(String)
    assigned_by_id = Column(Integer, ForeignKey("managers.id"))
    date_create = Column(String)
    date_modify = Column(String)
    source_id = Column(String)
    last_activity_time = Column(String)
