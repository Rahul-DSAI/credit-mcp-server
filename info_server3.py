import os
from datetime import datetime

from uvicorn import run
from starlette.routing import Route
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from mcp.server.fastmcp import FastMCP
from mcp.server.session import ServerSession
from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from mcp.server.sse import SseServerTransport
import logging

# ── Logging setup ──
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("client")

# ─── Configuration ──────────────────────────────────────────────────────────────

os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY", "")

mcp = FastMCP(
    "my-project",
    settings={"initialization_timeout": 10.0}
)

# ─── Optional Monkey‑Patch Workaround ────────────────────────────────────────────
old_recv = ServerSession._received_request

async def _recv_no_crash(self, *args, **kwargs):
    try:
        return await old_recv(self, *args, **kwargs)
    except RuntimeError:
        return

ServerSession._received_request = _recv_no_crash

# ─── Register Your Tools ─────────────────────────────────────────────────────────

@mcp.tool()
def get_restaurants_nearby(latitude: float, longitude: float):
    print(f"[DEBUG] get_restaurants_nearby called with latitude={latitude}, longitude={longitude}")
    query = f"restaurants near latitude {latitude}, longitude {longitude}"
    search = GoogleSerperAPIWrapper(type="places")
    results = search.results(query)
    return results

@mcp.tool()
def get_weather(latitude: float, longitude: float):
    print(f"[DEBUG] get_weather called with latitude={latitude}, longitude={longitude}")
    query = f"current weather near latitude {latitude}, longitude {longitude}"
    search = GoogleSerperAPIWrapper(type="search", num=5)
    results = search.results(query)
    return results

@mcp.tool()
def get_time():
    current_time = datetime.now().strftime("Current time is %Y-%m-%d %H:%M:%S")
    return current_time

# ─── Define the SSE handler ──────────────────────────────────────────────────────

async def handle_sse(request):
    sse_transport = SseServerTransport("/messages/")
    async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
        read_stream, write_stream = streams
        session_id = str(request.scope.get("session_id"))
        logger.debug(f"Sending session_id to client: {session_id}")

        # Fixed: use a dictionary instead of a nonexistent method
        await mcp.run(write_stream, read_stream, {"user": "anonymous"})

# ─── App Mounting ────────────────────────────────────────────────────────────────

app = Starlette(debug=True, routes=[
    Route("/sse", handle_sse),
])

# ─── Run Server ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000, log_level="debug")
