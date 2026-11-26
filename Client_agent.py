import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

import asyncio

print("[DEBUG] Initializing ChatOpenAI model...")
model = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY")
)

print("[DEBUG] Preparing StdioServerParameters...")
server_params = StdioServerParameters(
    command="python",
    args=["info_server.py"],  # Ensure the file path is correct and in the same directory or full path
)

async def main():
    print("[DEBUG] Starting stdio client...")
    async with stdio_client(server_params) as (read, write):
        print("[DEBUG] stdio_client started, setting up session...")

        async with ClientSession(read, write) as session:
            print("[DEBUG] Client session created, initializing connection...")

            await session.initialize()
            print("[DEBUG] Session initialized successfully.")

            print("[DEBUG] Loading MCP tools from server...")
            tools = await load_mcp_tools(session)
            print(f"[DEBUG] Loaded {len(tools)} tools: {[tool.name for tool in tools]}")

            print("[DEBUG] Creating ReAct agent with tools and model...")
            agent = create_react_agent(model, tools)

            # Ask the question with lat/lon
            query = "What are 5 restaurants near me and what's the weather like at latitude 22.5726 and longitude 88.3639?"
            print(f"[DEBUG] Sending agent query: {query}")
            response = await agent.ainvoke({"messages": query})

            print("[DEBUG] Received agent response:")
            print(response)

print("[DEBUG] Running main() loop...")
asyncio.run(main())
