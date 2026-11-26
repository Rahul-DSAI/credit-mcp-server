import asyncio
import os
import logging

from mcp.client.websocket import websocket_client
from mcp.client.session import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_community.chat_models import ChatOpenAI

# ── Logging setup ──
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("client")

API_WS = os.getenv("MCP_WS_URL", "ws://localhost:8765/ws")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "REDACTED_OPENAI_KEY")
logger.debug(f"API_WS={API_WS}, OPENAI_API_KEY={'set' if OPENAI_API_KEY else 'missing'}")

async def main():
    logger.debug("Entering main()")

    # Connect to MCP server (WebSocket)
    async with websocket_client(API_WS) as (recv_stream, send_stream):
        logger.debug("WebSocket client connected, initializing MCP session")

        session = ClientSession(recv_stream, send_stream)
        await session.initialize()
        logger.debug("MCP session initialized")

        # Load tools from server
        tools = await load_mcp_tools(session)
        if not tools:
            logger.error("No tools were loaded. Check if the server supports tools/list and listChanged = True.")
            return

        logger.info(f"Loaded MCP tools: {[tool.name for tool in tools]}")

        # Set up the LLM (ChatOpenAI)
        llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            openai_api_key=OPENAI_API_KEY,
            temperature=0,
        )
        logger.debug("LLM initialized")

        # Create the ReAct agent
        agent = create_react_agent(llm, tools)
        logger.debug("ReAct agent created")

        # Example prompt
        prompt = (
            "List 5 restaurants near latitude 22.5726, longitude 88.3639, "
            "tell me the weather there, and give me the current time."
        )
        logger.info(f"Sending prompt: {prompt}")

        try:
            answer = await agent.invoke(prompt)
            logger.info(f"Agent response: {answer}")
            print("\n=== AGENT RESPONSE ===")
            print(answer)
        except Exception as e:
            logger.exception(f"Agent failed to complete prompt: {e}")

if __name__ == "__main__":
    logger.debug("Starting asyncio event loop")
    asyncio.run(main())
