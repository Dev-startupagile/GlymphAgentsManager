import os
from dotenv import load_dotenv
from fastapi import FastAPI
from app.routes.agents import router as agents_router
from app.routes.auth import auth as auth_router
from database.connection import engine
from database.models import Base

# Load environment variables from .env
load_dotenv()

# FastAPI app
app = FastAPI()

# Initialize database
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(agents_router, prefix="/agents", tags=["Agents"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Glymph Agents Manager API!"}
