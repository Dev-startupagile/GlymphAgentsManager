from sqlalchemy.orm import Session
from fastapi import HTTPException
from database.models.agent import AgentModel
from AgentWrapper.factories import AgentFactory
import uuid
import logging

logger = logging.getLogger("AgentManager")
logging.basicConfig(level=logging.INFO)

class AgentManager:
    """Manages the lifecycle of agents, including creation and usage."""

    @staticmethod
    def create_agent_in_db(request: dict, db: Session):
        """
        Creates and saves an agent configuration in the database.

        :param request: The request data containing agent configuration.
        :param db: The database session.
        :return: A success message.
        """
        # Check if the agent name already exists
        existing_agent = db.query(AgentModel).filter(AgentModel.name == request["name"]).first()
        if existing_agent:
            logger.error(f"Agent with name '{request['name']}' already exists.")
            raise HTTPException(status_code=400, detail=f"Agent with name '{request['name']}' already exists.")

        # Save the agent configuration to the database
        new_agent = AgentModel(
            id=str(uuid.uuid4()),
            name=request["name"],
            description=request["description"],
            llm_type=request["llm_type"],
            llm_config=request["llm_config"],
            prompt_template=request["prompt_template"],
            fallback_prompt=request.get("fallback_prompt", "Sorry, something went wrong.")
        )
        db.add(new_agent)
        db.commit()

        logger.info(f"Agent '{request['name']}' created and saved to the database.")
        return {"message": f"Agent '{request['name']}' created successfully."}

    @staticmethod
    def use_agent_from_db(name: str, input_text: str, db: Session):
        """
        Retrieves an agent from the database and uses it to process input.

        :param name: The name of the agent.
        :param input_text: The input to be processed by the agent.
        :param db: The database session.
        :return: The response from the agent.
        """
        # Retrieve the agent configuration from the database
        agent_config = db.query(AgentModel).filter(AgentModel.name == name).first()
        if not agent_config:
            logger.error(f"Agent '{name}' not found in the database.")
            raise HTTPException(status_code=404, detail=f"Agent '{name}' not found.")

        # Recreate the agent using the factory
        try:
            agent = AgentFactory.create_agent({
                "name": agent_config.name,
                "description": agent_config.description,
                "llm_type": agent_config.llm_type,
                "llm_config": agent_config.llm_config,
                "prompt_template": agent_config.prompt_template,
                "fallback_prompt": agent_config.fallback_prompt
            })
            logger.info(f"Agent '{name}' successfully recreated.")

        except Exception as e:
            logger.error(f"Failed to recreate agent '{name}': {e}")
            raise HTTPException(status_code=500, detail=f"Failed to recreate agent '{name}'.")

        # Use the agent to process the input
        try:
            # Assuming `invoke_tool` is the placeholder logic for the agent
            response = agent.invoke_tool("input", {"input": input_text})  # Adjust this logic as needed
            logger.info(f"Agent '{name}' processed input successfully.")
            return {"response": response}

        except Exception as e:
            logger.error(f"Agent '{name}' failed to process input: {e}")
            raise HTTPException(status_code=500, detail=f"Agent '{name}' failed to process input.")
