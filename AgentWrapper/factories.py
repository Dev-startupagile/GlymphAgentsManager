import logging
from langchain.llms import OpenAI, Cohere
from langchain_community.llms import HuggingFaceHub
from langchain.agents import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import Tool

logger = logging.getLogger("Factory")
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
    def create_agent(config: dict, tools: list[dict]):
        """
        Create an agent with its tools using the specified configuration.

        :param config: A dictionary containing the agent's configuration.
        :param tools: A list of tools (flows) with their configuration.
        :return: An instance of the created agent.
        """
        try:
            # Create the LLM
            llm = LLMFactory.create(config["llm_type"], config["llm_config"])
            logger.info(f"LLM created for agent '{config['name']}'.")

            # Create tools for the agent
            langchain_tools = []
            for tool_config in tools:
                langchain_tools.append(Tool(name=tool_config["name"], func=tool_config["config"]["func"]))

            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([("system", config["prompt_template"])])
            logger.info(f"Prompt template set for agent '{config['name']}'.")

            # Create the agent
            agent = create_tool_calling_agent(llm=llm, tools=langchain_tools, prompt=prompt)
            logger.info(f"Agent '{config['name']}' created successfully with tools.")

            return agent

        except Exception as e:
            logger.error(f"Error creating agent '{config['name']}': {e}")
            raise

logger = logging.getLogger("ToolFactory")
logging.basicConfig(level=logging.INFO)

class ToolFactory:
    """Factory for creating tools."""

    @staticmethod
    def create_tool(config: dict):
        """
        Create a tool instance based on the provided configuration.

        :param config: A dictionary containing the tool's configuration.
        :return: An instance of the tool.
        """
        try:
            tool = Tool(
                name=config["name"],
                description=config.get("description", ""),
                func=config["config"]["func"],  # The callable function the tool executes
                return_direct=config["config"].get("return_direct", False),
            )
            logger.info(f"Tool '{config['name']}' created successfully.")
            return tool
        except Exception as e:
            logger.error(f"Failed to create tool: {e}")
            raise ValueError(f"Error creating tool: {str(e)}")


