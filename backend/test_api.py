import unittest
import json
import os
import sys

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.app import app, DB_PATH

class TestFRAAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
    def test_database_exists(self):
        self.assertTrue(os.path.exists(DB_PATH), f"Database file not found at {DB_PATH}")

    def test_get_villages(self):
        response = self.app.get('/api/villages')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        # Check first village structure
        v = data[0]
        self.assertIn('id', v)
        self.assertIn('name', v)
        self.assertIn('latitude', v)
        self.assertIn('longitude', v)
        self.assertIn('state_name', v)
        self.assertIn('claims', v)
        self.assertIn('assets', v)
        self.assertIsInstance(v['claims'], list)
        self.assertIsInstance(v['assets'], list)

    def test_get_stats(self):
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_claims', data)
        self.assertIn('total_area_acres', data)
        self.assertIn('status_counts', data)
        self.assertIn('state_breakdown', data)
        self.assertIn('asset_counts', data)

    def test_digitize_ocr_ner(self):
        sample_doc = {
            "document_name": "test_legacy_claim_99.pdf",
            "text_content": "Individual rights to Ram Gond. Forest land claimed at village Adilabad Pada, Telangana. Area of agricultural plot is 4.5 acres. Coordinates: Lat 19.671 Lng 78.532."
        }
        response = self.app.post('/api/digitize', 
                               data=json.dumps(sample_doc), 
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('claim_id', data)
        self.assertEqual(data['extracted_metadata']['claimant_name'], "Ram Gond")
        self.assertEqual(data['extracted_metadata']['claim_type'], "IFR")
        self.assertEqual(data['extracted_metadata']['area_acres'], 4.5)
        self.assertEqual(data['extracted_metadata']['tribal_group'], "Gond")

    def test_detect_assets(self):
        # We need a village ID. Let's get the first village ID.
        villages_resp = self.app.get('/api/villages')
        villages = json.loads(villages_resp.data)
        v_id = villages[0]['id']
        
        # Trigger asset detection
        response = self.app.post('/api/detect-assets', 
                               data=json.dumps({"village_id": v_id}),
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('detected_assets', data)
        self.assertGreater(len(data['detected_assets']), 0)
        self.assertIn('updated_water_index', data)
        self.assertIn('updated_forest_cover', data)

    def test_dss_evaluate(self):
        dss_payload = {
            "water_threshold": 0.45,
            "forest_threshold": 60.0,
            "infra_threshold": 0.5,
            "land_threshold": 2.5
        }
        response = self.app.post('/api/dss/evaluate', 
                               data=json.dumps(dss_payload), 
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('recommendations', data)
        self.assertIn('counts', data)
        self.assertIsInstance(data['recommendations'], list)
        self.assertGreater(len(data['recommendations']), 0)

if __name__ == '__main__':
    unittest.main()
