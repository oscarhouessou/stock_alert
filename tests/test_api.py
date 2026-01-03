import unittest
from fastapi.testclient import TestClient
from main import app
import database
import os

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_db = "test_api_inventory.db"
        database.DB_NAME = self.test_db
        database.init_db()
        self.headers = {"X-User-ID": "test_api_user"}

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_get_products_empty(self):
        response = self.client.get("/products", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_add_product_endpoint(self):
        product_data = [{
            "name": "Bread",
            "category": "alimentation",
            "unit": "Unité",
            "price": 500,
            "quantity": 10
        }]
        response = self.client.post("/products/add-multiple", json=product_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["name"], "Bread")

    def test_confirm_sale_endpoint(self):
        # First add a product
        self.client.post("/products/add-multiple", json=[{
            "name": "Coffee", "price": 1000, "quantity": 10
        }], headers=self.headers)
        
        # Then sell it
        sale_data = [{"name": "coffee", "quantity": 2}]
        response = self.client.post("/sales/confirm", json=sale_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_amount"], 2000)

if __name__ == "__main__":
    unittest.main()
