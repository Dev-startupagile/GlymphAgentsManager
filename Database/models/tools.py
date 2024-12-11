from sqlalchemy import Column, String, JSON, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from database.base import Base

class ToolModel(Base):
    __tablename__ = "tools"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    api_key = Column(String, nullable=True)

    webhook = relationship("WebhookModel", back_populates="tool", uselist=False)  # One-to-one relationship

