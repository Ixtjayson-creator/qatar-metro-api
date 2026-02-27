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
    # Example: Legtaifiya_Orange.pdf
    name_part = filename.replace(".pdf", "")
    
    if "_" in name_part:
        station_raw, line = name_part.rsplit("_", 1)
    else:
        station_raw = name_part
        line = "Unknown"

    # Decode URL encoding and clean
    station = unquote(station_raw).replace("_", " ").strip()

    # Open PDF
    doc = fitz.open(filepath)
    text = ""

    for page in doc:
        text += page.get_text()

    doc.close()

    # Extract times (simple regex HH:MM)
    times = re.findall(r"\b\d{2}:\d{2}\b", text)

    # Basic logic (you can improve this later)
    first_train = times[0] if len(times) > 0 else ""
    last_train = times[1] if len(times) > 1 else ""

    # Detect days
    if "Friday" in text:
        days = "Friday"
    else:
        days = "Saturday - Thursday"

    data.append({
        "Station": station,
        "Line": line,
        "First_Train": first_train,
        "Last_Train": last_train,
        "Days": days
    })

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
