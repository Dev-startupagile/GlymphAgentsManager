from sqlalchemy import Column, Integer, String
from database.base import Base

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False) 
    description = Column(String(255), nullable=True)  
