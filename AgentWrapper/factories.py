import logging
from langchain.llms import OpenAI, Cohere
from langchain_community.llms import HuggingFaceHub
from langchain.agents import create_tool_calling_agent
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
    PromptTemplate,
)
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

import requests
from functools import partial
from typing import Any, Dict, List
from langchain.tools import Tool


logger = logging.getLogger("ToolFactory")
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("Factory")
logging.basicConfig(level=logging.INFO)

def generic_api_call(query: str, tool_config: Dict[str, Any]) -> str:
    """
    A generic API call function that uses the tool_config dictionary
    to determine which endpoint to call, which method to use, etc.

    Expected tool_config keys:
    - endpoint_url (str): The API endpoint URL.
    - method (str): HTTP method ('GET', 'POST', etc.). Defaults to 'GET'.
    - headers (dict): Optional headers for the request.
    - params (dict): Optional query parameters.
    - data (dict): Optional JSON body.
    - You can also include 'query_in_params' or 'query_in_data' booleans to control where 'query' goes.

    :param query: The input string from the user/agent. It can be used as a search term or input parameter.
    :param tool_config: A dictionary containing configuration for the API call.
    :return: The response text from the endpoint.
    """
    url = tool_config.get("endpoint_url")
    if not url:
        raise ValueError("No endpoint_url specified in tool config.")

    method = tool_config.get("method", "GET").upper()
    headers = tool_config.get("headers", {})
    params = tool_config.get("params", {})
    data = tool_config.get("data", {})

    if tool_config.get("query_in_params", True):
        params["query"] = query
    if tool_config.get("query_in_data", False):
        data["query"] = query

    if "{query}" in url:
        url = url.replace("{query}", query)

    response = requests.request(method, url, headers=headers, params=params, json=data)

    if not response.ok:
        raise ValueError(f"Request to {url} failed with status {response.status_code}: {response.text}")

    return response.text

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
            return ChatOpenAI(
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
    def create_agent(config: Dict[str, Any], tools: List[Dict[str, Any]]) -> Any:
        """
        Create an agent with its tools using the specified configuration.

        :param config: A dictionary containing the agent's configuration.
        :param tools: A list of tools (flows) with their configuration.
        :return: An instance of the created agent.
        """
        try:
            logger = logging.getLogger("AgentFactory")
            if not logger.handlers:
                logging.basicConfig(level=logging.INFO)

            llm = LLMFactory.create(config["llm_type"], config["llm_config"])
            logger.info(f"LLM created for agent '{config['name']}'.")

            langchain_tools = []
            for tool_config in tools:
                bound_func = partial(generic_api_call, tool_config=tool_config["config"])
                lc_tool = Tool(
                    name=tool_config["name"],
                    description=tool_config.get("description", ""),
                    func=bound_func,
                    return_direct=tool_config["config"].get("return_direct", False),
                )
                langchain_tools.append(lc_tool)
                logger.info(f"Tool '{tool_config['name']}' added to LangChain tools.")

            messages_placeholder = MessagesPlaceholder(variable_name='chat_history', optional=True)
            human_message_prompt = HumanMessagePromptTemplate(
                prompt=PromptTemplate(
                    input_variables=['input', 'userid'],
                    template='{input}'
                )
            )
            _agent_scratchpad = MessagesPlaceholder(variable_name='agent_scratchpad')

            system_prompt = SystemMessagePromptTemplate.from_template(config["prompt_template"])

            prompt = ChatPromptTemplate.from_messages([
                system_prompt,
                messages_placeholder,
                human_message_prompt,
                _agent_scratchpad
            ])
            logger.info(f"Prompt template set for agent '{config['name']}' with agent_scratchpad.")

            agent = create_tool_calling_agent(
                llm=llm,
                tools=langchain_tools,
                prompt=prompt
            )
            logger.info(f"Agent '{config['name']}' created successfully with tools and agent_scratchpad.")

            return agent

        except Exception as e:
            logger.error(f"Error creating agent '{config.get('name', 'Unnamed Agent')}': {e}")
            raise


class ToolFactory:
    """Factory for creating tools."""

    @staticmethod
    def create_tool(config: dict) -> Tool:
        """
        Create a tool instance based on the provided configuration.

        Example config:
        {
            "name": "WeatherTool",
            "description": "Fetches weather information",
            "config": {
                "func": "generic_api_call",           # The function to use
                "return_direct": True,
                "endpoint_url": "https://api.weather.com/v3/weather/conditions",
                "method": "GET",
                "headers": {"Authorization": "Bearer YOUR_API_KEY"},
                "params": {"units": "metric"},        # Default params
                "query_in_params": True               # Put the user query in the params as 'query'
            },
            "webhook_url": "https://make.com/webhook",
            "is_active": True,
            "api_key": "auth-key"
        }

        :param config: A dictionary containing the tool's configuration.
        :return: An instance of the tool.
        """
        try:
            func_name = config["config"].get("func", "generic_api_call")
            if func_name != "generic_api_call":
                raise ValueError("Only 'generic_api_call' is supported by this ToolFactory.")

            bound_func = partial(generic_api_call, tool_config=config["config"])

            tool = Tool(
                name=config["name"],
                description=config.get("description", ""),
                func=bound_func,
                return_direct=config["config"].get("return_direct", False),
            )

            logger.info(f"Tool '{config['name']}' created successfully.")
            return tool
        except Exception as e:
            logger.error(f"Failed to create tool: {e}")
            raise ValueError(f"Error creating tool: {str(e)}")


