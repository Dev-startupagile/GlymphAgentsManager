from sqlalchemy import Column, String, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from database.base import Base
from database.models.agentTools import AgentToolAssociation

class ToolModel(Base):
    __tablename__ = "tools"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    api_key = Column(String, nullable=True)

    agent_tool_associations = relationship("AgentToolAssociation", backref="tool")

    @property
    def agents(self):
        return [assoc.agent for assoc in self.agent_tool_associations]
