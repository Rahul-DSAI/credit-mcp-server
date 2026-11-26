import os
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
import json
import re, json
# Initialize MCP server
server = FastMCP("FoodRecommender")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@server.tool()
def search_restaurants_by_coords(latitude: float, longitude: float) -> list[dict]:
    """
    Agent 1: Find the top 10 nearest restaurants (name + address).
    Ensures the model returns *only* a JSON array, and then safely parses it.
    """
    # 1) Strongly nudge the model to output *only* the JSON
    query = (
        f"Find the top 5 nearest restaurants to latitude {latitude}, "
        f"longitude {longitude}.  **Respond with *only* a JSON array** of objects "
        "with keys `name`, `address` and `(latitude,longitude)` —no markdown, no code fences, no extra text."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini-search-preview",
        web_search_options={},
        messages=[{"role": "user", "content": query}],
    )
    raw = resp.choices[0].message.content.strip()

    # 2) Try to extract a JSON array even if it's wrapped in fences or text
    #    a) look for ```json [ ... ] ```
    m = re.search(r"```json\s*(\[[\s\S]*?\])\s*```", raw)
    if m:
        json_text = m.group(1)
    else:
        # b) fallback: grab from first '[' to last ']'
        start = raw.find('[')
        end   = raw.rfind(']')
        if start != -1 and end != -1:
            json_text = raw[start:end+1]
        else:
            json_text = raw  # give it a shot

    # 3) Parse
    try:
        restaurants = json.loads(json_text)
    except json.JSONDecodeError:
        # if it still fails, return empty so orchestrator can handle it
        return []

    return restaurants

@server.tool()
def get_menu_details(name: str, address: str) -> str:
    """
    Agent 2: Given a restaurant name+address, list all menu items with:
      - rating
      - price
      - tags
      - mealtime
      - food concepts
      - food description
      - food preparation styles
    Returns a markdown‑style string.
    """
    query =(
        f"You are a restaurant data extraction assistant. "
        f"For the restaurant named \"{name}\" located at \"{address}\", "
        f"list every menu item of restaurant.  "
        f"For each menu item, provide exactly the following fields:\n"
        f"  • item_name — the name of the dish\n"
        f"  • rating — average customer rating out of 5 \n"
        f"  • price — price with respects to USD (null if unknown)\n"
        f"  • tags — a list of descriptive tags (e.g. [\"spicy\",\"vegetarian\"])\n"
        f"  • mealtime — one of [\"breakfast\",\"lunch\",\"dinner\",\"snack\",\"all day\"]\n"
        f"  • food_concepts — a list of high‑level concepts (e.g. [\"comfort food\",\"fusion\"])\n"
        f"  • description — a one‑sentence description of the dish\n"
        f"  • preparation_styles — a list of cooking/preparation methods (e.g. [\"grilled\",\"fried\"]) \n\n"
        f"**Output**: *only* a JSON array of objects, each object with exactly these keys. "
        f"Do not include any markdown, code fences, or extra text."
    )
    completion = client.chat.completions.create(
        model="gpt-4o-search-preview",
        web_search_options={},
        messages=[{"role": "user", "content": query}],
    )
    return completion.choices[0].message.content

@server.tool()
def recommend_food_place_by_coords(latitude: float, longitude: float) -> str:
    """
    Orchestrator: 
     1) Finds restaurants via Agent 1.
     2) For each, fetches menu details via Agent 2.
     3) Aggregates into one big markdown response.
    """
    restaurants = search_restaurants_by_coords(latitude, longitude)
    if not restaurants:
        return f"No restaurants found near {latitude},{longitude}."
    
    output = [f"## Top {len(restaurants)} restaurants near {latitude},{longitude}\n"]
    for idx, r in enumerate(restaurants, 1):
        name = r.get("name", "Unknown")
        addr = r.get("address", "Unknown address")
        print(r)
        output.append(f"### {idx}. {name}\n**Address:** {addr}\n")
        menu_md = get_menu_details(name, addr)
        output.append(menu_md)
        output.append("\n---\n")
    
    return "\n".join(output)

if __name__ == "__main__":
    # Test run for Kolkata coords
    latitude = 22.5726
    longitude = 88.3639
    print(recommend_food_place_by_coords(latitude, longitude))
