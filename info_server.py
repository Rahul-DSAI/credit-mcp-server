import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from langchain_community.utilities import GoogleSerperAPIWrapper

print("[DEBUG] Setting SERPER_API_KEY...")
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY", "")

print("[DEBUG] Initializing MCP Server...")
mcp = FastMCP("Info")

# Tool: Get restaurants near given lat/lon
@mcp.tool()
def get_restaurants_nearby(latitude: float, longitude: float):
    print(f"[DEBUG] get_restaurants_nearby called with latitude={latitude}, longitude={longitude}")
    
    query = f"restaurants near latitude {latitude}, longitude {longitude}"
    print(f"[DEBUG] Search query: {query}")

    search = GoogleSerperAPIWrapper(type="places")
    print("[DEBUG] GoogleSerperAPIWrapper initialized for restaurants.")

    results = search.results(query)

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
    print("[DEBUG] Raw weather search results received.")

    snippets = [r["snippet"] for r in results.get("organic", []) if "weather" in r["snippet"].lower()]
    print(f"[DEBUG] Filtered weather snippets: {snippets}")

    result = snippets[0] if snippets else "Weather info not available."
    print(f"[DEBUG] Returning weather info: {result}")

    return result

# Tool: Get current time
@mcp.tool()
def get_time():
    print("[DEBUG] get_time called.")
    
    current_time = datetime.now().strftime("Current time is %Y-%m-%d %H:%M:%S")
    print(f"[DEBUG] Current time: {current_time}")

    return current_time
