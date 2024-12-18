from sqlalchemy.orm import Session
from sqlalchemy import and_
from database.models.agent import AgentModel
from database.models.tools import ToolModel
from database.models.agentTools import AgentToolAssociation
from fastapi import HTTPException, status
from typing import Dict, Any, Optional

def associate_tools_to_agent(db: Session, agent_id: str, tool_ids: list):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent with id '{agent_id}' not found.")

    tools = db.query(ToolModel).filter(ToolModel.id.in_(tool_ids), ToolModel.is_active == True).all()
    if len(tools) != len(tool_ids):
        existing_tool_ids = {tool.id for tool in tools}
        missing = set(tool_ids) - existing_tool_ids
        raise HTTPException(status_code=404, detail=f"Tools with ids {missing} not found or inactive.")


    for tool in tools:
        association = db.query(AgentToolAssociation).filter(
            and_(
                AgentToolAssociation.agent_id == agent_id,
                AgentToolAssociation.tool_id == tool.id
            )
        ).first()
        if not association:
            new_association = AgentToolAssociation(agent_id=agent_id, tool_id=tool.id)
            db.add(new_association)
    
    db.commit()
    return {"message": "Tools associated with the agent successfully."}

def unassociate_tools_from_agent(db: Session, agent_id: str, tool_ids: list):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent with id '{agent_id}' not found.")

    associations = db.query(AgentToolAssociation).filter(
        and_(
            AgentToolAssociation.agent_id == agent_id,
            AgentToolAssociation.tool_id.in_(tool_ids)
        )
    ).all()

    if not associations:
        raise HTTPException(status_code=404, detail="No matching tool associations found for this agent.")

    for association in associations:
        db.delete(association)

    db.commit()
    return {"message": "Tools unassociated from the agent successfully."}


def get_agent_with_tools(db: Session, agent_id: str) -> Optional[AgentModel]:
    """
    Retrieve an agent along with its associated tools by agent ID.
    """
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent with id '{agent_id}' not found.")
    return agent

def get_agent_with_tools_by_name(db: Session, agent_name: str) -> Optional[AgentModel]:
    """
    Retrieve an agent along with its associated tools by agent name.
    """
    agent = db.query(AgentModel).filter(AgentModel.name == agent_name).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent with name '{agent_name}' not found.")
    return agent
