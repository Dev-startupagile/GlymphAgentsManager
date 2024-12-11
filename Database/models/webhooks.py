from sqlalchemy import Column, String, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from database.base import Base

class WebhookModel(Base):
    __tablename__ = "webhooks"

    id = Column(String, primary_key=True, index=True)
    tool_id = Column(String, ForeignKey("tools.id"), nullable=False)
    url = Column(String, nullable=False)  
    api_key = Column(String, nullable=False)  
    description = Column(Text, nullable=True)  
    is_active = Column(Boolean, default=True)  

    tool = relationship("ToolModel", back_populates="webhook")
