from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from rapidfuzz import process, fuzz

app = FastAPI(
    title="Qatar Metro API",
    description="API for Qatar Metro train timings and station info",
    version="1.1"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load CSV safely
try:
    df = pd.read_csv("metro_data_clean.csv", on_bad_lines='skip')  # skip malformed rows
except FileNotFoundError:
    df = pd.DataFrame()
except pd.errors.ParserError:
    df = pd.DataFrame()

if df.empty:
    metro_data = []
else:
    # Transform CSV to structured JSON per station
    metro_data = []
    for _, row in df.iterrows():
        station_name = row.get("Station", "")
        line_color = row.get("Line", "")
        first_train = row.get("First_Train", "")
        last_train = row.get("Last_Train", "")
        days = row.get("Days", "")
        
        # Check if station already exists
        existing = next((s for s in metro_data if s["Station"] == station_name), None)
        line_info = {
            "Line": line_color,
            "First_Train": first_train,
            "Last_Train": last_train,
            "Days": days
        }
        if existing:
            existing["Lines"].append(line_info)
        else:
            metro_data.append({"Station": station_name, "Lines": [line_info]})

# Helper: station names for fuzzy search
station_names = [s["Station"] for s in metro_data]

@app.get("/", summary="API Root")
def root():
    return {"message": "Qatar Metro API is running", "total_stations": len(metro_data)}

@app.get("/metro", summary="Get all metro stations")
def get_metro_data(limit: int = Query(0, description="Number of stations to return, 0 for all"), skip: int = Query(0, description="Skip first N stations")):
    if not metro_data:
        raise HTTPException(status_code=404, detail="No metro data available")
    
    total_stations = len(metro_data)
    data = metro_data[skip:]
    if limit > 0:
        data = data[:limit]
    
    return {
        "total": total_stations, 
        "returned": len(data),
        "skip": skip,
        "limit": limit,
        "stations": data
    }

@app.get("/metro/search", summary="Search station by name")
def search_station(name: str = Query(..., description="Partial or full station name"), limit: int = Query(5, description="Max results to return")):
    if not station_names:
        raise HTTPException(status_code=404, detail="No metro data available")
    
    matches = process.extract(name, station_names, scorer=fuzz.WRatio, limit=limit)
    
    results = []
    for _, score, idx in matches:
        if score < 30: # Filter out very poor matches
            continue
        station = metro_data[idx].copy()
        station["match_score"] = round(score, 2)
        results.append(station)
    
    if not results:
        raise HTTPException(status_code=404, detail="No matching stations found")
    
    return {"query": name, "results": results}

@app.get("/metro/{station_name}", summary="Get exact station data")
def get_station_data(station_name: str):
    station = next((s for s in metro_data if s["Station"].lower() == station_name.lower()), None)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station '{station_name}' not found")
    return station
