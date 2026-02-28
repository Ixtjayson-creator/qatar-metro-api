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
    times = re.findall(r"\b\d{2}:\d{2}\b", text)

    # Improved logic: Usually first two are Sat-Thu, and then if Friday exists, there's another set.
    # This is still a bit of a guess without table parsing, but better than before.
    if len(times) >= 2:
        # Sat-Thu
        data.append({
            "Station": station,
            "Line": line,
            "First_Train": times[0],
            "Last_Train": times[1],
            "Days": "Saturday - Thursday"
        })
        
        # Friday (usually later in the text)
        if "Friday" in text and len(times) >= 4:
            data.append({
                "Station": station,
                "Line": line,
                "First_Train": times[-2], # Guessing Friday times are near the end
                "Last_Train": times[-1],
                "Days": "Friday"
            })
        elif "Friday" in text and len(times) >= 2:
             # If only 2 times found but Friday mentioned, maybe they are same or it's just Friday?
             # For now, let's just keep the Sat-Thu one as well.
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
