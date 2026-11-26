import os
import re
import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional

from mcp.server.fastmcp import FastMCP
from openai import OpenAI

# ——— Configuration —————————————————————————————————————————————————————
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY in your environment")

# Initialize MCP server & OpenAI client
server = FastMCP("FoodRecommender")
client = OpenAI(api_key=OPENAI_API_KEY)

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ——— Data Models —————————————————————————————————————————————————————
@dataclass
class Restaurant:
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@dataclass
class MenuItem:
    item_name: str
    rating: Optional[float]
    price: Optional[str]
    tags: List[str]
    mealtime: str
    food_concepts: List[str]
    description: str
    preparation_styles: List[str]

# ——— Utility: chunking output ——————————————————————————————————————————
def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
    """
    Split a large text into chunks not exceeding max_chars, preserving line boundaries.
    """
    lines = text.splitlines(keepends=True)
    chunks: List[str] = []
    current: str = ""
    for line in lines:
        if len(current) + len(line) > max_chars:
            chunks.append(current)
            current = line
        else:
            current += line
    if current:
        chunks.append(current)
    return chunks

# ——— Agent 1: Search Restaurants —————————————————————————————————————————
@server.tool()
@lru_cache(maxsize=32)
def search_restaurants_by_coords(latitude: float, longitude: float) -> List[Restaurant]:
    """
    Finds the top 5 nearest restaurants to the given coords.
    Returns a list of Restaurant objects.
    """
    prompt = (
        f"Find the top 5 nearest restaurants to latitude {latitude}, longitude {longitude}.  "
        "Respond with *only* a JSON array of objects with keys "
        "`name`, `address`, `latitude`, and `longitude`. No markdown, no code fences, no extra text."
    )
    logger.info("Searching restaurants at %s,%s", latitude, longitude)
    resp = client.chat.completions.create(
        model="gpt-4o-search-preview",
        web_search_options={},
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.choices[0].message.content.strip()

    # Extract JSON array
    m = re.search(r"```json\s*(\[[\s\S]*?\])\s*```", raw)
    json_text = m.group(1) if m else raw[raw.find('['): raw.rfind(']')+1]

    try:
        data = json.loads(json_text)
        return [
            Restaurant(
                name=entry["name"],
                address=entry["address"],
                latitude=entry.get("latitude"),
                longitude=entry.get("longitude"),
            )
            for entry in data
        ]
    except Exception as e:
        logger.error("Failed to parse restaurants JSON: %s", e)
        return []

# ——— Agent 2: Fetch Menu Details —————————————————————————————————————————
@server.tool()
def get_menu_details(name: str, address: str) -> List[MenuItem]:
    """
    Agent 2: Given a restaurant name+address, returns a list of MenuItem objects
    with full details—filling in any <REPLACE_ME> masks and populating all
    required fields in JSON.
    """
    system_message = """
You are a Mask Filler With Expertise in food industry knowledge which includes ideas in different food concepts and their preparation style, taste, ingredients etc.

Your primary task is to fill in the masked placeholders in the provided sentences.

The placeholders are represented by <REPLACE_ME>. You will replace these tokens with the most suitable sequence of words to form a coherent and contextually appropriate sentence. After filling in the masks, return the modified sentence.

Instructions:
- Carefully read the input sentence and understand the context provided by the existing words.
- Replace each <REPLACE_ME> token with the most appropriate sequence of words to form a coherent and contextually accurate sentence.

In addition to completing the placeholders, fill in the following categories for each menu item:
- foodInfo: a short description about the food item.
- tags: the main (7–8) ingredients or key elements, as a comma‑separated list.
- Food Presentation: pick best match labels from [Chilled, Epicurean, Frozen, Upscale, Artisanal, Haute cuisine, Locally sourced, Delicatessen, Delectable, Fast Food, Decadent, Handcrafted, Gastronomic, Exquisite, Rustic, Gourmet, Comfort food, Fusion, Homestyle, Wholesome, Hot, Nouvelle cuisine, Crafted].
- Food Preparation Styles: pick best match labels from [Protein, Braised, Baked, Stir‑fried, Marinated, Deep Fried, Grilled, Charred, Roasted, Caramelized, Broiled, Poached, Sous vide, Breaded, Dessert, Steamed, Fried, Caffeine‑free, Simmered, Sauteed, Smoked, Sugar‑free, Griddled].
- Flavor Types: pick best match labels from [Creamy, Robust, Velvety, Buttery, Mild, Salty, Crunchy, Rich, Aromatic, Sweet, Sour, Tangy, Fruity, Piquant, Decadent, Savory, Soft, Malty, Spicy, Sharp, Peppery, Tart, Refreshing, Bitter, Citrusy].
- Food Concepts: pick best match labels from [Provencal, Viennese, Artisanal, Fromagerie, Delicatessen, Charcuterie, Pâtisserie, Homemade, Farmstead, Rotisserie, Gourmet, Boulangerie, Market‑style, Localvore, Gastronomic, Epicurean, Culinary, Rustic, Brasserie, From Scratch, Bistro].
- Mealtime: pick one of [Dinner, Brunch, Breakfast, Snack, Lunch].
- Dietary: pick best match labels from [FODMAP, Gluten‑free, Keto, Low‑fat, Organic, Cooked, Vegan, Low‑carb, Plant‑Based, Macrobiotic, Dairy‑free, Flexitarian, Clean eating, Vegetarian, High‑protein, Whole30, Sugar‑free, Raw, Mediterranean, Pescatarian].

Output format:
- Return *only* a JSON array of objects, each with these keys:
  item_name, rating, price, tags, foodInfo, Food Presentation,
  Food Preparation Styles, Flavor Types, Food Concepts, Mealtime, Dietary.
- Do not include any markdown, code fences, or extra text.
Think step-by-step.
"""

    user_message = (
        f"Here are some masked template sentences for menu items at “{name}” ({address}):\n"
        "1. \"The <REPLACE_ME> burger is served with <REPLACE_ME>.\"\n"
        "2. \"Our signature <REPLACE_ME> pasta comes topped with <REPLACE_ME>.\"\n"
        "3. \"Enjoy the <REPLACE_ME> salad tossed in <REPLACE_ME>.\"\n"
        "\nNow fill in all <REPLACE_ME> tokens and supply the JSON array as specified."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-search-preview",
        web_search_options={},
        messages=[
            {"role": "system",  "content": system_message},
            {"role": "user",    "content": user_message},
        ],
    )

    raw = resp.choices[0].message.content.strip()

    # Try first to extract JSON array with code fences, similar to the restaurant search function.
    m = re.search(r"```json\s*(\[[\s\S]*?\])\s*```", raw)
    if m:
        json_text = m.group(1)
    else:
        # Fallback extraction: find the first '[' and last ']' to extract the JSON substring.
        start = raw.find('[')
        end   = raw.rfind(']')
        if start != -1 and end != -1:
            json_text = raw[start:end+1]
        else:
            logger.error("Failed to extract JSON array from get_menu_details response for %s", name)
            return []

    try:
        items = json.loads(json_text)
        return [
            MenuItem(
                item_name=it["item_name"],
                rating=it.get("rating"),
                price=it.get("price"),
                tags=it.get("tags", []),
                mealtime=it.get("Mealtime", it.get("mealtime", "all day")),
                food_concepts=it.get("Food Concepts", it.get("food_concepts", [])),
                description=it.get("foodInfo", ""),
                preparation_styles=it.get("Food Preparation Styles", []),
            )
            for it in items
        ]
    except Exception as e:
        logger.error("Failed to parse menu JSON for %s: %s", name, e)
        return []


# ——— Orchestrator with Chunked Output —————————————————————————————————————
@server.tool()
def recommend_food_place_by_coords(latitude: float, longitude: float) -> List[str]:
    """
    1) Finds restaurants.
    2) Fetches menu details for each.
    3) Returns a list of markdown chunks not exceeding token limits.
    """
    restaurants = search_restaurants_by_coords(latitude, longitude)
    if not restaurants:
        return [f"No restaurants found near {latitude},{longitude}."]

    # Build full report
    lines = [f"# Top {len(restaurants)} Restaurants Near {latitude},{longitude}\n"]
    for idx, r in enumerate(restaurants, start=1):
        lines.append(f"## {idx}. {r.name}")
        lines.append(f"**Address:** {r.address}\n")
        menu = get_menu_details(r.name, r.address)
        if not menu:
            lines.append("_No menu details available._\n---\n")
            continue

        for mi in menu:
            lines.append(f"- **{mi.item_name}**")
            lines.append(f"  - Rating: {mi.rating or 'N/A'}")
            lines.append(f"  - Price: {mi.price or 'N/A'}")
            lines.append(f"  - Tags: {', '.join(mi.tags) or 'N/A'}")
            lines.append(f"  - Mealtime: {mi.mealtime}")
            lines.append(f"  - Concepts: {', '.join(mi.food_concepts) or 'N/A'}")
            lines.append(f"  - Description: {mi.description}")
            lines.append(f"  - Preparation: {', '.join(mi.preparation_styles) or 'N/A'}\n")
        lines.append("---\n")

    full_text = "\n".join(lines)
    return chunk_text(full_text)

# ——— Run as script —————————————————————————————————————————————————————
if __name__ == "__main__":
    lat, lng = 22.5726, 88.3639
    chunks = recommend_food_place_by_coords(lat, lng)
    for chunk in chunks:
        print(chunk)
