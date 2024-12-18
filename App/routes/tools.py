from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.connection import get_db
from database.models.tools import ToolModel
from database.models.webhooks import WebhookModel
from AgentWrapper.tools import ToolManager
import uuid
import copy

router = APIRouter()


from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class ToolConfig(BaseModel):
    func: str = Field("generic_api_call", description="The function that will be called when using this tool.")
    return_direct: bool = Field(False, description="If True, the agent's response will be returned directly without formatting.")
    endpoint_url: str = Field(..., description="The API endpoint URL.")
    method: str = Field("GET", description="HTTP method to use, e.g., GET, POST, PUT.")
    headers: Dict[str, Any] = Field(default_factory=dict, description="HTTP headers to send with the request.")
    params: Dict[str, Any] = Field(default_factory=dict, description="Query parameters for the request.")
    data: Dict[str, Any] = Field(default_factory=dict, description="JSON body for the request if applicable.")
    input_location: str = Field("params", description="Where to place the user's query. One of 'params', 'data', 'headers', or 'path'.")
    input_key: str = Field("query", description="The key under which the user's query will be placed.")

class ToolCreateRequest(BaseModel):
    name: str = Field(..., description="The name of the tool.")
    description: str = Field("", description="A short description of what the tool does.")
    config: ToolConfig = Field(..., description="Configuration for the tool.")
    webhook_url: Optional[str] = Field(None, description="An optional webhook URL for external integrations.")
    is_active: bool = Field(True, description="If False, the tool should not be used.")
    api_key: Optional[str] = Field(None, description="An optional API key if needed by the tool.")

    class Config:
        schema_extra = {
            "example": {
                "name": "WeatherTool",
                "description": "Fetches weather information",
                "config": {
                    "func": "generic_api_call",
                    "return_direct": True,
                    "endpoint_url": "https://api.weather.com/v3/weather/conditions",
                    "method": "GET",
                    "headers": {"Authorization": "Bearer YOUR_API_KEY"},
                    "params": {"units": "metric"},
                    "data": {},
                    "input_location": "params",
                    "input_key": "query"
                },
                "webhook_url": "https://make.com/webhook",
                "is_active": True,
                "api_key": "auth-key",
            }
        }

class ToolUpdateConfig(BaseModel):
    func: Optional[str] = Field(None, description="The function to call when using this tool.")
    return_direct: Optional[bool] = Field(None, description="If True, return the agent's response directly.")
    endpoint_url: Optional[str] = Field(None, description="The updated API endpoint URL.")
    method: Optional[str] = Field(None, description="The updated HTTP method.")
    headers: Optional[Dict[str, Any]] = Field(None, description="Updated HTTP headers.")
    params: Optional[Dict[str, Any]] = Field(None, description="Updated query params.")
    data: Optional[Dict[str, Any]] = Field(None, description="Updated JSON body.")
    input_location: Optional[str] = Field(None, description="Where to place the user's query.")
    input_key: Optional[str] = Field(None, description="The key under which the user's query will be placed.")

class ToolUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Update the tool's name.")
    description: Optional[str] = Field(None, description="Update the tool's description.")
    config: Optional[ToolUpdateConfig] = Field(None, description="Partial updates to the tool's configuration.")
    webhook_url: Optional[str] = Field(None, description="Update the webhook URL if needed.")
    is_active: Optional[bool] = Field(None, description="Activate/deactivate the tool.")
    api_key: Optional[str] = Field(None, description="Update the API key if needed.")

    class Config:
        schema_extra = {
            "example": {
                "name": "WeatherToolUpdated",
                "description": "Updated description for the weather tool",
                "config": {
                    "endpoint_url": "https://api.weather.com/v3/weather/forecast",
                    "method": "POST",
                    "params": {"units": "imperial"}
                },
                "is_active": False
            }
        }


@router.post("/tools/create")
def create_tool_with_webhook(request: ToolCreateRequest, db: Session = Depends(get_db)):
    """Create a new tool and its associated webhook."""
    tool_data = {
        "name": request.name,
        "description": request.description,
        "config": request.config.model_dump(),
        "is_active": request.is_active,
    }
    tool_response = ToolManager.create_tool_in_db(tool_data, db)

    new_webhook = WebhookModel(
        id=str(uuid.uuid4()),
        tool_id=tool_response["tool_id"],
        url=request.webhook_url,
        api_key=request.api_key,
        description=request.description,
        is_active=request.is_active,
    )
    db.add(new_webhook)
    db.commit()

    return {"message": f"Tool '{request.name}' and its webhook created successfully.", "tool_id": tool_response["tool_id"]}


