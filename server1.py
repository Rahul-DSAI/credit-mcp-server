import os
from mcp.server.fastmcp import FastMCP
import requests

server = FastMCP("FoodRecommender")

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")  # Replace with your actual API key

@server.tool()
def parse_query(query: str) -> dict:
    """Extract food item and location from user query."""
    import re
    food_match = re.findall(r"(pizza|burger|sushi|pasta|biryani|noodles|tacos)", query.lower())
    loc_match = re.findall(r"in ([a-zA-Z\s]+)", query.lower())
    return {
        "food": food_match[0] if food_match else None,
        "location": loc_match[0] if loc_match else None
    }

@server.tool()
def search_nearby_restaurants(food: str, location: str) -> list[str]:
    """Search for nearby restaurants serving a food item using Google Places."""
    query = f"{food} restaurants in {location}"
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "key": GOOGLE_PLACES_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        results = data.get("results", [])
        return [f"{place['name']} - {place['formatted_address']}" for place in results[:5]]
    except Exception as e:
        return [f"Error fetching restaurants: {str(e)}"]

@server.tool()
def recommend_food_place(query: str) -> str:
    """Main entry: parses query and returns nearby restaurant suggestions."""
    parsed = parse_query(query)
    food = parsed["food"]
    location = parsed["location"]

    if not food or not location:
        return "Please provide both a food item and location in your query."

    places = search_nearby_restaurants(food, location)

    if not places:
        return f"Sorry, I couldn't find any {food} places in {location}."

    response = f"Here are some {food} places in {location}:\n"
    response += "\n".join(f"- {place}" for place in places)
    return response

if __name__ == "__main__":
    # Example query to test the recommend_food_place function
    sample_query = "Find pizza in Jyangra Kolkata - 700059"
    print("Query:", sample_query)
    response = recommend_food_place(sample_query)
    print("Response:", response)
