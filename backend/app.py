import os
import sqlite3
import json
import random
import re
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app) # Enable CORS for frontend integration

@app.route('/')
def index():
    return app.send_static_file('index.html')

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'fra_dss.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Heuristic Entity Extractor (simulating NER and OCR)
def mock_ner_extract(text):
    # Match patterns for claimant
    claimant = "Unknown Claimant"
    m_name = re.search(r"(?:claimant\s+name|applicant\s+name|individual\s+rights?\s+to|individual\s+claim\s+of|representative|claimant|applicant|claim\s+of|claim\s+by)\s*:?\s*([A-Za-z\s]{3,30})", text, re.IGNORECASE)
    if m_name:
        candidate = m_name.group(1).strip()
        candidate = re.split(r'\n|\r|Tribal|Group|State|District|Location|Community|PVTG|Category|Acreage|GPS', candidate, flags=re.IGNORECASE)[0].strip()
        if candidate:
            claimant = candidate

    # Match patterns for village
    village = "Unknown Village"
    m_village = re.search(r"(?:village|at)\s*:?\s*([A-Za-z\s]{3,25})", text, re.IGNORECASE)
    if m_village:
        candidate_vil = m_village.group(1).strip()
        candidate_vil = re.split(r'\n|\r|District|State|Type|Coordinates|GPS|Claim|Plot', candidate_vil, flags=re.IGNORECASE)[0].strip()
        if candidate_vil:
            village = candidate_vil

    # Match patterns for area
    area_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:acres|acre|ac)", text, re.IGNORECASE)
    area = float(area_match.group(1)) if area_match else 2.0

    # Match patterns for coordinates
    lat_lng_match = re.search(r"lat(?:itude)?\s*(\d+\.\d+).*?lng(?:itude)?\s*(\d+\.\d+)", text, re.IGNORECASE)
    lat = float(lat_lng_match.group(1)) if lat_lng_match else None
    lng = float(lat_lng_match.group(2)) if lat_lng_match else None

    # Match claim type (IFR/CR/CFR)
    claim_type = "IFR"
    if re.search(r"\bCFR\b|community\s+forest\s+resource", text, re.IGNORECASE):
        claim_type = "CFR"
    elif re.search(r"\bCR\b|community\s+rights", text, re.IGNORECASE):
        claim_type = "CR"
    elif re.search(r"\bIFR\b|individual", text, re.IGNORECASE):
        claim_type = "IFR"

    # Standardize names
    if "baiga" in text.lower():
        tribal_group = "Baiga"
    elif "gond" in text.lower():
        tribal_group = "Gond"
    elif "bhil" in text.lower():
        tribal_group = "Bhil"
    elif "tripuri" in text.lower():
        tribal_group = "Tripuri"
    elif "reang" in text.lower():
        tribal_group = "Reang"
    elif "santhal" in text.lower():
        tribal_group = "Santhal"
    elif "kolha" in text.lower():
        tribal_group = "Kolha"
    elif "kondh" in text.lower():
        tribal_group = "Kondh"
    elif "koya" in text.lower():
        tribal_group = "Koya"
    else:
        tribal_group = "General"

    return {
        "claimant_name": claimant,
        "village_name": village,
        "area_acres": area,
        "latitude": lat,
        "longitude": lng,
        "claim_type": claim_type,
        "tribal_group": tribal_group,
        "status": "Pending"
    }

# 1. API: List Villages (with nested claims and assets)
@app.route('/api/villages', methods=['GET'])
def get_villages():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query villages with state and district names
    cursor.execute("""
        SELECT v.*, d.name AS district_name, s.name AS state_name 
        FROM villages v
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
    """)
    rows = cursor.fetchall()
    
    villages = []
    for row in rows:
        v_dict = dict(row)
        
        # Load GeoJSON boundary
        if v_dict['boundary_geojson']:
            try:
                v_dict['boundary_geojson'] = json.loads(v_dict['boundary_geojson'])
            except Exception:
                pass
                
        v_id = v_dict['id']
        
        # Get claims
        cursor.execute("SELECT * FROM fra_claims WHERE village_id = ?", (v_id,))
        v_dict['claims'] = [dict(c) for c in cursor.fetchall()]
        
        # Get assets
        cursor.execute("SELECT * FROM village_assets WHERE village_id = ?", (v_id,))
        assets = []
        for asset in cursor.fetchall():
            a_dict = dict(asset)
            if a_dict['coordinates_geojson']:
                try:
                    a_dict['coordinates_geojson'] = json.loads(a_dict['coordinates_geojson'])
                except Exception:
                    pass
            assets.append(a_dict)
        v_dict['assets'] = assets
        
        villages.append(v_dict)
        
    conn.close()
    return jsonify(villages)

