-- Schema for FRA Atlas and Decision Support System (DSS)

-- 1. States table
CREATE TABLE IF NOT EXISTS states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- 2. Districts table
CREATE TABLE IF NOT EXISTS districts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY(state_id) REFERENCES states(id),
    UNIQUE(state_id, name)
);

-- 3. Villages table
CREATE TABLE IF NOT EXISTS villages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    boundary_geojson TEXT, -- Store GeoJSON string of the village boundary polygon
    water_index REAL DEFAULT 1.0, -- Range 0.0 (scarce) to 1.0 (abundant)
    forest_cover_percentage REAL DEFAULT 0.0, -- Range 0 to 100
    infrastructure_index REAL DEFAULT 1.0, -- Range 0.0 (poor) to 1.0 (highly developed)
    tribal_group TEXT DEFAULT 'General',
    FOREIGN KEY(district_id) REFERENCES districts(id)
);

-- 4. FRA Claims table (Individual, Community, and CFR rights)
CREATE TABLE IF NOT EXISTS fra_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_id INTEGER NOT NULL,
    claimant_name TEXT NOT NULL,
    claim_type TEXT CHECK(claim_type IN ('IFR', 'CR', 'CFR')) NOT NULL,
    status TEXT CHECK(status IN ('Pending', 'Verified', 'Rejected')) DEFAULT 'Pending',
    date_filed TEXT NOT NULL,
    date_granted TEXT,
    area_acres REAL NOT NULL,
    document_name TEXT,
    extracted_text TEXT, -- Stores OCR / NER extracted plain text
    FOREIGN KEY(village_id) REFERENCES villages(id)
);

-- 5. Village Assets table (Satellite mapping results)
CREATE TABLE IF NOT EXISTS village_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    village_id INTEGER NOT NULL,
    asset_type TEXT CHECK(asset_type IN ('Pond', 'Agricultural Farm', 'Forest Resource', 'Homestead')) NOT NULL,
    count_or_area REAL NOT NULL, -- Count for items, or area in acres for farms/forests
    coordinates_geojson TEXT NOT NULL, -- GeoJSON representation of the asset location
    detected_at TEXT NOT NULL,
    FOREIGN KEY(village_id) REFERENCES villages(id)
);
