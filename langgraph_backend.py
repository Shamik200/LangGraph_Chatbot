from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3

from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

import requests

load_dotenv()  # Load environment variables from .env file

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Tools......................................

search_tool = DuckDuckGoSearchRun()

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    A simple calculator that can add, subtract, multiply, or divide two numbers.
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "subtract":
            result = first_num - second_num
        elif operation == "multiply":
            result = first_num * second_num
        elif operation == "divide":
            if second_num == 0:
                return {"error": "Cannot divide by zero."}
            result = first_num / second_num
        else:
            return {"error": "Invalid operation. Please use add, subtract, multiply, or divide."}
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetches the current stock price for a given symbol using a public API.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=ED9F1H16AMELX986"
    r = requests.get(url)
    return r.json()

tools = [search_tool, calculator, get_stock_price]

llm_with_tools = llm.bind_tools(tools)

# --------------------------------------------

def chat_node(state: ChatState):
    """A node that handles chat messages."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")

chatbot = graph.compile(checkpointer=checkpointer)

# for message_chunk, metadata in chatbot.stream(
#     {'messages': [HumanMessage(content='What is Recipe to make pasta?')]},
#     config={'configurable': {'thread_id': 'thread_1'}},
#     stream_mode='messages'
# ):
#     if message_chunk.content:
#         print(message_chunk.content, end='', flush=True)

def retrieve_all_threads():
    
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)
