import os
import re
import fitz  # PyMuPDF
import pandas as pd
from urllib.parse import unquote

PDF_FOLDER = "qr_pdfs"
OUTPUT_FILE = "metro_data_clean.csv"

data = []

# Loop through all PDFs
for filename in os.listdir(PDF_FOLDER):
    if not filename.endswith(".pdf"):
        continue

    filepath = os.path.join(PDF_FOLDER, filename)

    # Extract station + line from filename
    # Example: Legtaifiya_Orange.pdf or Al_Sudan_Gold_0.pdf
    name_part = filename.replace(".pdf", "")
    
    # Known line colors to help with parsing
    COLORS = ["Red", "Green", "Gold", "Orange", "Turquoise", "Pink"]
    
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

    # Decode URL encoding and clean
    station = unquote(station_raw).replace("_", " ").strip()

    # Open PDF
    doc = fitz.open(filepath)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    # Extract all times (HH:MM)
    all_times = re.findall(r"\b\d{2}:\d{2}\b", text)
    
    # Remove duplicates but preserve order
    unique_times = []
    seen = set()
    for t in all_times:
        if t not in seen:
            unique_times.append(t)
            seen.add(t)

    # Heuristic: Sat-Thu starts at 05 or 06, Friday starts at 09 or 14
    f_start = [t for t in unique_times if t.startswith("09:") or t.startswith("14:")]
    st_start = [t for t in unique_times if t.startswith("05:") or t.startswith("06:")]
    ends = [t for t in unique_times if t.startswith("00:") or t.startswith("01:") or t.startswith("02:")]
    
    if st_start:
        st_first = st_start[0]
        # Heuristic for last train
        st_last = ends[0] if ends else (unique_times[1] if len(unique_times) > 1 else "")
        data.append({
            "Station": station,
            "Line": line,
            "First_Train": st_first,
            "Last_Train": st_last,
            "Days": "Saturday - Thursday"
        })
    
    if f_start:
        f_first = f_start[0]
        f_last = ends[0] if ends else (unique_times[-1] if len(unique_times) > 0 else "")
        data.append({
            "Station": station,
            "Line": line,
            "First_Train": f_first,
            "Last_Train": f_last,
            "Days": "Friday"
        })
    elif "Friday" in text and len(st_start) > 0:
        # If no explicit 9:00/14:00 found but Friday mentioned, maybe add it as same for now or skip
        pass

# Convert to DataFrame
df = pd.DataFrame(data)

# Remove empty stations
df = df[df["Station"] != ""]

# Sort nicely
df = df.sort_values(by=["Station", "Line"])

# Save clean CSV
df.to_csv(OUTPUT_FILE, index=False)

print("===================================")
print("Parser completed successfully ✅")
print("Total rows:", len(df))
print("Saved file:", OUTPUT_FILE)
print("===================================")
