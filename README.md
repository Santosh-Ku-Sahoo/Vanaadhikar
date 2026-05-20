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
│   ├── app.py                      # Flask Web API & DSS Rule Engine
│   ├── test_api.py                 # Synchronous API Endpoint Unit Tests
│   └── test_problem_statement.py   # Problem Statement Alignment Integration Tests
├── database/
│   ├── schema.sql                  # SQLite Database Schema Definitions
│   ├── seed.py                     # Spatial and Tabular Database Seeder
│   └── fra_dss.db                  # Generated SQLite Database
├── frontend/
│   ├── index.html                  # Rich WebGIS Dashboard structure
│   ├── style.css                   # Premium Dark Mode stylesheet
│   └── script.js                   # Leaflet, Chart.js, and client-side logic
└── README.md                       # Documentation
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
You can access the frontend in one of two ways:
1. **Via the Flask Web Server (Recommended)**: Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in your web browser. The Flask backend automatically serves the frontend static files.
2. **Via Local File System**: Double-click or open [frontend/index.html](file:///C:/Users/asus/OneDrive/Documents/fra_nexus/fra_web/frontend/index.html) in your browser. The frontend dynamically resolves the backend URL to communicate with port 5000.

---

## 🧪 Verification & Testing

### 1. API Unit Tests
Verify that all backend API routes and database models are functioning correctly:
```bash
python backend/test_api.py
```
**Expected Output:**
```text
Ran 6 tests in 0.122s
OK
```

### 2. Problem Statement Alignment Tests
Verify the complete implementation of the 4 core properties (WebGIS Atlas, Document Digitization, Satellite Asset Mapping, and multi-ministry DSS integration):
```bash
python backend/test_problem_statement.py
```
This runs the full integration testing suite and prints a detailed verification report for each of the properties.
