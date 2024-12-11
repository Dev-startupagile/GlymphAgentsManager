from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.connection import get_db
from database.models.webhooks import WebhookModel
from database.models.tools import ToolModel
import uuid

router = APIRouter()

# Pydantic models for validation

class WebhookCreateRequest(BaseModel):
    url: str
    api_key: str
    description: str = None
    is_active: bool = True

    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com/webhook",
                "api_key": "webhook-api-key",
                "description": "A webhook for sending notifications",
                "is_active": True,
            }
        }


class WebhookUpdateRequest(BaseModel):
    url: str = None
    api_key: str = None
    description: str = None
    is_active: bool = None

    class Config:
        schema_extra = {
            "example": {
                "url": "https://updated-example.com/webhook",
                "api_key": "updated-api-key",
                "description": "Updated webhook description",
                "is_active": False,
            }
        }


@router.post("/webhooks/create")
def create_webhook(request: WebhookCreateRequest, db: Session = Depends(get_db)):
    """
    Create a new webhook.
    """
    new_webhook = WebhookModel(
        id=str(uuid.uuid4()),
        url=request.url,
        api_key=request.api_key,
        description=request.description,
        is_active=request.is_active,
    )
    db.add(new_webhook)
    db.commit()
    return {"message": "Webhook created successfully.", "webhook_id": new_webhook.id}


@router.get("/webhooks/list")
def list_webhooks(db: Session = Depends(get_db)):
    """
    List all webhooks.
    """
    webhooks = db.query(WebhookModel).all()
    return [
        {
            "id": webhook.id,
            "url": webhook.url,
            "api_key": webhook.api_key,
            "description": webhook.description,
            "is_active": webhook.is_active,
        }
        for webhook in webhooks
    ]


@router.get("/webhooks/details/{webhook_id}")
def get_webhook_details(webhook_id: str, db: Session = Depends(get_db)):
    """
    Retrieve details of a specific webhook by ID.
    """
    webhook = db.query(WebhookModel).filter(WebhookModel.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail=f"Webhook with ID '{webhook_id}' not found.")
    return {
        "id": webhook.id,
        "url": webhook.url,
        "api_key": webhook.api_key,
        "description": webhook.description,
        "is_active": webhook.is_active,
    }


@router.put("/webhooks/update/{webhook_id}")
def update_webhook(webhook_id: str, request: WebhookUpdateRequest, db: Session = Depends(get_db)):
    """
    Update an existing webhook by ID.
    """
    webhook = db.query(WebhookModel).filter(WebhookModel.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail=f"Webhook with ID '{webhook_id}' not found.")

    for key, value in request.dict(exclude_unset=True).items():
        if hasattr(webhook, key):
            setattr(webhook, key, value)

    db.commit()
    return {"message": f"Webhook '{webhook_id}' updated successfully."}


@router.delete("/webhooks/delete/{webhook_id}")
def delete_webhook(webhook_id: str, db: Session = Depends(get_db)):
    """
    Delete a webhook by ID.
    """
    webhook = db.query(WebhookModel).filter(WebhookModel.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail=f"Webhook with ID '{webhook_id}' not found.")

    db.delete(webhook)
    db.commit()
    return {"message": f"Webhook '{webhook_id}' deleted successfully."}


@router.post("/webhooks/link/{webhook_id}/tool/{tool_id}")
def link_webhook_to_tool(webhook_id: str, tool_id: str, db: Session = Depends(get_db)):
    """
    Link a webhook to a specific tool.
    """
    webhook = db.query(WebhookModel).filter(WebhookModel.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail=f"Webhook with ID '{webhook_id}' not found.")

    tool = db.query(ToolModel).filter(ToolModel.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool with ID '{tool_id}' not found.")

    # Link the webhook to the tool
    webhook.tool_id = tool.id
    db.commit()

    return {"message": f"Webhook '{webhook_id}' linked to Tool '{tool_id}'."}
