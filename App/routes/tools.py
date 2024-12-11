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


class ToolCreateRequest(BaseModel):
    name: str
    description: str
    config: dict
    webhook_url: str
    is_active: bool = True
    api_key: str = None

    class Config:
        schema_extra = {
            "example": {
                "name": "WeatherTool",
                "description": "Fetches weather information",
                "config": {"func": "fetch_weather", "return_direct": True},
                "webhook_url": "https://make.com/webhook",
                "is_active": True,
                "api_key": "auth-key",
            }
        }


class ToolUpdateRequest(BaseModel):
    description: str = None
    config: dict = None
    webhook_url: str = None
    is_active: bool = None
    api_key: str = None

    class Config:
        schema_extra = {
            "example": {
                "description": "Updated tool description",
                "config": {"func": "updated_func"},
                "webhook_url": "https://updated-webhook.com",
                "is_active": False,
                "api_key": "updated-api-key",
            }
        }


@router.post("/tools/create")
def create_tool_with_webhook(request: ToolCreateRequest, db: Session = Depends(get_db)):
    """Create a new tool and its associated webhook."""
    tool_data = {
        "name": request.name,
        "description": request.description,
        "config": request.config,
        "is_active": request.is_active,
        "api_key": request.api_key,
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
