from sqlalchemy import Column, String, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.base import Base

class AgentModel(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    llm_type = Column(String, nullable=False)
    llm_config = Column(JSON, nullable=False)
    prompt_template = Column(Text, nullable=False)
    fallback_prompt = Column(Text, nullable=True)

    tools = relationship("ToolModel", back_populates="agent")
