from sqlalchemy import Column, String, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from database.base import Base

class ToolCredentialModel(Base):
    __tablename__ = "tool_credentials"

    id = Column(String, primary_key=True, index=True)
    tool_id = Column(String, nullable=False)
    name = Column(String, nullable=False)  
    value = Column(String, nullable=False)  