# 2. API: Aggregate Stats
@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Global aggregates
    cursor.execute("SELECT COUNT(*) as total_claims, SUM(area_acres) as total_area FROM fra_claims")
    global_row = cursor.fetchone()
    total_claims = global_row['total_claims'] or 0
    total_area = round(global_row['total_area'] or 0.0, 2)
    
    cursor.execute("SELECT status, COUNT(*) as count FROM fra_claims GROUP BY status")
    status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
    for s in ['Pending', 'Verified', 'Rejected']:
        status_counts.setdefault(s, 0)
        
    cursor.execute("SELECT claim_type, COUNT(*) as count FROM fra_claims GROUP BY claim_type")
    type_counts = {row['claim_type']: row['count'] for row in cursor.fetchall()}
    for t in ['IFR', 'CR', 'CFR']:
        type_counts.setdefault(t, 0)
        
    # State-wise breakdown
    cursor.execute("""
        SELECT s.name as state, 
               COUNT(c.id) as total_claims,
               SUM(CASE WHEN c.status = 'Verified' THEN 1 ELSE 0 END) as verified_claims,
               SUM(CASE WHEN c.status = 'Pending' THEN 1 ELSE 0 END) as pending_claims,
               SUM(CASE WHEN c.status = 'Rejected' THEN 1 ELSE 0 END) as rejected_claims,
               SUM(c.area_acres) as total_area,
               AVG(v.water_index) as avg_water_index,
               AVG(v.forest_cover_percentage) as avg_forest_cover
        FROM states s
        LEFT JOIN districts d ON s.id = d.state_id
        LEFT JOIN villages v ON d.id = v.district_id
        LEFT JOIN fra_claims c ON v.id = c.village_id
        GROUP BY s.name
    """)
    state_breakdown = []
    for row in cursor.fetchall():
        r = dict(row)
        r['total_area'] = round(r['total_area'] or 0.0, 2)
        r['avg_water_index'] = round(r['avg_water_index'] or 0.0, 2)
        r['avg_forest_cover'] = round(r['avg_forest_cover'] or 0.0, 2)
        state_breakdown.append(r)
        
    # Asset counts
    cursor.execute("SELECT asset_type, COUNT(*) as count FROM village_assets GROUP BY asset_type")
    asset_breakdown = {row['asset_type']: row['count'] for row in cursor.fetchall()}
    for a in ['Pond', 'Agricultural Farm', 'Forest Resource', 'Homestead']:
        asset_breakdown.setdefault(a, 0)
        
    conn.close()
    return jsonify({
        "total_claims": total_claims,
        "total_area_acres": total_area,
        "status_counts": status_counts,
        "type_counts": type_counts,
        "state_breakdown": state_breakdown,
        "asset_counts": asset_breakdown
    })

