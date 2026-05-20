import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'fra_dss.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

# Heuristics for bounding box polygon around a coordinate
def make_bbox_geojson(lat, lng, size=0.015):
    # Generates a simple GeoJSON Polygon bounding box
    coords = [
        [lng - size, lat - size],
        [lng + size, lat - size],
        [lng + size, lat + size],
        [lng - size, lat + size],
        [lng - size, lat - size]
    ]
    return json.dumps({
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [coords]
        }
    })

def seed_database():
    print(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Read and execute schema
    print(f"Executing schema from {SCHEMA_PATH}...")
    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)

    # Clean existing data to avoid duplicates if re-run
    cursor.execute("DELETE FROM sqlite_sequence")
    cursor.execute("DELETE FROM village_assets")
    cursor.execute("DELETE FROM fra_claims")
    cursor.execute("DELETE FROM villages")
    cursor.execute("DELETE FROM districts")
    cursor.execute("DELETE FROM states")
    conn.commit()

    # 1. Insert States
    states = ["Madhya Pradesh", "Tripura", "Odisha", "Telangana"]
    state_ids = {}
    for state in states:
        cursor.execute("INSERT INTO states (name) VALUES (?)", (state,))
        state_ids[state] = cursor.lastrowid

    # 2. Insert Districts
    districts = {
        "Madhya Pradesh": ["Mandla", "Dindori", "Dhar"],
        "Tripura": ["Dhalai", "South Tripura"],
        "Odisha": ["Mayurbhanj", "Nabarangpur"],
        "Telangana": ["Bhadradri Kothagudem", "Adilabad"]
    }
    district_ids = {}
    for state, dist_list in districts.items():
        state_id = state_ids[state]
        for dist in dist_list:
            cursor.execute("INSERT INTO districts (state_id, name) VALUES (?, ?)", (state_id, dist))
            district_ids[f"{state}_{dist}"] = cursor.lastrowid

    # 3. Insert Villages
    # Format: (name, state, district, lat, lng, water_index, forest_cover, infra_index, tribal_group)
    villages_data = [
        # Madhya Pradesh
        ("Kanha Basti", "Madhya Pradesh", "Mandla", 22.330, 80.610, 0.30, 68.0, 0.40, "Baiga"),
        ("Dindori Village", "Madhya Pradesh", "Dindori", 22.950, 81.080, 0.25, 75.0, 0.20, "Gond"),
        ("Dhar Rampura", "Madhya Pradesh", "Dhar", 22.600, 75.300, 0.60, 35.0, 0.50, "Bhil"),
        # Tripura
        ("Ganda Chara", "Tripura", "Dhalai", 23.484, 91.879, 0.80, 82.0, 0.30, "Tripuri"),
        ("Manu Bazar", "Tripura", "South Tripura", 23.058, 91.738, 0.75, 70.0, 0.40, "Reang"),
        # Odisha
        ("Similipal Pada", "Odisha", "Mayurbhanj", 21.920, 86.350, 0.35, 80.0, 0.25, "Santhal"),
        ("Baripada Tribal Tola", "Odisha", "Mayurbhanj", 21.935, 86.720, 0.50, 60.0, 0.45, "Kolha"),
        ("Nabarangpur Kuti", "Odisha", "Nabarangpur", 20.020, 82.250, 0.20, 55.0, 0.30, "Kondh"),
        # Telangana
        ("Bhadrachalam Gudem", "Telangana", "Bhadradri Kothagudem", 17.670, 80.890, 0.45, 50.0, 0.55, "Koya"),
        ("Adilabad Pada", "Telangana", "Adilabad", 19.670, 78.530, 0.30, 40.0, 0.35, "Gond")
    ]

    village_inserted_ids = []
    for name, state, dist, lat, lng, water, forest, infra, tribal in villages_data:
        dist_id = district_ids[f"{state}_{dist}"]
        geojson = make_bbox_geojson(lat, lng, size=0.015)
        cursor.execute("""
            INSERT INTO villages (district_id, name, latitude, longitude, boundary_geojson, water_index, forest_cover_percentage, infrastructure_index, tribal_group)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (dist_id, name, lat, lng, geojson, water, forest, infra, tribal))
        v_id = cursor.lastrowid
        village_inserted_ids.append((v_id, name, lat, lng))

    # 4. Insert FRA Claims
    # Format: (village_name, claimant, type, status, date_filed, date_granted, area_acres, document, extracted_text)
    claims_data = [
        ("Kanha Basti", "Ramesh Baiga", "IFR", "Verified", "2024-03-12", "2024-11-20", 4.2, "ramesh_baiga_ifr.pdf", "Individual Forest Rights claim by Ramesh Baiga, village Kanha Basti, Mandla, MP. Survey Plot 24A, 4.2 Acres of agricultural/homestead land."),
        ("Kanha Basti", "Savitri Baiga", "IFR", "Pending", "2025-01-15", None, 3.0, "savitri_baiga_ifr.pdf", "IFR Claim by Savitri Baiga. Village: Kanha Basti. Claim Type: Individual Forest Rights. Area: 3.0 Acres. Coordinates: Lat 22.331, Lng 80.608. Pending field verification."),
        ("Kanha Basti", "Kanha Baiga Community", "CFR", "Verified", "2023-05-10", "2024-02-18", 120.0, "kanha_community_cfr.pdf", "Community Forest Resource rights for Kanha Basti, Mandla. 120 Acres of forest area for collection of Minor Forest Produce (Tendu leaves, Mahua flowers) and grazing rights."),
        
        ("Dindori Village", "Budhram Gond", "IFR", "Verified", "2023-11-04", "2024-08-12", 2.8, "budhram_gond_ifr.pdf", "Individual rights claim of Budhram Gond, Dindori Village, MP. 2.8 Acres of farm land. Plot no 145. Document verified by Gram Sabha on 2023-12-10."),
        ("Dindori Village", "Dindori Village Council", "CR", "Pending", "2025-02-28", None, 50.0, "dindori_cr_claim.pdf", "Community Rights for Dindori village forest boundary. Requesting joint management over 50 Acres of water-catchment forest zone."),
        
        ("Dhar Rampura", "Kalu Bhil", "IFR", "Verified", "2024-06-15", "2025-01-10", 3.5, "kalu_bhil_ifr.pdf", "IFR Claim of Kalu Bhil, Dhar Rampura. 3.5 Acres of dry-land agricultural plot near village boundary."),
        ("Dhar Rampura", "Bhil Community Dhar", "CFR", "Rejected", "2024-02-10", None, 300.0, "bhil_cfr_claim.pdf", "Claim rejected due to overlap with Wild Life Sanctuary core zone without proper Gram Sabha resolution minutes."),

        ("Ganda Chara", "Subodh Tripuri", "IFR", "Verified", "2023-09-20", "2024-06-05", 5.0, "subodh_tripuri.pdf", "IFR Claim for Subodh Tripuri, Ganda Chara, Dhalai. 5.0 Acres. Forest land used for horticultural cultivation (pineapple, bamboo)."),
        ("Ganda Chara", "Ganda Chara Joint Forest Committee", "CFR", "Verified", "2024-04-12", "2024-12-01", 150.0, "gandachara_cfr.pdf", "CFR Rights granted for Ganda Chara JFC. 150 Acres of community bamboo forest resource."),

        ("Manu Bazar", "Balaram Reang", "IFR", "Pending", "2025-03-01", None, 2.5, "balaram_reang_ifr.pdf", "IFR Claim of Balaram Reang, Manu Bazar, South Tripura. 2.5 Acres of homestead and mixed orchard land."),

        ("Similipal Pada", "Suresh Santhal", "IFR", "Verified", "2024-01-10", "2024-09-15", 3.8, "suresh_santhal_ifr.pdf", "IFR rights granted to Suresh Santhal, Similipal Pada, Mayurbhanj, Odisha. Plot 88, 3.8 Acres of agricultural land."),
        ("Similipal Pada", "Similipal Pada Gram Sabha", "CFR", "Verified", "2023-03-15", "2023-11-20", 250.0, "similipal_cfr.pdf", "Community Forest Resource rights granted to Similipal Pada. 250 Acres of dense forest inside Similipal buffer zone. Traditional hunting/gathering rights reserved."),
        ("Similipal Pada", "Mangal Santhal", "IFR", "Pending", "2025-02-10", None, 4.0, "mangal_santhal_ifr.pdf", "IFR Claim of Mangal Santhal. Similipal Pada. 4.0 Acres. Under process by Sub-divisional Level Committee."),

        ("Baripada Tribal Tola", "Birsa Kolha", "IFR", "Verified", "2024-05-18", "2024-12-14", 1.5, "birsa_kolha.pdf", "IFR claim approved for Birsa Kolha. Baripada Tribal Tola. 1.5 Acres. Homestead and back-yard agricultural plot."),

        ("Nabarangpur Kuti", "Hari Kondh", "IFR", "Verified", "2024-02-20", "2024-11-05", 2.2, "hari_kondh.pdf", "IFR claim approved for Hari Kondh. Nabarangpur Kuti. 2.2 Acres. Farm land located in slope terrain."),
        ("Nabarangpur Kuti", "Nabarangpur Community", "CR", "Pending", "2025-01-20", None, 80.0, "nabarangpur_cr.pdf", "Community claim for 80 Acres of minor forest produce collection zone near Nabarangpur forest beat."),

        ("Bhadrachalam Gudem", "Laxmi Koya", "IFR", "Verified", "2024-04-05", "2024-10-22", 3.2, "laxmi_koya_ifr.pdf", "IFR rights granted to Laxmi Koya. Bhadrachalam Gudem, Telangana. 3.2 Acres of podu cultivation land."),
        ("Bhadrachalam Gudem", "Koya Community Bhadrachalam", "CFR", "Verified", "2023-08-14", "2024-05-10", 180.0, "koya_cfr.pdf", "CFR rights granted to Koya Community. Bhadrachalam. 180 Acres of teak and bamboo mixed forest area."),

        ("Adilabad Pada", "Ram Gond", "IFR", "Pending", "2025-03-10", None, 4.5, "ram_gond_ifr.pdf", "IFR claim by Ram Gond, Adilabad Pada, Telangana. 4.5 Acres of podu farming land. Pending revenue inspection.")
    ]

    village_id_map = {name: v_id for v_id, name, lat, lng in village_inserted_ids}

    for v_name, claimant, c_type, status, filed, granted, area, doc, text in claims_data:
        v_id = village_id_map[v_name]
        cursor.execute("""
            INSERT INTO fra_claims (village_id, claimant_name, claim_type, status, date_filed, date_granted, area_acres, document_name, extracted_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (v_id, claimant, c_type, status, filed, granted, area, doc, text))

    # 5. Insert Village Assets (simulating Computer Vision detects)
    # Asset types: 'Pond', 'Agricultural Farm', 'Forest Resource', 'Homestead'
    # Coordinates format: GeoJSON Point [lng, lat]
    for v_id, name, lat, lng in village_inserted_ids:
        # Generate some assets for each village
        assets = []
        if "Basti" in name or "Pada" in name or "Tola" in name or "Gudem" in name or "Village" in name or "Bazar" in name or "Chara" in name or "Kuti" in name or "Rampura" in name:
            # 1. Agricultural Farm (near center)
            assets.append(('Agricultural Farm', 1.5, [lng + 0.003, lat + 0.002]))
            assets.append(('Agricultural Farm', 2.0, [lng - 0.004, lat + 0.005]))
            # 2. Pond (water body)
            assets.append(('Pond', 0.8, [lng - 0.006, lat - 0.003]))
            # 3. Forest Resource (dense forest patch)
            assets.append(('Forest Resource', 15.0, [lng + 0.008, lat - 0.008]))
            # 4. Homestead
            assets.append(('Homestead', 0.2, [lng + 0.001, lat + 0.001]))
            assets.append(('Homestead', 0.15, [lng - 0.001, lat - 0.002]))

        for asset_type, area, asset_coords in assets:
            asset_geojson = json.dumps({
                "type": "Feature",
                "properties": {"name": f"{asset_type} in {name}"},
                "geometry": {
                    "type": "Point",
                    "coordinates": asset_coords
                }
            })
            cursor.execute("""
                INSERT INTO village_assets (village_id, asset_type, count_or_area, coordinates_geojson, detected_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (v_id, asset_type, area, asset_geojson, ))

    conn.commit()
    print("Database seeding completed successfully!")
    conn.close()

if __name__ == "__main__":
    seed_database()
