import os
from mcp.server.fastmcp import FastMCP
from openai import OpenAI

# Initialize MCP server
server = FastMCP("FoodRecommender")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@server.tool()
def search_nearest_restaurant_menu(latitude: float, longitude: float) -> str:
    """
    Uses gpt-4o-search-preview with web_search_options to find the nearest
    restaurant to the given coords and list its menu items.
    """
    # 1. Build a natural‑language query
    query = (
        f"Find the top 10 nearest restaurant to latitude {latitude}, "
        f"longitude {longitude}, and list all of its menu items."
    )

    # 2. Invoke the chat completion with web search enabled
    completion = client.chat.completions.create(
        model="gpt-4o-search-preview",
        web_search_options={},       # enable the built‑in web search tool
        messages=[
            {"role": "user", "content": query}
        ],
    )

    # 3. Extract and return the assistant’s answer
    return completion.choices[0].message.content

@server.tool()
def recommend_food_place_by_coords(latitude: float, longitude: float) -> str:
    """
    MCP entry point: wrap our search function so agent just passes lat/long.
    """
    return search_nearest_restaurant_menu(latitude, longitude)

if __name__ == "__main__":
    # Example run for Kolkata coords
    latitude = 22.5726
    longitude = 88.3639
    print(f"Coordinates: {latitude}, {longitude}")
    print("Response:", recommend_food_place_by_coords(latitude, longitude))
