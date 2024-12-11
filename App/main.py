import os
from dotenv import load_dotenv
from fastapi import FastAPI
from app.routes.agents import router as agents_router
from app.routes.auth import auth as auth_router
from app.routes.organizations import organizations as organizations_router
from app.routes.users import router as users_router
from app.routes.tools import router as tools_route
from app.routes.webhooks import router as webhook_route
from database.connection import engine
from database.models import Base

load_dotenv()

app = FastAPI()

# Initialize database
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(agents_router, prefix="/agents", tags=["Agents"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(organizations_router, prefix="/organizations", tags=["Organizations"])
app.include_router(tools_route, prefix="/tools", tags=["Tools"])
app.include_router(webhook_route, prefix="/webhooks", tags=["Webhooks"])


@app.get("/")
def read_root():
    return {"message": "Welcome to the Glymph Agents Manager API!"}
