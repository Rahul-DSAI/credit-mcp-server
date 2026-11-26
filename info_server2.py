import os
from datetime import datetime
import logging

from uvicorn import run
from mcp.server.fastmcp import FastMCP
from mcp.server.session import ServerSession          # for optional monkey‑patch
from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from mcp.server.sse import SseServerTransport
from anyio import BrokenResourceError

# ─── Configuration ──────────────────────────────────────────────────────────────

os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY", "")

# Create the MCP server with a 10‑second initialization timeout
mcp = FastMCP(
    "my-project",
    settings={"initialization_timeout": 10.0}          # auto‑close sessions not initialized
)

# ─── Optional Monkey‑Patch Workaround ────────────────────────────────────────────
old_recv = ServerSession._received_request  # pylint: disable=protected-access

async def _recv_no_crash(self, *args, **kwargs):
    try:
        return await old_recv(self, *args, **kwargs)
    except RuntimeError:
        # ignore stray calls before full initialization
        return

ServerSession._received_request = _recv_no_crash  # pylint: disable=protected-access

# ─── Register Your Tools ─────────────────────────────────────────────────────────

@mcp.tool()
def get_restaurants_nearby(latitude: float, longitude: float):
    print(f"[DEBUG] get_restaurants_nearby called with latitude={latitude}, longitude={longitude}")
    
    query = f"restaurants near latitude {latitude}, longitude {longitude}"
    print(f"[DEBUG] Search query: {query}")

    search = GoogleSerperAPIWrapper(type="places")
    print("[DEBUG] GoogleSerperAPIWrapper initialized for restaurants.")

    results = search.results(query)
    print(f"[DEBUG] Search results: {results}")
    return results

# Tool: Get current weather near given lat/lon
@mcp.tool()
def get_weather(latitude: float, longitude: float):
    print(f"[DEBUG] get_weather called with latitude={latitude}, longitude={longitude}")
    
    query = f"current weather near latitude {latitude}, longitude {longitude}"
    print(f"[DEBUG] Weather search query: {query}")

    search = GoogleSerperAPIWrapper(type="search", num=5)
    print("[DEBUG] GoogleSerperAPIWrapper initialized for weather.")

    results = search.results(query)
    print(f"[DEBUG] Weather search results: {results}")

    return results

# Tool: Get current time
@mcp.tool()
def get_time():
    print("[DEBUG] get_time called.")
    
    current_time = datetime.now().strftime("Current time is %Y-%m-%d %H:%M:%S")
    print(f"[DEBUG] Current time: {current_time}")

    return current_time

# ─── Mount the Built‑in SSE App with Error Handling ─────────────────────────────

async def handle_sse(request):
    try:
        # Create an SSE transport instance
        sse_transport = SseServerTransport("/messages/")
        
        # Connect the SSE stream
        async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
            read_stream, write_stream = streams
            # Proceed with your app logic, using streams as needed
            await mcp.run(write_stream, read_stream, mcp.create_initialization_options())
    except BrokenResourceError:
        # Handle the case where the client disconnects unexpectedly
        logging.warning("SSE connection closed by client.")
    except Exception as e:
        logging.error(f"Error during SSE connection: {e}")

# ─── Run the Server with SSE Handling ─────────────────────────────────────────────

app = mcp.sse_app()

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000, log_level="debug")
