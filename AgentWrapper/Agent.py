from sqlalchemy.orm import Session
from fastapi import HTTPException
from database.models.agent import AgentModel
from AgentWrapper.factories import AgentFactory
import uuid
import logging
from typing import Any, Dict

logger = logging.getLogger("AgentManager")
if not logger.handlers:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


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
        existing_agent = db.query(AgentModel).filter(AgentModel.name == request["name"]).first()
        if existing_agent:
            logger.error(f"Agent with name '{request['name']}' already exists.")
            raise HTTPException(status_code=400, detail=f"Agent with name '{request['name']}' already exists.")

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
        Retrieves an agent and its tools from the database and uses it to process input.
        
        :param name: The name of the agent.
        :param input_text: The input to be processed by the agent.
        :param db: The database session.
        :return: The response from the agent.
        """
        logger.debug(f"Fetching agent '{name}' from the database.")

        agent_config = db.query(AgentModel).filter(AgentModel.name == name).first()
        if not agent_config:
            logger.error(f"Agent '{name}' not found in the database.")
            raise HTTPException(status_code=404, detail=f"Agent '{name}' not found.")

        tools_config = [
            {
                "name": tool.name,
                "description": tool.description,
                "config": tool.config
            }
            for tool in agent_config.tools if tool.is_active
        ]

        logger.debug(f"Parsed tools for agent '{name}': {tools_config}")

        try:
            # Create the agent with tools
            agent = AgentFactory.create_agent({
                "name": agent_config.name,
                "description": agent_config.description,
                "llm_type": agent_config.llm_type,
                "llm_config": agent_config.llm_config,
                "prompt_template": agent_config.prompt_template,
                "fallback_prompt": agent_config.fallback_prompt
            }, tools_config)
            logger.info(f"Agent '{name}' successfully recreated with tools.")
        except Exception as e:
            logger.exception(f"Failed to recreate agent '{name}': {e}")
            raise HTTPException(status_code=500, detail=f"Failed to recreate agent '{name}'.")

        try:
            # Prepare the input dictionary
            agent_input = {
                "input": input_text,
                "intermediate_steps": {}
            }

            # Invoke the agent
            response = agent.invoke(
                agent_input,
                config={"configurable": {"session_id": "session-789"}} 
            )
            logger.info(f"Agent '{name}' processed input successfully.")
            return {"response": response}

        except Exception as e:
            logger.exception(f"Agent '{name}' failed to process input: {e}")
            raise HTTPException(status_code=500, detail=f"Agent '{name}' failed to process input.")
