from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.connection import get_db
from database.models.agent import AgentModel
from AgentWrapper.agent import AgentManager

agents = APIRouter()

# Pydantic models for request validation

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




