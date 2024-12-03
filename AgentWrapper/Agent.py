import logging
from typing import List, Dict, Optional, Any, Callable
from langchain.agents import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain.llms import OpenAI
from langchain_core.tools import Tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentWrapper")

class AgentConfig:
    def __init__(
        self,
        name: str,
        description: str,
        tools: List[Tool],
        llm_config: Dict[str, Any],
        prompt_template: str,
        chat_history: Optional[BaseChatMessageHistory] = None,
        fallback_prompt: Optional[str] = "I'm sorry, I couldn't process your request. Please try again.",
        verbose: bool = False,
    ):
        self.name = name
        self.description = description
        self.tools = tools
        self.llm_config = llm_config
        self.prompt_template = prompt_template
        self.chat_history = chat_history
        self.fallback_prompt = fallback_prompt
        self.verbose = verbose

        self._validate()

    def _validate(self):
        if not self.name:
            raise ValueError("AgentConfig must have a 'name'.")
        if not self.llm_config.get("api_key"):
            raise ValueError("AgentConfig must include an API key in 'llm_config'.")
        if not isinstance(self.tools, list) or not all(isinstance(t, Tool) for t in self.tools):
            raise ValueError("'tools' must be a list of Tool objects.")
        if not self.prompt_template:
            raise ValueError("'prompt_template' cannot be empty.")

def create_agent(config: AgentConfig):
    try:
        llm = OpenAI(
            model=config.llm_config.get("model", "gpt-4"),
            temperature=config.llm_config.get("temperature", 0.7),
            api_key=config.llm_config.get("api_key"),
            verbose=config.verbose,
        )
        logger.info(f"LLM created for agent '{config.name}'.")

        prompt = ChatPromptTemplate.from_messages([
            ("system", config.prompt_template)
        ])
        logger.info(f"Prompt template set for agent '{config.name}'.")

        agent = create_tool_calling_agent(llm, config.tools, prompt)
        logger.info(f"Agent '{config.name}' created with tools: {[tool.name for tool in config.tools]}.")

        if config.chat_history:
            agent = RunnableWithMessageHistory(
                agent=agent,
                history=config.chat_history,
                input_messages_key="input",
                history_messages_key="chat_history"
            )
            logger.info(f"Chat history enabled for agent '{config.name}'.")

        return agent

    except Exception as e:
        logger.error(f"Failed to create agent '{config.name}': {str(e)}")
        # fallback agent if creation fails
        return create_fallback_agent(config)

def create_fallback_agent(config: AgentConfig):
    """Creates a basic fallback agent with a default response."""
    def fallback_tool(input_text: str) -> str:
        return config.fallback_prompt

    fallback_prompt = ChatPromptTemplate.from_messages([
        ("system", "Fallback Agent: A simple response generator."),
    ])
    fallback_tool_instance = Tool(name="fallback", func=fallback_tool, description="Fallback tool.")
    fallback_agent = create_tool_calling_agent(
        OpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=config.llm_config.get("api_key")),
        tools=[fallback_tool_instance],
        prompt=fallback_prompt
    )
    logger.warning(f"Fallback agent created for '{config.name}'.")
    return fallback_agent

class AgentRegistry:
    """Registry to manage multiple agents."""
    def __init__(self):
        self._agents = {}

    def register(self, name: str, agent):
        if name in self._agents:
            logger.warning(f"Agent with name '{name}' is being overwritten.")
        self._agents[name] = agent
        logger.info(f"Agent '{name}' registered successfully.")

    def get(self, name: str):
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' not found in the registry.")
        return self._agents[name]

    def list_agents(self):
        return list(self._agents.keys())

agent_registry = AgentRegistry()
