# agent.py
from sqlalchemy import Column, String, JSON, Text
from sqlalchemy.orm import relationship
from database.base import Base

from database.models.agentTools import AgentToolAssociation

class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    llm_type = Column(String, nullable=False)
    llm_config = Column(JSON, nullable=False)
    prompt_template = Column(Text, nullable=False)
    fallback_prompt = Column(Text, nullable=True)

    # Establish a relationship to AgentToolAssociation
    agent_tool_associations = relationship("AgentToolAssociation", backref="agent")

    @property
    def tools(self):
        return [assoc.tool for assoc in self.agent_tool_associations]
