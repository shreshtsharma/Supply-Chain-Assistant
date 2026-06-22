# agent.py
import asyncio
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model="llama-3.1-8b-instant",  
    temperature=0,
    max_retries=2,
)


async def initialize_agent():
    client = MultiServerMCPClient(
        {
            "supply-chain": {
                       "url": "https://supply-chain-assistant-production.up.railway.app/sse",
                        "transport": "sse",
            }
        }
    )
    tools = await client.get_tools()
    checkpointer = MemorySaver()
    agent = create_react_agent(llm, tools, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "streamlit-session"}}
    return agent, config

async def get_agent_response(agent, config, user_input):
    response = await agent.ainvoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=config
    )
    return response["messages"][-1].content

#terminal testing
if __name__ == "__main__":
    async def run():
        agent, config = await initialize_agent()
        print("Supply Chain Risk Assistant ready!")
        print("Type 'exit' to quit\n")
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                break
            result = await get_agent_response(agent, config, user_input)
            print(f"\nAssistant: {result}\n")
    
    asyncio.run(run())