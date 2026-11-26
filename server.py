import os
from mcp.server.fastmcp import FastMCP
import requests

server = FastMCP("FoodRecommender")

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")  # Replace with your actual API key

@server.tool()
def parse_query(query: str) -> dict:
    """Extract food items and location from user query."""
    import re
    # Extract multiple food items
    food_match = re.findall(r"(pizza|burger|sushi|pasta|biryani|noodles|tacos)", query.lower())
    # Extract location
    loc_match = re.findall(r"in ([a-zA-Z\s]+)", query.lower())
    return {
        "food": food_match if food_match else None,
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
def search_nearby_restaurants_by_coords(latitude: float, longitude: float) -> list[str]:
    """Search for nearby restaurants using Google Places with latitude and longitude."""
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{latitude},{longitude}",
        "radius": 5000,  # Search within a 5 km radius
        "type": "restaurant",  # Search for restaurants
        "key": GOOGLE_PLACES_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        results = data.get("results", [])
        return [f"{place['name']} - {place['vicinity']}" for place in results[:5]]
    except Exception as e:
        return [f"Error fetching restaurants: {str(e)}"]

@server.tool()
def recommend_food_place(query: str) -> str:
    """Main entry: parses query and returns nearby restaurant suggestions for multiple food items."""
    parsed = parse_query(query)
    food_list = parsed["food"]
    location = parsed["location"]

    if not food_list or not location:
        return "Please provide both food items and a location in your query."

    response = f"Here are some places in {location}:\n"
    for food in food_list:
        response += f"\n{food.capitalize()} places:\n"
        places = search_nearby_restaurants(food, location)
        if not places:
            response += f"  - Sorry, I couldn't find any {food} places in {location}.\n"
        else:
            response += "\n".join(f"  - {place}" for place in places) + "\n"

    return response

@server.tool()
def recommend_food_place_by_coords(latitude: float, longitude: float) -> str:
    """Return nearby restaurant suggestions based on latitude and longitude."""
    places = search_nearby_restaurants_by_coords(latitude, longitude)

    if not places:
        return f"Sorry, I couldn't find any restaurants near {latitude}, {longitude}."

    response = f"Here are some restaurants near {latitude}, {longitude}:\n"
    response += "\n".join(f"  - {place}" for place in places)
    return response

if __name__ == "__main__":
    # Example coordinates to test the recommend_food_place_by_coords function
    latitude = 22.5726  # Example latitude (Kolkata)
    longitude = 88.3639  # Example longitude (Kolkata)
    print(f"Coordinates: {latitude}, {longitude}")
    response = recommend_food_place_by_coords(latitude, longitude)
    print("Response:", response)
