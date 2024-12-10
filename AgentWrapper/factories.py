from langchain.llms import OpenAI, Cohere
from langchain_community.llms import HuggingFaceHub
from langchain.agents import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
import logging

logger = logging.getLogger("AgentFactory")
logging.basicConfig(level=logging.INFO)

class LLMFactory:
    """Factory for creating LLM instances."""

    @staticmethod
    def create(llm_type: str, config: dict):
        """
        Create an LLM instance based on the specified type and configuration.

        :param llm_type: The type of LLM ('openai', 'cohere', 'huggingface').
        :param config: A dictionary of LLM-specific configuration (e.g., API key, model).
        :return: An instance of the LLM.
        """
        if llm_type == "openai":
            logger.info(f"Creating OpenAI LLM with config: {config}")
            return OpenAI(
                model=config.get("model", "gpt-4o"),
                temperature=config.get("temperature", 0.7),
                api_key=config["api_key"]
            )
        elif llm_type == "cohere":
            logger.info(f"Creating Cohere LLM with config: {config}")
            return Cohere(
                api_key=config["api_key"],
                model=config.get("model", "command-xlarge-nightly")
            )
        elif llm_type == "huggingface":
            logger.info(f"Creating Hugging Face LLM with config: {config}")
            return HuggingFaceHub(
                repo_id=config["repo_id"],
                api_token=config["api_key"]
            )
        else:
            logger.error(f"Unsupported LLM type: {llm_type}")
            raise ValueError(f"Unsupported LLM type: {llm_type}")


class AgentFactory:
    """Factory for creating agents."""

    @staticmethod
    def create_agent(config: dict):
        """
        Create an agent using the specified configuration.

        :param config: A dictionary containing the agent's configuration:
            - 'name': Name of the agent.
            - 'description': Description of the agent.
            - 'llm_type': The type of LLM ('openai', 'cohere', 'huggingface').
            - 'llm_config': Configuration for the LLM (API key, model).
            - 'prompt_template': The prompt template for the agent.
            - 'fallback_prompt': Fallback response for the agent.
        :return: An instance of the created agent.
        """
        try:
            llm = LLMFactory.create(config["llm_type"], config["llm_config"])
            logger.info(f"LLM created for agent '{config['name']}'.")
            prompt = ChatPromptTemplate.from_messages([("system", config["prompt_template"])])
            logger.info(f"Prompt template set for agent '{config['name']}'.")
            agent = create_tool_calling_agent(llm=llm, tools=[], prompt=prompt)  # no tools for now
            logger.info(f"Agent '{config['name']}' created successfully.")

            return agent

        except Exception as e:
            logger.error(f"Error creating agent '{config['name']}': {e}")
            raise
