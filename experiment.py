
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.utilities import GoogleSerperAPIWrapper
from mcp.server.fastmcp import FastMCP

# —————— MCP setup ——————
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY", "")
mcp = FastMCP("Info")

@mcp.tool()
def get_restaurants_nearby(lat: float, lon: float):
    query = f"restaurants near latitude {lat}, longitude {lon}"
    results = GoogleSerperAPIWrapper(type="search", num=10).results(query)
    return results

@mcp.tool()
def get_weather(lat: float, lon: float):
    query = f"current weather near latitude {lat}, longitude {lon}"
    results = GoogleSerperAPIWrapper(type="search", num=5).results(query)
    return results

@mcp.tool()
def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# —————— FastAPI app ——————
app = FastAPI(title="Info MCP HTTP Gateway")

class Coord(BaseModel):
    lat: float
    lon: float

@app.post("/restaurants")
def restaurants(c: Coord):
    try:
        return {"restaurants": get_restaurants_nearby(c.lat, c.lon)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/weather")
def weather(c: Coord):
    try:
        return {"weather": get_weather(c.lat, c.lon)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/time")
def time_():
    try:
        return {"time": get_time()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("experiment:app", host="127.0.0.1", port=8000, reload=True)
