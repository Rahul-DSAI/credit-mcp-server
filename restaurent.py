import os
from mcp.server.fastmcp import FastMCP
import requests

server = FastMCP("FoodRecommender")

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")  # Replace with your actual API key

@server.tool()
def search_restaurants_full_details(latitude: float, longitude: float) -> list[dict]:
    """
    Search nearby restaurants and return name, rating, coordinates, and address.
    """
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{latitude},{longitude}",
        "radius": 5000,
        "type": "restaurant",
        "key": GOOGLE_PLACES_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        results = data.get("results", [])
        restaurants = []

        for place in results[:5]:  # Limit to top 5
            name = place.get("name")
            rating = place.get("rating", "N/A")
            location = place.get("geometry", {}).get("location", {})
            lat = location.get("lat")
            lng = location.get("lng")
            address = place.get("vicinity", "Address not available")

            restaurants.append({
                "name": name,
                "rating": rating,
                "latitude": lat,
                "longitude": lng,
                "address": address
            })

        return restaurants

    except Exception as e:
        return [{"error": f"Failed to fetch data: {str(e)}"}]

@server.tool()
def recommend_restaurants_with_address(latitude: float, longitude: float) -> str:
    """
    Recommend nearby restaurants with name, rating, lat/long, and address.
    """
    restaurants = search_restaurants_full_details(latitude, longitude)

    if not restaurants or "error" in restaurants[0]:
        return f"Error: {restaurants[0]['error']}" if restaurants else "No results found."

    response = f"Top restaurants near ({latitude}, {longitude}):\n"
    for r in restaurants:
        response += (
            f"\n- {r['name']} | Rating: {r['rating']} | "
            f"Location: ({r['latitude']}, {r['longitude']}) | "
            f"Address: {r['address']}"
        )

    return response

if __name__ == "__main__":
    latitude = 22.5726  # Example latitude
    longitude = 88.3639  # Example longitude 
    result = recommend_restaurants_with_address(latitude, longitude)
    print(result)
