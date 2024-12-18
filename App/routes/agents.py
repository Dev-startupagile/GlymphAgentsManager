from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.connection import get_db
from database.models.agent import AgentModel
from AgentWrapper.agent import AgentManager
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from app.agent_tools_crud import associate_tools_to_agent, unassociate_tools_from_agent, get_agent_with_tools, get_agent_with_tools_by_name

agents = APIRouter()

class LLMConfig(BaseModel):
    model_name: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 256
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    class Config:
        schema_extra = {
            "example": {
                "model_name": "gpt-4",
                "api_key": "your-api-key",
                "temperature": 0.7,
                "max_tokens": 150,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
            }
        }


class AgentCreateRequest(BaseModel):
    name: str
    description: str
    llm_type: str
    llm_config: LLMConfig
    prompt_template: str
    fallback_prompt: str = "Sorry, something went wrong."

    class Config:
        schema_extra = {
            "example": {
                "name": "ChatBot",
                "description": "An intelligent chatbot",
                "llm_type": "openai",
                "llm_config": {
                    "model_name": "gpt-4",
                    "api_key": "your-api-key",
                    "temperature": 0.7,
                    "max_tokens": 150,
                    "top_p": 1.0,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                },
                "prompt_template": "You are a helpful assistant...",
                "fallback_prompt": "I'm sorry, I couldn't understand your question.",
            }
        }


class AgentUseRequest(BaseModel):
    name: str
    input_text: str

    class Config:
        schema_extra = {
            "example": {
                "name": "ChatBot",
                "input_text": "How is the weather today?",
            }
        }

from pydantic import BaseModel, Field
from typing import List

class AssociateToolsRequest(BaseModel):
    tool_ids: List[str] = Field(..., description="List of Tool IDs to associate with the agent.")

    class Config:
        schema_extra = {
            "example": {
                "tool_ids": [
                    "0fee971f-fadf-4fe1-b591-7c625a9eaea4",
                    "1a2b3c4d-5678-90ab-cdef-1234567890ab"
                ]
            }
        }

class UnassociateToolsRequest(BaseModel):
    tool_ids: List[str] = Field(..., description="List of Tool IDs to remove from the agent.")

    class Config:
        schema_extra = {
            "example": {
                "tool_ids": [
                    "0fee971f-fadf-4fe1-b591-7c625a9eaea4"
                ]
            }
        }

class ToolSchema(BaseModel):
    id: str = Field(..., description="The unique identifier of the tool.")
    name: str = Field(..., description="The name of the tool.")
    description: Optional[str] = Field(None, description="A short description of what the tool does.")
    config: Dict[str, Any] = Field(..., description="Configuration details for the tool.")
    is_active: bool = Field(..., description="Indicates whether the tool is active.")
    api_key: Optional[str] = Field(None, description="API key for the tool, if applicable.")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "0fee971f-fadf-4fe1-b591-7c625a9eaea4",
                "name": "weather_tool",
                "description": "An API to check weather",
                "config": {
                    "func": "generic_api_call",
                    "endpoint_url": "http://api.weatherapi.com/v1/current.json",
                    "method": "GET",
                    "headers": {"Authorization": "Bearer YOUR_API_KEY"},
                    "params": {"units": "metric"},
                    "data": {},
                    "input_location": "params",
                    "input_key": "q"
                },
                "is_active": True,
                "api_key": "auth-key"
            }
        }


class AgentSchema(BaseModel):
    id: str = Field(..., description="The unique identifier of the agent.")
    name: str = Field(..., description="The name of the agent.")
    description: str = Field(..., description="A short description of the agent.")
    llm_type: str = Field(..., description="The type of LLM used by the agent (e.g., OpenAI, Cohere).")
    llm_config: Dict[str, Any] = Field(..., description="Configuration details for the LLM.")
    prompt_template: str = Field(..., description="The prompt template used by the agent.")
    fallback_prompt: Optional[str] = Field(None, description="Fallback prompt if the main prompt fails.")
    tools: List[ToolSchema] = Field(default_factory=list, description="List of tools associated with the agent.")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "agent-123",
                "name": "prime_agent",
                "description": "A prime agent for handling various tasks",
                "llm_type": "openai",
                "llm_config": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "api_key": "openai-api-key"
                },
                "prompt_template": "You are a helpful assistant.",
                "fallback_prompt": "I encountered an issue processing your request.",
                "tools": [
                    {
                        "id": "0fee971f-fadf-4fe1-b591-7c625a9eaea4",
                        "name": "weather_tool",
                        "description": "An API to check weather",
                        "config": {
                            "func": "generic_api_call",
                            "endpoint_url": "http://api.weatherapi.com/v1/current.json",
                            "method": "GET",
                            "headers": {"Authorization": "Bearer YOUR_API_KEY"},
                            "params": {"units": "metric"},
                            "data": {},
                            "input_location": "params",
                            "input_key": "q"
                        },
                        "is_active": True,
                        "api_key": "auth-key"
                    }
                ]
            }
        }



