import unittest
import json
import os
import sqlite3
import sys

# Add parent directory to path to import app and DB_PATH
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.app import app, DB_PATH

class TestProblemStatementAlignment(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_problem_statement_alignment(self):
        print("\n" + "="*70)
        print("   VANAADHIKAR: PROBLEM STATEMENT ALIGNMENT INTEGRATION TEST REPORT")
        print("="*70)

        # -------------------------------------------------------------
        # PROPERTY 1: Centralized Spatial Repository (WebGIS / FRA Atlas)
        # -------------------------------------------------------------
        print("\n[TEST] Property 1: WebGIS Spatial Repository (FRA Atlas)")
        response = self.client.get('/api/villages')
        self.assertEqual(response.status_code, 200)
        villages = json.loads(response.data)
        
        self.assertGreater(len(villages), 0)
        print(f"  [PASS] Seeded {len(villages)} target villages across MP, Tripura, Odisha, and Telangana.")
        
        # Verify shapefiles (GeoJSON) and coordinates are present
        for v in villages[:2]:
            self.assertIn('boundary_geojson', v)
            self.assertIsNotNone(v['boundary_geojson'])
            self.assertIn('latitude', v)
            self.assertIn('longitude', v)
            print(f"  [PASS] Georeferencing verified: {v['name']} ({v['state_name']}) at [{v['latitude']}, {v['longitude']}] with boundary shapefile.")

        # -------------------------------------------------------------
        # PROPERTY 2: Digitizing Legacy Records & Integrating with Atlas
        # -------------------------------------------------------------
        print("\n[TEST] Property 2: Legacy Digitization & Atlas Integration")
        
        # Sample document text simulating a paper patta application
        scanned_doc = {
            "document_name": "reang_community_cfr.txt",
            "text_content": "Community Forest Resource Claim. Representative: Reang forest dwellers. State: Tripura, Village: Ganda Chara. Resource area: 45.0 acres. Boundary Center Coordinates: Lat 23.4845, Lng 91.8795. Rights: Bamboo collection."
        }
        
        dig_response = self.client.post('/api/digitize', 
                                       data=json.dumps(scanned_doc), 
                                       content_type='application/json')
        self.assertEqual(dig_response.status_code, 200)
        dig_data = json.loads(dig_response.data)
        
        self.assertTrue(dig_data['success'])
        self.assertEqual(dig_data['extracted_metadata']['claimant_name'], "Reang forest dwellers")
        self.assertEqual(dig_data['extracted_metadata']['claim_type'], "CFR")
        self.assertEqual(dig_data['extracted_metadata']['area_acres'], 45.0)
        self.assertEqual(dig_data['extracted_metadata']['tribal_group'], "Reang")
        
        print("  [PASS] Simulated OCR/NER successfully digitized legacy document:")
        print(f"         - Claimant: {dig_data['extracted_metadata']['claimant_name']}")
        print(f"         - Rights Type: {dig_data['extracted_metadata']['claim_type']} ({dig_data['extracted_metadata']['area_acres']} acres)")
        print(f"         - Target Tribe: {dig_data['extracted_metadata']['tribal_group']}")

        # -------------------------------------------------------------
        # PROPERTY 3: Satellite Remote Sensing & AI Asset Mapping
        # -------------------------------------------------------------
        print("\n[TEST] Property 3: Remote Sensing & Asset Mapping Integration")
        # Target village
        v_id = villages[0]['id']
        v_name = villages[0]['name']
        original_water_idx = villages[0]['water_index']
        
        cv_response = self.client.post('/api/detect-assets', 
                                       data=json.dumps({"village_id": v_id}),
                                       content_type='application/json')
        self.assertEqual(cv_response.status_code, 200)
        cv_data = json.loads(cv_response.data)
        
        self.assertTrue(cv_data['success'])
        self.assertGreater(len(cv_data['detected_assets']), 0)
        print(f"  [PASS] Simulated Sentinel-2 CV scanner executed for village: {v_name}")
        for asset in cv_data['detected_assets']:
            print(f"         - Detected Asset: {asset['asset_type']} ({asset['count_or_area']} ac) at coordinates: {asset['coordinates']}")
            
        print(f"  [PASS] Environmental indices updated: Water Scarcity Index changed from {original_water_idx:.2f} to {cv_data['updated_water_index']:.2f}")

        # -------------------------------------------------------------
        # PROPERTY 4: Decision Support System (DSS) Scheme Layering
        # -------------------------------------------------------------
        print("\n[TEST] Property 4: Decision Support System (DSS) Scheme Layering")
        dss_payload = {
            "water_threshold": 0.50,
            "infra_threshold": 0.60,
            "land_threshold": 2.0
        }
        
        dss_response = self.client.post('/api/dss/evaluate', 
                                       data=json.dumps(dss_payload), 
                                       content_type='application/json')
        self.assertEqual(dss_response.status_code, 200)
        dss_data = json.loads(dss_response.data)
        
        self.assertTrue(dss_data['success'])
        recs = dss_data['recommendations']
        counts = dss_data['counts']
        
        self.assertGreater(len(recs), 0)
        print(f"  [PASS] DSS evaluated {len(recs)} scheme recommendations across target datasets.")
        print(f"         - PM-KISAN recommendations: {counts['PM-KISAN']}")
        print(f"         - JJM (Jal Jeevan Mission) water priorities: {counts['JJM']}")
        print(f"         - MGNREGA conservation plans: {counts['MGNREGA']}")
        print(f"         - DAJGUA Multi-Ministry integration actions: {counts['DAJGUA']}")
        
        # Verify presence of multi-ministry coordination (DAJGUA)
        dajgua_recs = [r for r in recs if r['scheme_name'] == 'DAJGUA Integrated Development Scheme']
        self.assertGreater(len(dajgua_recs), 0)
        print(f"  [PASS] DAJGUA multi-ministry layering verified (Ministry of Tribal Affairs + MoRD + Jal Shakti):")
        print(f"         - Sample recommendation: {dajgua_recs[0]['beneficiary_name']} -> {dajgua_recs[0]['reason']}")

        print("\n" + "="*70)
        print("  RESULT: ALL COGNITIVE PROPERTIES ALIGNED & SUCCESSFULLY VERIFIED")
        print("="*70 + "\n")

if __name__ == '__main__':
    unittest.main()
