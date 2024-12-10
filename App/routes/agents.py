from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.connection import get_db
from AgentWrapper.agent import AgentManager

router = APIRouter()

# Pydantic models for validation

class LLMConfig(BaseModel):
    model_name: str
    api_key: str = None  
    temperature: float = 0.7  
    max_tokens: int = 256  
    top_p: float = 1.0  
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0  
    

class AgentCreateRequest(BaseModel):
    name: str
    description: str
    llm_type: str
    llm_config: LLMConfig
    prompt_template: str
    fallback_prompt: str = "Sorry, something went wrong."


class AgentUseRequest(BaseModel):
    name: str
    input_text: str

@router.post("/create")
def create_agent(request: AgentCreateRequest, db: Session = Depends(get_db)):
    """Endpoint to create and save an agent configuration."""
    return AgentManager.create_agent_in_db(request.dict(), db)

@router.post("/use")
def use_agent(request: AgentUseRequest, db: Session = Depends(get_db)):
    """Endpoint to retrieve and use a saved agent."""
    return AgentManager.use_agent_from_db(request.name, request.input_text, db)

@router.delete("/delete")
def use_agent(request: AgentUseRequest, db: Session = Depends(get_db)):
    """Endpoint to retrieve and use a saved agent."""
    return AgentManager.use_agent_from_db(request.name, request.input_text, db)