@agents.post("/agents/create")
def create_agent(request: AgentCreateRequest, db: Session = Depends(get_db)):
    """
    Create and save a new agent configuration.
    """
    try:
        return AgentManager.create_agent_in_db(request.model_dump(), db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@agents.get("/agents/list")
def list_agents(db: Session = Depends(get_db)):
    """
    List all agents saved in the database.
    """
    agents = db.query(AgentModel).all()
    return [
        {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "llm_type": agent.llm_type,
        }
        for agent in agents
    ]


@agents.get("/agents/details/{name}")
def get_agent_details(name: str, db: Session = Depends(get_db)):
    """
    Retrieve details of a specific agent by name.
    """
    agent = db.query(AgentModel).filter(AgentModel.name == name).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found.")

    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "llm_type": agent.llm_type,
        "llm_config": agent.llm_config,
        "prompt_template": agent.prompt_template,
        "fallback_prompt": agent.fallback_prompt,
    }

@agents.post("/agents/use")
def use_agent(request: AgentUseRequest, db: Session = Depends(get_db)):
    """
    Use an agent to process input text.
    """
    try:
        return AgentManager.use_agent_from_db(request.name, request.input_text, db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@agents.put("/agents/update/{name}")
def update_agent(name: str, request: AgentCreateRequest, db: Session = Depends(get_db)):
    """
    Update an existing agent's configuration by name.
    """
    agent = db.query(AgentModel).filter(AgentModel.name == name).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found.")

    try:
        # Update agent fields
        for key, value in request.dict().items():
            setattr(agent, key, value)
        db.commit()
        return {"message": f"Agent '{name}' updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@agents.delete("/agents/delete/{name}")
def delete_agent(name: str, db: Session = Depends(get_db)):
    """
    Delete an agent by name.
    """
    agent = db.query(AgentModel).filter(AgentModel.name == name).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found.")

    try:
        db.delete(agent)
        db.commit()
        return {"message": f"Agent '{name}' deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agents.post("/agents/{agent_id}/tools/associate", status_code=200)
def associate_tools(
    agent_id: str,
    request: AssociateToolsRequest,
    db: Session = Depends(get_db)
):
    """
    Associate a list of tools to an agent.
    """
    tool_ids = request.tool_ids
    if not tool_ids:
        raise HTTPException(status_code=400, detail="No tool IDs provided.")
    return associate_tools_to_agent(db, agent_id, tool_ids)

@agents.post("/agents/{agent_id}/tools/unassociate", status_code=200)
def unassociate_tools(
    agent_id: str,
    request: UnassociateToolsRequest,
    db: Session = Depends(get_db)
):
    """
    Unassociate a list of tools from an agent.
    """
    tool_ids = request.tool_ids
    if not tool_ids:
        raise HTTPException(status_code=400, detail="No tool IDs provided.")
    return unassociate_tools_from_agent(db, agent_id, tool_ids)


@agents.get("/agents/{agent_id}", response_model=AgentSchema, status_code=200)
def list_agent_and_tools(agent_id: str, db: Session = Depends(get_db)):
    """
    Retrieve an agent and its associated tools by agent ID.
    """
    agent = get_agent_with_tools(db, agent_id)
    return agent

@agents.get("/agents/name/{agent_name}", response_model=AgentSchema, status_code=200)
def list_agent_and_tools_by_name(agent_name: str, db: Session = Depends(get_db)):
    """
    Retrieve an agent and its associated tools by agent name.
    """
    agent = get_agent_with_tools_by_name(db, agent_name)
    return agent