# 3. API: Simulate OCR / NER Document Digitization
@app.route('/api/digitize', methods=['POST'])
def digitize_document():
    data = request.json or {}
    text_content = data.get('text_content', '')
    doc_name = data.get('document_name', 'scanned_patta.pdf')
    
    if not text_content:
        return jsonify({"error": "No text content provided for extraction"}), 400
        
    # Extract entities
    entities = mock_ner_extract(text_content)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Try to find a matching village in database, or default to first village
    village_name = entities['village_name']
    cursor.execute("SELECT id FROM villages WHERE name LIKE ? LIMIT 1", (f"%{village_name}%",))
    v_row = cursor.fetchone()
    
    if v_row:
        village_id = v_row['id']
    else:
        # Assign to a random existing village to avoid orphan claims
        cursor.execute("SELECT id FROM villages ORDER BY RANDOM() LIMIT 1")
        village_id = cursor.fetchone()['id']
        
    # Check if this claimant already exists to avoid duplicates
    cursor.execute("SELECT id FROM fra_claims WHERE claimant_name = ? AND village_id = ?", 
                   (entities['claimant_name'], village_id))
    existing_claim = cursor.fetchone()
    
    if not existing_claim:
        # Insert claim into DB
        cursor.execute("""
            INSERT INTO fra_claims (village_id, claimant_name, claim_type, status, date_filed, area_acres, document_name, extracted_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            village_id,
            entities['claimant_name'],
            entities['claim_type'],
            entities['status'],
            datetime.now().strftime("%Y-%m-%d"),
            entities['area_acres'],
            doc_name,
            text_content
        ))
        conn.commit()
        claim_id = cursor.lastrowid
    else:
        claim_id = existing_claim['id']
        
    conn.close()
    
    return jsonify({
        "success": True,
        "claim_id": claim_id,
        "extracted_metadata": {
            "claimant_name": entities['claimant_name'],
            "village_id": village_id,
            "village_name": village_name,
            "claim_type": entities['claim_type'],
            "area_acres": entities['area_acres'],
            "status": entities['status'],
            "tribal_group": entities['tribal_group']
        },
        "message": f"Successfully digitized legacy record for {entities['claimant_name']}."
    })

# 4. API: Simulate AI Computer Vision Asset Detection
@app.route('/api/detect-assets', methods=['POST'])
def detect_assets():
    data = request.json or {}
    village_id = data.get('village_id')
    
    if not village_id:
        return jsonify({"error": "village_id is required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify village exists
    cursor.execute("SELECT * FROM villages WHERE id = ?", (village_id,))
    village = cursor.fetchone()
    if not village:
        conn.close()
        return jsonify({"error": "Village not found"}), 404
        
    lat, lng = village['latitude'], village['longitude']
    
    # Detect 1-3 new random assets
    detected_assets = []
    asset_types = ['Pond', 'Agricultural Farm', 'Forest Resource', 'Homestead']
    num_assets = random.randint(1, 3)
    
    for _ in range(num_assets):
        asset_type = random.choice(asset_types)
        # Random location offset within ~500 meters
        offset_lat = random.uniform(-0.005, 0.005)
        offset_lng = random.uniform(-0.005, 0.005)
        
        area = round(random.uniform(0.1, 5.0) if asset_type != 'Forest Resource' else random.uniform(5.0, 30.0), 2)
        
        asset_geojson = json.dumps({
            "type": "Feature",
            "properties": {"name": f"AI Detected {asset_type}"},
            "geometry": {
                "type": "Point",
                "coordinates": [lng + offset_lng, lat + offset_lat]
            }
        })
        
        cursor.execute("""
            INSERT INTO village_assets (village_id, asset_type, count_or_area, coordinates_geojson, detected_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (village_id, asset_type, area, asset_geojson))
        
        detected_assets.append({
            "asset_type": asset_type,
            "count_or_area": area,
            "coordinates": [lng + offset_lng, lat + offset_lat]
        })
        
    # Slightly adjust indices based on new detections
    # If ponds are detected, increase water index. If forest cover is detected, increase forest cover.
    new_water_idx = min(1.0, village['water_index'] + 0.05 * sum(1 for a in detected_assets if a['asset_type'] == 'Pond'))
    new_forest_pct = min(100.0, village['forest_cover_percentage'] + 1.2 * sum(a['count_or_area'] for a in detected_assets if a['asset_type'] == 'Forest Resource'))
    
    cursor.execute("""
        UPDATE villages 
        SET water_index = ?, forest_cover_percentage = ? 
        WHERE id = ?
    """, (new_water_idx, new_forest_pct, village_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "village_id": village_id,
        "detected_assets": detected_assets,
        "updated_water_index": round(new_water_idx, 2),
        "updated_forest_cover": round(new_forest_pct, 2)
    })

# 5. API: DSS Recommendation Engine (Evaluating Rules & Scheme Layering)
@app.route('/api/dss/evaluate', methods=['POST'])
def evaluate_dss():
    data = request.json or {}
    
    # Custom thresholds from frontend sliders (with defaults)
    water_threshold = float(data.get('water_threshold', 0.4)) # Prioritize JJM water schemes if water index below this
    forest_threshold = float(data.get('forest_threshold', 50.0)) # CFR interventions if forest density below this
    infra_threshold = float(data.get('infra_threshold', 0.5)) # DAJGUA infrastructure if index below this
    land_threshold = float(data.get('land_threshold', 2.0)) # PM-KISAN if agricultural acres above this
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Load all villages with district and state
    cursor.execute("""
        SELECT v.*, d.name AS district_name, s.name AS state_name 
        FROM villages v
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
    """)
    villages = [dict(row) for row in cursor.fetchall()]
    
    # Load all verified/pending claims
    cursor.execute("""
        SELECT c.*, v.name as village_name, v.water_index, v.forest_cover_percentage, 
               v.infrastructure_index, v.tribal_group, d.name as district_name, s.name as state_name
        FROM fra_claims c
        JOIN villages v ON c.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
    """)
    claims = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    recommendations = []
    
    # Evaluate Rules:
    # Rule 1: PM-KISAN (Individual agricultural support)
    # Target: IFR, Status: Verified, Area >= land_threshold
    for claim in claims:
        if claim['claim_type'] == 'IFR' and claim['status'] == 'Verified':
            if claim['area_acres'] >= land_threshold:
                priority = "High" if claim['area_acres'] > 4.0 else "Medium"
                score = round(claim['area_acres'] * 2, 2)
                recommendations.append({
                    "type": "Individual Beneficiary",
                    "beneficiary_name": claim['claimant_name'],
                    "village_name": claim['village_name'],
                    "district_name": claim['district_name'],
                    "state_name": claim['state_name'],
                    "scheme_name": "PM-KISAN",
                    "ministry": "Ministry of Agriculture",
                    "reason": f"Verified IFR patta holder with {claim['area_acres']} acres of agricultural land.",
                    "priority": priority,
                    "score": score
                })
                
    # Rule 2: Jal Jeevan Mission (JJM - Drinking Water Infrastructure)
    # Target: Villages with water_index < water_threshold
    for vil in villages:
        if vil['water_index'] < water_threshold:
            score = round((1.0 - vil['water_index']) * 10, 2)
            priority = "Critical" if vil['water_index'] < 0.25 else "High"
            recommendations.append({
                "type": "Community / Village",
                "beneficiary_name": f"Village: {vil['name']}",
                "village_name": vil['name'],
                "district_name": vil['district_name'],
                "state_name": vil['state_name'],
                "scheme_name": "Jal Jeevan Mission (JJM)",
                "ministry": "Ministry of Jal Shakti",
                "reason": f"Severe water scarcity detected (Water Index: {vil['water_index']}). Priority drinking water connection required.",
                "priority": priority,
                "score": score
            })

    # Rule 3: MGNREGA (Water Conservation & Livelihood Asset Creation)
    # Target: Villages with water index < water_threshold or low assets. Suggest Pond excavation.
    for vil in villages:
        if vil['water_index'] < 0.5:
            score = round((0.5 - vil['water_index']) * 8 + 3, 2)
            recommendations.append({
                "type": "Community / Village",
                "beneficiary_name": f"Gram Panchayat: {vil['name']}",
                "village_name": vil['name'],
                "district_name": vil['district_name'],
                "state_name": vil['state_name'],
                "scheme_name": "MGNREGA Pond Excavation",
                "ministry": "Ministry of Rural Development",
                "reason": f"Drought-prone village. Suggests employing local FRA community under MGNREGA for pond building to restore water table.",
                "priority": "High" if score > 6 else "Medium",
                "score": score
            })

    # Rule 4: DAJGUA (Development Action Plan for Jaunsa-Ghar-Uday / 3 ministries integration for PVTGs & Tribal villages)
    # Target: Tribal village with low infrastructure (infrastructure_index < infra_threshold)
    # Ministries: Ministry of Tribal Affairs (MoTA), MoRD, Jal Shakti
    for vil in villages:
        # Check if the village has a PVTG / particularly concentrated tribal group
        is_tribal = vil['tribal_group'] in ['Baiga', 'Reang', 'Kondh', 'Koya', 'Gond', 'Bhil', 'Kolha', 'Tripuri']
        if is_tribal and vil['infrastructure_index'] < infra_threshold:
            score = round((1.0 - vil['infrastructure_index']) * 10, 2)
            priority = "Critical" if vil['infrastructure_index'] < 0.3 else "High"
            recommendations.append({
                "type": "Multi-Ministry Infrastructure (DAJGUA)",
                "beneficiary_name": f"Tribal Settlement: {vil['name']} ({vil['tribal_group']} group)",
                "village_name": vil['name'],
                "district_name": vil['district_name'],
                "state_name": vil['state_name'],
                "scheme_name": "DAJGUA Integrated Development Scheme",
                "ministry": "Tribal Affairs + Rural Dev + Jal Shakti",
                "reason": f"Particularly Vulnerable / Tribal Group habitat with infrastructure index of {vil['infrastructure_index']}. Recommends road access, clean energy, and vocational skill centers.",
                "priority": priority,
                "score": score
            })

    # Sort recommendations by priority score descending
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    return jsonify({
        "success": True,
        "recommendations": recommendations,
        "counts": {
            "total_recommendations": len(recommendations),
            "PM-KISAN": sum(1 for r in recommendations if r['scheme_name'] == 'PM-KISAN'),
            "JJM": sum(1 for r in recommendations if 'Jal Jeevan' in r['scheme_name']),
            "MGNREGA": sum(1 for r in recommendations if 'MGNREGA' in r['scheme_name']),
            "DAJGUA": sum(1 for r in recommendations if 'DAJGUA' in r['scheme_name'])
        }
    })

if __name__ == '__main__':
    # Run backend server locally on port 5000
    app.run(debug=True, port=5000)
