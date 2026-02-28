import json
import pandas as pd
import re
from urllib.parse import unquote

JSON_FILE = "metro_tables.json"
OUTPUT_FILE = "metro_data_clean.csv"

# Known line colors
COLORS = ["Red", "Green", "Gold", "Orange", "Turquoise", "Pink"]

def parse_filename(filename):
    name_part = filename.replace(".pdf", "")
    parts = name_part.split("_")
    line = "Unknown"
    station_parts = []
    
    for i, part in enumerate(parts):
        if part in COLORS:
            line = part
            station_parts = parts[:i]
            break
    
    if not station_parts:
        if "_" in name_part:
            station_raw, line = name_part.rsplit("_", 1)
        else:
            station_raw = name_part
            line = "Unknown"
    else:
        station_raw = "_".join(station_parts)
    
    station = unquote(station_raw).replace("_", " ").strip()
    return station, line

def extract_times(text):
    return re.findall(r"\b\d{2}:\d{2}\b", str(text))

def process_json():
    try:
        with open(JSON_FILE, "r") as f:
            data_json = json.load(f)
    except FileNotFoundError:
        print(f"Error: {JSON_FILE} not found.")
        return

    all_data = []

    for item in data_json:
        filename = item.get("filename", "")
        station, line = parse_filename(filename)
        tables = item.get("tables", [])
        
        # Flatten all text from tables
        full_text = ""
        all_times = []
        for table in tables:
            for row in table:
                for cell in row:
                    if cell:
                        full_text += str(cell) + " "
                        all_times.extend(extract_times(cell))
        
        # Simple heuristic:
        # Sat-Thu starts early (05, 06)
        # Friday starts at 09 or 14
        
        sat_thu_times = []
        friday_times = []
        
        for t in all_times:
            hour = int(t.split(":")[0])
            if hour in [5, 6]:
                sat_thu_times.append(t)
            elif hour in [9, 14]:
                friday_times.append(t)
            elif hour in [0, 1, 2]: # Last trains
                # We'll associate these later
                pass
        
        # Actually, let's use a more robust way: many PDFs have a Sat-Thu section and a Friday section.
        # If we have at least 2 times, we assume first two or early two are Sat-Thu.
        
        # Let's try to find "Friday" in the JSON structure
        found_friday = False
        friday_times_v2 = []
        sat_thu_times_v2 = []
        
        unique_times = []
        seen = set()
        for t in all_times:
            if t not in seen:
                unique_times.append(t)
                seen.add(t)
        
        # Heuristic for Sat-Thu and Friday
        if len(unique_times) >= 2:
            # Most stations start at 05:XX or 06:XX for Sat-Thu
            # Friday starts at 09:XX or 14:XX
            
            # Let's look for the 09: or 14: pattern for Friday
            f_start = [t for t in unique_times if t.startswith("09:") or t.startswith("14:")]
            st_start = [t for t in unique_times if t.startswith("05:") or t.startswith("06:")]
            ends = [t for t in unique_times if t.startswith("00:") or t.startswith("01:") or t.startswith("02:")]
            
            if st_start:
                st_first = st_start[0]
                st_last = ends[0] if ends else (unique_times[1] if len(unique_times) > 1 else "")
                all_data.append({
                    "Station": station,
                    "Line": line,
                    "First_Train": st_first,
                    "Last_Train": st_last,
                    "Days": "Saturday - Thursday"
                })
            
            if f_start:
                f_first = f_start[0]
                f_last = ends[0] if ends else (unique_times[-1] if len(unique_times) > 0 else "")
                all_data.append({
                    "Station": station,
                    "Line": line,
                    "First_Train": f_first,
                    "Last_Train": f_last,
                    "Days": "Friday"
                })
            elif "Friday" in full_text and len(st_start) > 0:
                # If specifically mentioned Friday but no 9/14 time found, maybe it's same? 
                # Or maybe it has another early time?
                # Sometimes Friday starts at 09:00 for Red/Green line
                pass

    if not all_data:
        print("No data extracted.")
        return

    df = pd.DataFrame(all_data)
    df = df.drop_duplicates()
    df = df.sort_values(by=["Station", "Line", "Days"], ascending=[True, True, False])
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"===================================")
    print(f"Updated CSV successfully using JSON data ✅")
    print(f"Total rows: {len(df)}")
    print(f"Saved to: {OUTPUT_FILE}")
    print(f"===================================")

if __name__ == "__main__":
    process_json()
