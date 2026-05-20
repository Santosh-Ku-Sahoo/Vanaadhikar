# Vanaadhikar: AI-Powered FRA Atlas & Decision Support System (DSS)

Vanaadhikar is a centralized WebGIS portal and Decision Support System (DSS) designed to monitor, digitize, and layer developmental benefits for the Forest Rights Act (FRA) implementation. The project concentrates on the following target states: **Madhya Pradesh, Tripura, Odisha, and Telangana**.

---

## 🚀 Key Features

1. **Interactive WebGIS Portal (FRA Atlas)**
   - Custom Leaflet.js map visualization rendering village boundary shapefiles (GeoJSON) and claim coordinates.
   - Status indicators representing **Verified Patta** (Green), **Pending Review** (Amber), and **Rejected Claims** (Red).
   - Advanced filters by State, Right Type (IFR, CR, CFR), and Claim Status.
   - Socio-economic metrics (Water Scarcity Index, Forest Cover %, Infrastructure Index) and assets list displayed dynamically on village selection.

2. **AI-powered Claim Digitizer**
   - Simulated Optical Character Recognition (OCR) and Named Entity Recognition (NER) text extraction pipeline.
   - Extracts names, coordinates, tribal groups, acreage, and right types from scanned legacy document archives.
   - Standardizes the extracted entities and commits them directly into the central SQLite database.

3. **Remote Sensing Asset Mapping**
   - Simulates Computer Vision (CV) model classifications (Sentinel-2 satellite imagery).
   - Automatically detects homestead boundaries, farms, forest margins, and water bodies (ponds).
   - Dynamically updates database spatial assets and re-calculates environmental indices.

4. **Decision Support System (DSS)**
   - Rule-based policy engine that layers Central Sector Schemes (CSS) to maximize livelihood options:
     - **DAJGUA**: Multi-ministry PVTG (Particularly Vulnerable Tribal Groups) infrastructure support.
     - **Jal Jeevan Mission (JJM)**: priority drinking water connection for water-scarce villages.
     - **MGNREGA**: Community pond excavation recommendations.
     - **PM-KISAN**: Direct income support for verified agricultural patta holders.
   - Planners can adjust threshold sliders (Water Index, Infrastructure Index, Agricultural Land size) to evaluate and prioritize interventions.

---

## 📁 Project Structure

```text
fra_web/
├── backend/
│   ├── app.py             # Flask Web API & DSS Rule Engine
│   └── test_api.py        # Synchronous API Endpoint Unit Tests
├── database/
│   ├── schema.sql         # SQLite Database Schema Definitions
│   ├── seed.py            # Spatial and Tabular Database Seeder
│   └── fra_dss.db         # Generated SQLite Database
├── frontend/
│   ├── index.html         # Rich WebGIS Dashboard structure
│   ├── style.css          # Premium Dark Mode stylesheet
│   └── script.js          # Leaflet, Chart.js, and client-side logic
└── README.md              # Documentation
```

---

## 🛠️ Tech Stack & Requirements

- **Backend**: Python 3.12+ (Flask, Flask-CORS, SQLite3)
- **Frontend**: Vanilla HTML5, CSS3 (Glassmorphism, custom dark styling), JavaScript (ES6)
- **Map Engine**: Leaflet.js
- **Charts**: Chart.js
- **Icons & Typography**: FontAwesome v6, Google Fonts (Inter, Outfit)

---

## ⚙️ Installation & Running the App

### Step 1: Clone the repository (or go to workspace)
Make sure you are in the project root folder `fra_web`.

### Step 2: Install dependencies
Install the required Python backend libraries:
```bash
pip install flask flask-cors
```

### Step 3: Seed the Database
Initialize the SQLite database with rich mock spatial assets and boundaries for MP, Tripura, Odisha, and Telangana:
```bash
python database/seed.py
```

### Step 4: Run the Flask API Server
Start the backend server on local port 5000:
```bash
python backend/app.py
```
The server will boot and display `* Running on http://127.0.0.1:5000`.

### Step 5: Open the WebGIS Dashboard
Simply double-click or open the frontend file in any modern web browser:
- [frontend/index.html](file:///c:/Users/asus/OneDrive/Documents/fra_web/frontend/index.html)

---

## 🧪 Verification & Testing

Verify that all backend API routes and database models are functioning correctly by executing the test script:
```bash
python backend/test_api.py
```
**Expected Output:**
```text
Ran 6 tests in 0.138s
OK
```
