# Qatar Metro API 🚇

A simple FastAPI-based API for Qatar Metro and Lusail Tram timings.

## Features
- **List Stations**: Get all stations with their respective schedules.
- **Fuzzy Search**: Search for stations by name (e.g., "wakra" matches "Al Wakra").
- **Day-Specific Schedules**: Distinguishes between Saturday–Thursday and Friday timings.
- **Automatic Data Parsing**: Includes a parser to extract timings from official Qatar Rail PDFs.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the API
```bash
uvicorn metro_api:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

## API Usage Examples

### Get All Stations
**GET** `/metro`
```bash
curl http://127.0.0.1:8000/metro
```

### Search for a Station
**GET** `/metro/search?name=wakra`
```bash
curl "http://127.0.0.1:8000/metro/search?name=wakra"
```

### Get Exact Station Details
**GET** `/metro/Al Bidda`
```bash
curl "http://127.0.0.1:8000/metro/Al%20Bidda"
```

## Parsing New Data
If you have new official PDFs:
1. Place them in a folder named `qr_pdfs/`.
2. Run the parser:
```bash
python parser.py
```
3. Update the clean CSV (optional if using the parser directly):
```bash
python update_csv.py
```

## Technology Stack
- **Python 3.10+**
- **FastAPI** (Web Framework)
- **Pandas** (Data Handling)
- **RapidFuzz** (Fuzzy Search)
- **PyMuPDF** (PDF Parsing)
