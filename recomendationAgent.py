import os
import time
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
import json
import re, json
# Initialize MCP server
server = FastMCP("FoodRecommender")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
food_choices = [{
        "Restaurant Name": "Flurys", 
        "Address": "18 Park Street, Park Street area, Kolkata, West Bengal 700071, India",
        "latitude": 22.5535,
        "longitude": 88.3512,
        "Item Name": "Chicken Patty",
        "Average Rating": 4.2,
        "price": 1.80,
        "foodInfo": "Savory puff pastry filled with chicken filling and baked till crispy.",
        "tags": "chicken, puff pastry, butter, flour, onion, garlic, spices",
        "My Rating": 3
    },
    {
        "Restaurant Name": "Oh! Calcutta", 
        "Address": "Forum Mall, 10/3 Elgin Road, Sreepally, Bhowanipore, Kolkata, West Bengal 700020, India",
        "latitude": 22.5283,
        "longitude": 88.3522,
        "Item Name": "Calcutta Fish Fry",
        "rating": 4.6,
        "price": 6.30,
        "foodInfo": "A classic Bengali starter featuring bhetki fish fillets marinated, coated in breadcrumbs, and deep-fried.",
        "tags": "bhetki fish, breadcrumbs, spices",
        "My Rating": 4
    },
    {
        "Restaurant Name": "Oh! Calcutta", 
        "Address": "Forum Mall, 10/3 Elgin Road, Sreepally, Bhowanipore, Kolkata, West Bengal 700020, India",
        "latitude": 22.5283,
        "longitude": 88.3522,
        "Item Name": "Bhetki Gondhoraj",
        "rating": 4.6,
        "price": 6.30,
        "foodInfo": "Freshwater bhetki fish marinated with Gondhoraj lemon and spices, then grilled to perfection.",
        "tags": "bhetki fish, Gondhoraj lemon, spices",
        "My Rating": 3.9
    }]


def extract_json_from_text(text):
    try:
        # Try to parse the whole content first (assuming it's pure JSON)
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: extract JSON array from within the text using regex
        json_matches = re.findall(r'\[.*?\]', text, re.DOTALL)
        for match in json_matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Failed to decode JSON from text:\n{text[:500]}")
    

@server.tool()
def search_restaurants_by_coords(latitude: float, longitude: float, top_k=10, radius=5) -> list[dict]:
    """
    Agent 1: Find the top 10 nearest restaurants (name + address).
    Ensures the model returns *only* a JSON array, and then safely parses it.
    """
    # 1) Strongly nudge the model to output *only* the JSON
    query = (
        f"Find the top {top_k} nearest(within {radius} km radius) restaurants to latitude {latitude}, "
        f"longitude {longitude}.  **Respond with *only* a JSON array** of objects "
        "with keys `name`, `address` and `exact location with(latitude,longitude)` and `distance(km)` —no markdown, no code fences, no extra text."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini-search-preview",
        web_search_options={},
        messages=[{"role": "user", "content": query}],
    )
    raw = resp.choices[0].message.content.strip()
    restaurants = extract_json_from_text(raw)
    return restaurants


@server.tool()
def get_recomendation_menu_details(name: str, address: str, liked_foods: list[dict], top_k=5) -> str:
    adon_fileds = """
    - itemName:  The name of the dish.
    - rating:  Average customer rating out of 5.
    - price:  Price with respect to USD.
    - matchPercentange:  recomendation score out of 100.
    - foodInfo: A short description about the food item.
    - tags: The main (8-10) `ingredients` or `key elements` or `Food Presentation` or `Food Preparation Styles` or `Flavor Types` or `Food Concepts` or `Dietary`, as a comma‑separated list.
    """
    query =(
        f"You are an Food Expert with knowledge in variety of food and its test and users choices over different foods depending on their liked foods and guven rating and test profile."
        f"For the restaurant named \"{name}\" located at \"{address}\", "
        f"list top {top_k} recomendaed menu item of restaurant, depending on my given food ratings and test profile:"
        f"{json.dumps(liked_foods)}"
        f"For each recomended menu item, provide exactly the following fields:\n"
        f"{adon_fileds}"
        f"**Output**: *only* a minified JSON array of objects, each object with exactly these keys. "
        f"Do not include any markdown, code fences, or extra text."
    )
    completion = client.chat.completions.create(
        model="gpt-4o-search-preview",
        messages=[{"role": "user", "content": query}],
    )
    return completion.choices[0].message.content



@server.tool()
def recommend_food_place_by_coords(latitude: float, longitude: float) -> str:
    restaurants = search_restaurants_by_coords(latitude, longitude)
    if not restaurants:
        return f"No restaurants found near {latitude},{longitude}."
    op = []
    # output = [f"## Top {len(restaurants)} restaurants near {latitude},{longitude}\n"]
    for idx, r in enumerate(restaurants, 1):
        name = r.get("name", "Unknown")
        addr = r.get("address", "Unknown address")
        print(r)
        # output.append(f"### {idx}. {name}\n**Address:** {addr}\n")
        menu_md = get_recomendation_menu_details(name, addr, food_choices)
        menu = extract_json_from_text(menu_md)
        op.extend([{**r, **m} for m in menu])
        # print("menu_md:: ",menu_md)
        # output.append(menu_md)
        # output.append("\n---\n")
    
    return op

if __name__ == "__main__":
    # Test run for Kolkata coords
    latitude = 22.5726
    longitude = 88.3639
    start = time.time()
    oo = recommend_food_place_by_coords(latitude, longitude)
    with open("x.json", "w") as f:
        json.dump(oo,f, indent=3)
    print(">>>>>", time.time() - start)