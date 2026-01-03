import os
import unittest
import sqlite3
from database import init_db, add_product, remove_product, record_sale, get_all_products, get_product
import database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Use a temporary database for tests
        self.test_db = "test_inventory.db"
        database.DB_NAME = self.test_db
        init_db()
        self.user_id = "test_user"

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_and_get_product(self):
        # Test adding a product
        add_product(self.user_id, "Riz", 1000, 10, "alimentation", "Sac")
        
        # Test case-insensitive retrieval (which we just implemented)
        product = get_product(self.user_id, "riz")
        self.assertIsNotNone(product)
        self.assertEqual(product.name, "Riz")
        self.assertEqual(product.quantity, 10)
        self.assertEqual(product.price, 1000)

    def test_remove_product(self):
        add_product(self.user_id, "Lait", 500, 20)
        
        # Exact match
        remove_product(self.user_id, "Lait", 5)
        product = get_product(self.user_id, "Lait")
        self.assertEqual(product.quantity, 15)
        
        # Case-insensitive update
        remove_product(self.user_id, "lait", 5)
        product = get_product(self.user_id, "Lait")
        self.assertEqual(product.quantity, 10)

    def test_record_sale(self):
        add_product(self.user_id, "Sucre", 700, 100)
        
        items = [
            {"name": "sucre", "quantity": 10}
        ]
        
        success, message, total = record_sale(self.user_id, items)
        self.assertTrue(success)
        self.assertEqual(total, 7000)
        
        product = get_product(self.user_id, "Sucre")
        self.assertEqual(product.quantity, 90)

    def test_sale_insufficient_stock(self):
        add_product(self.user_id, "Sel", 100, 5)
        items = [{"name": "sel", "quantity": 10}]
        success, message, total = record_sale(self.user_id, items)
        self.assertFalse(success)
        self.assertIn("Stock insuffisant", message)

if __name__ == "__main__":
    unittest.main()
