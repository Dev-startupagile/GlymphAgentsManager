from sqlalchemy.orm import Session
from fastapi import HTTPException
from database.models.tools import ToolModel
from database.models.webhooks import WebhookModel
import uuid

class ToolManager:
    """Handles the lifecycle of tools and their associated webhooks."""

    @staticmethod
    def create_tool_in_db(request: dict, db: Session):
        """
        Creates and saves a tool configuration in the database.
        Expected keys in request: 'name', 'config'.
        Optional keys: 'description', 'is_active', 'api_key'.
        """
        if "name" not in request:
            raise HTTPException(status_code=400, detail="Tool 'name' is required.")
        if "config" not in request:
            raise HTTPException(status_code=400, detail="Tool 'config' is required.")

        existing_tool = db.query(ToolModel).filter(ToolModel.name == request["name"]).first()
        if existing_tool:
            raise HTTPException(status_code=400, detail=f"Tool with name '{request['name']}' already exists.")

        new_tool = ToolModel(
            id=str(uuid.uuid4()),
            name=request["name"],
            description=request.get("description", ""),
            config=request["config"],
            is_active=request.get("is_active", True),
            api_key=request.get("api_key"),
        )

        try:
            db.add(new_tool)
            db.commit()
            return {"message": f"Tool '{request['name']}' created successfully.", "tool_id": new_tool.id}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create tool: {str(e)}")

    @staticmethod
    def create_webhook_for_tool(tool_id: str, request: dict, db: Session):
        """
        Creates a webhook for an existing tool.
        """
        # Check if the tool exists
        tool = db.query(ToolModel).filter(ToolModel.id == tool_id).first()
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool with ID '{tool_id}' not found.")

        # Check if a webhook already exists for this tool
        existing_webhook = db.query(WebhookModel).filter(WebhookModel.tool_id == tool_id).first()
        if existing_webhook:
            raise HTTPException(status_code=400, detail=f"Webhook already exists for tool '{tool.name}'.")

        # Create and save the webhook
        new_webhook = WebhookModel(
            id=str(uuid.uuid4()),
            tool_id=tool_id,
            url=request["url"],
            api_key=request["api_key"],
            description=request.get("description", ""),
            is_active=request.get("is_active", True),
        )
        db.add(new_webhook)
        db.commit()
        return {"message": f"Webhook created for tool '{tool.name}'.", "webhook_id": new_webhook.id}

    @staticmethod
    def update_webhook(webhook_id: str, request: dict, db: Session):
        """
        Updates an existing webhook.
        """
        # Check if the webhook exists
        webhook = db.query(WebhookModel).filter(WebhookModel.id == webhook_id).first()
        if not webhook:
            raise HTTPException(status_code=404, detail=f"Webhook with ID '{webhook_id}' not found.")

        # Update the webhook fields
        for key, value in request.items():
            if hasattr(webhook, key):
                setattr(webhook, key, value)

        db.commit()
        return {"message": f"Webhook '{webhook_id}' updated successfully."}

    @staticmethod
    def delete_webhook(webhook_id: str, db: Session):
        """
        Deletes a webhook by ID.
        """
        # Check if the webhook exists
        webhook = db.query(WebhookModel).filter(WebhookModel.id == webhook_id).first()
        if not webhook:
            raise HTTPException(status_code=404, detail=f"Webhook with ID '{webhook_id}' not found.")

        # Delete the webhook
        db.delete(webhook)
        db.commit()
        return {"message": f"Webhook '{webhook_id}' deleted successfully."}

    @staticmethod
    def list_webhooks_for_tool(tool_id: str, db: Session):
        """
        Lists all webhooks associated with a tool.
        """
        # Check if the tool exists
        tool = db.query(ToolModel).filter(ToolModel.id == tool_id).first()
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool with ID '{tool_id}' not found.")

        # Fetch the webhooks linked to the tool
        webhooks = db.query(WebhookModel).filter(WebhookModel.tool_id == tool_id).all()
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

    @staticmethod
    def list_tools(db: Session):
        """
        Lists all tools in the database.
        """
        tools = db.query(ToolModel).all()
        return [{"id": tool.id, "name": tool.name, "description": tool.description} for tool in tools]

    @staticmethod
    def get_tool_by_name(name: str, db: Session):
        """
        Retrieves a tool by name.
        """
        tool = db.query(ToolModel).filter(ToolModel.name == name).first()
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{name}' not found.")
        return {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "config": tool.config,
            "is_active": tool.is_active,
            "api_key": tool.api_key,
        }

    @staticmethod
    def update_tool(name: str, request: dict, db: Session):
        """
        Updates a tool configuration by name.
        """
        tool = db.query(ToolModel).filter(ToolModel.name == name).first()
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{name}' not found.")

        for key, value in request.items():
            if hasattr(tool, key):
                setattr(tool, key, value)

        db.commit()
        return {"message": f"Tool '{name}' updated successfully."}

    @staticmethod
    def delete_tool(name: str, db: Session):
        """
        Deletes a tool by name.
        """
        tool = db.query(ToolModel).filter(ToolModel.name == name).first()
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{name}' not found.")

        db.delete(tool)
        db.commit()
        return {"message": f"Tool '{name}' deleted successfully."}
