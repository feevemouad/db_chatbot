from config import cfg
from sql.sql_tool import ExtendedSQLDatabaseToolkit
from sql_db_factory import sql_db_factory

FINAL_ANSWER_ACTION = "Final Answer:"

from langchain.sql_database import SQLDatabase
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_sql_agent
from langchain.agents import AgentExecutor
from langchain.agents.agent_types import AgentType
from typing import Tuple, Dict
from langchain.memory import ConversationBufferMemory
from langchain.prompts.chat import MessagesPlaceholder
from langchain.agents.agent import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish, OutputParserException
from langchain.agents.mrkl.prompt import FORMAT_INSTRUCTIONS

from typing import Union
import re

FINAL_ANSWER_ACTION = "Final Answer:"


class ExtendedMRKLOutputParser(AgentOutputParser):
    def get_format_instructions(self) -> str:
        return FORMAT_INSTRUCTIONS

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        includes_answer = self.includes_final_answer(text)
        regex = (
            r"Action\s*\d*\s*:[\s]*(.*?)[\s]*Action\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        )
        action_match = re.search(regex, text, re.DOTALL)
        if action_match:
            if includes_answer:
                raise OutputParserException(
                    "Parsing LLM output produced both a final answer "
                    f"and a parse-able action: {text}"
                )
            action = action_match.group(1).strip()
            action_input = action_match.group(2)
            tool_input = action_input.strip(" ")
            # ensure if its a well formed SQL query we don't remove any trailing " chars
            if tool_input.startswith("SELECT ") is False:
                tool_input = tool_input.strip('"')

            return AgentAction(action, tool_input, text)

        elif includes_answer:
            return AgentFinish(
                {"output": text.split(FINAL_ANSWER_ACTION)[-1].strip()}, text
            )

        if not re.search(r"Action\s*\d*\s*:[\s]*(.*?)", text, re.DOTALL):
            raise OutputParserException(
                f"Could not parse LLM output: `{text}`",
                observation="Invalid Format: Missing 'Action:' after 'Thought:'",
                llm_output=text,
                send_to_llm=True,
            )
        elif not re.search(
            r"[\s]*Action\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)", text, re.DOTALL
        ):
            raise OutputParserException(
                f"Could not parse LLM output: `{text}`",
                observation="Invalid Format:"
                " Missing 'Action Input:' after 'Action:'",
                llm_output=text,
                send_to_llm=True,
            )
        else:
            raise OutputParserException(f"Could not parse LLM output: `{text}`")

    def includes_final_answer(self, text):
        includes_answer = (
            FINAL_ANSWER_ACTION in text or FINAL_ANSWER_ACTION.lower() in text.lower()
        )
        return includes_answer

    @property
    def _type(self) -> str:
        return "mrkl"


def setup_memory() -> Tuple[Dict, ConversationBufferMemory]:
    """
    Sets up memory for the open ai functions agent.
    :return a tuple with the agent keyword pairs and the conversation memory.
    """
    agent_kwargs = {
        "extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
    }
    memory = ConversationBufferMemory(memory_key="memory", return_messages=True)

    return agent_kwargs, memory


def init_sql_db_toolkit() -> SQLDatabaseToolkit:
    db: SQLDatabase = sql_db_factory()
    toolkit = ExtendedSQLDatabaseToolkit(db=db, llm=cfg.llm)
    return toolkit


def initialize_agent(toolkit: SQLDatabaseToolkit) -> AgentExecutor:
    agent_executor = create_sql_agent(
        llm=cfg.llm,
        toolkit=toolkit,
        verbose=True,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        memory=setup_memory(),
        output_parser=ExtendedMRKLOutputParser(),
        handle_parsing_errors=True

    )
    return agent_executor


def agent_factory() -> AgentExecutor:
    sql_db_toolkit = init_sql_db_toolkit()
    agent_executor = initialize_agent(sql_db_toolkit)
    # agent = agent_executor.agent
    # agent.output_parser = ExtendedMRKLOutputParser()
    return agent_executor


if __name__ == "__main__":
    import os
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"]="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"
    os.environ["LANGCHAIN_PROJECT"]="kbasellms"

    agent_executor = agent_factory()
    # result = agent_executor.run("Describe all tables") 
    
                #     result: The tables "blacklist" and "lotterygains" have the following columns:

                # * blacklist:
                #         + id
                #         + nom
                # * lotterygains:
                #         + id
                #         + nom
                #         + gain

                # These are the relevant tables for querying, as per the schema.
                
    # result = agent_executor.run("Fetch the names from the lotterygains table.")
    # result: The names from the lotterygains table are ABDERRAHIM, Anonymous, BLACKLISTED.
    
    
    # result = agent_executor.run("What is the total sum of gains from the lotterygains table?")
    #result: $87.93
    
    
    # result = agent_executor.run("What is the average gain from the lotterygains table?")
    # result: The average gain from the lotterygains table is $4.89.
    
    # result = agent_executor.run("Get the total gains for all people who are not in the blacklist table.")
    # result: The total gains for all people who are not in the blacklist table is $87.93
    
    result = agent_executor.run("Describe all tables")
    print("result:",result)
