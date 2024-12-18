from sqlalchemy import Column, String, ForeignKey
from database.base import Base

class AgentToolAssociation(Base):
    __tablename__ = "agent_tools"
    agent_id = Column(String, ForeignKey("agents.id"), primary_key=True)
    tool_id = Column(String, ForeignKey("tools.id"), primary_key=True)
