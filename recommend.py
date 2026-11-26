import os
from openai import OpenAI
import json

# Initialize OpenAI client (Groq/OpenRouter/OpenAI-compatible)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"))

# Load restaurant data
with open("restaurant_menu_data.json", "r", encoding="utf-8") as f:
    restaurants = json.load(f)

# Format restaurant info into a readable prompt chunk
def format_restaurants(restaurants):
    output = ""
    for entry in restaurants.values():
        rest = entry.get("restaurant", {})  # Get restaurant dictionary
        name = rest.get("name", "Unknown")
        address = rest.get("address", "Unknown")
        output += f"\n- {name} (Address: {address})\n"
        
        for dish in entry.get("menu", []):
            item_name = dish.get("itemName", "Unknown")
            rating = dish.get("rating", "N/A")
            output += f"    - {item_name} (Rating: {rating})\n"
    return output


# User input
user_info = {"tags": ["Caesar dressing", "Romaine lettuce", "Parmesan cheese", "croutons"],"location":"kolkata", "Dietary": ["High-protein"], "Mealtime": ["Lunch"], "Flavor Types": ["Creamy", " Savory", " Salty", " Crunchy"], "Food Concepts": ["Gourmet"], "isReprocessed": False, "Food Description": ["Gourmet"], "foodCategoryName": ["Soups and Salads"], "Food Preparation Styles": ["Grilled"]}

favorite_food = "Prawn Cutlets"

# Compose the prompt
prompt = f"""
You are a helpful food recommendation assistant. Based on the user's info, favorite food item, and the list of restaurants, suggest the top 10 food items that match their taste and are highly rated.

User Info:
- Location: {user_info['location']}
- Preferences: {user_info}

Favorite Food: {favorite_food}

Restaurant Menus:
{format_restaurants(restaurants)}

Please return the top 10 recommendations in this format:
1. <Dish> at <Restaurant> (Dish Rating: <X>) - Why it's a good match.
"""

# Make API call using OpenAI SDK style
response = client.chat.completions.create(
    model="gpt-4o-mini",  # or "gpt-4.1" depending on endpoint support
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0.7
)

# Output the result
print(response.choices[0].message.content)