@router.get("/tools/list")
def list_tools(db: Session = Depends(get_db)):
    """List all tools."""
    return ToolManager.list_tools(db)


@router.get("/tools/details/{tool_id}")
def get_tool_details(tool_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a specific tool."""
    tool = db.query(ToolModel).filter(ToolModel.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool with ID '{tool_id}' not found.")

    webhook = db.query(WebhookModel).filter(WebhookModel.tool_id == tool.id).first()
    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "config": tool.config,
        "is_active": tool.is_active,
        "webhook": {
            "id": webhook.id if webhook else None,
            "url": webhook.url if webhook else None,
            "api_key": webhook.api_key if webhook else None,
            "description": webhook.description if webhook else None,
            "is_active": webhook.is_active if webhook else None,
        },
    }


@router.put("/tools/update/{tool_id}")
def update_tool_and_webhook(tool_id: str, request: ToolUpdateRequest, db: Session = Depends(get_db)):
    """Update an existing tool and its associated webhook."""
    tool = db.query(ToolModel).filter(ToolModel.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool with ID '{tool_id}' not found.")

    for key, value in request.dict(exclude_unset=True).items():
        if hasattr(tool, key):
            setattr(tool, key, value)
    db.commit()

    webhook = db.query(WebhookModel).filter(WebhookModel.tool_id == tool_id).first()
    if webhook:
        if request.webhook_url:
            webhook.url = request.webhook_url
        if request.api_key:
            webhook.api_key = request.api_key
        if request.description:
            webhook.description = request.description
        if request.is_active is not None:
            webhook.is_active = request.is_active
        db.commit()

    return {"message": f"Tool '{tool.name}' and its webhook updated successfully."}


@router.delete("/tools/delete/{tool_id}")
def delete_tool_and_webhook(tool_id: str, db: Session = Depends(get_db)):
    """Delete a tool and its associated webhook."""
    tool = db.query(ToolModel).filter(ToolModel.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool with ID '{tool_id}' not found.")
    db.delete(tool)

    webhook = db.query(WebhookModel).filter(WebhookModel.tool_id == tool_id).first()
    if webhook:
        db.delete(webhook)

    db.commit()
    return {"message": f"Tool '{tool.name}' and its webhook deleted successfully."}


@router.post("/tools/duplicate/{tool_id}")
def duplicate_tool(tool_id: str, db: Session = Depends(get_db)):
    """Duplicate an existing tool."""
    tool = db.query(ToolModel).filter(ToolModel.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool with ID '{tool_id}' not found.")

    duplicated_tool = copy.deepcopy(tool)
    duplicated_tool.id = str(uuid.uuid4())
    duplicated_tool.name = f"{tool.name}_copy"
    db.add(duplicated_tool)
    db.commit()

    return {"message": f"Tool '{tool.name}' duplicated successfully.", "new_tool_id": duplicated_tool.id}


@router.post("/tools/activate/{tool_id}")
def activate_tool(tool_id: str, db: Session = Depends(get_db)):
    """Activate a tool."""
    tool = db.query(ToolModel).filter(ToolModel.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool with ID '{tool_id}' not found.")

    tool.is_active = True
    db.commit()

    return {"message": f"Tool '{tool.name}' activated successfully."}


@router.post("/tools/deactivate/{tool_id}")
def deactivate_tool(tool_id: str, db: Session = Depends(get_db)):
    """Deactivate a tool."""
    tool = db.query(ToolModel).filter(ToolModel.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool with ID '{tool_id}' not found.")

    tool.is_active = False
    db.commit()

    return {"message": f"Tool '{tool.name}' deactivated successfully."}


@router.get("/tools/{tool_id}/action-usage")
def get_tool_action_usage(tool_id: str, db: Session = Depends(get_db)):
    """List actions and their usage within a tool."""
    # Example: Track tool usage stats if implemented
    tool = db.query(ToolModel).filter(ToolModel.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool with ID '{tool_id}' not found.")

    # Placeholder: Implement actual usage tracking
    usage_stats = {"calls": 42, "errors": 2, "success_rate": 95.24}

    return {
        "tool_id": tool_id,
        "tool_name": tool.name,
        "usage": usage_stats,
    }
