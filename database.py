import sqlite3
from typing import Optional, List, Tuple
from models import Product, ProductInput

DB_NAME = "inventory.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check for user_id column
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'user_id' not in columns:
        # Add user_id column if missing
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN user_id TEXT DEFAULT 'default'")
        except:
            # If table doesn't exist or other error, recreate
            pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            name TEXT NOT NULL,
            category TEXT DEFAULT 'autres',
            unit TEXT DEFAULT 'Unité',
            price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 0,
            barcode TEXT,
            description TEXT,
            total_value REAL NOT NULL DEFAULT 0,
            UNIQUE(user_id, name)
        )
    ''')
    conn.commit()
    conn.close()

def get_product(user_id: str, name: str) -> Optional[Product]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE user_id = ? AND name = ?", (user_id, name))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Product(
            id=row["id"], 
            name=row["name"], 
            category=row["category"], 
            unit=row["unit"],
            price=row["price"], 
            quantity=row["quantity"], 
            barcode=row["barcode"], 
            description=row["description"], 
            total_value=row["total_value"]
        )
    return None

def add_product(user_id: str, name: str, price: float, quantity: int, 
                category: str = "autres", unit: str = "Unité",
                barcode: str = None, description: str = None) -> Product:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if exists for this user
    cursor.execute("SELECT * FROM products WHERE user_id = ? AND name = ?", (user_id, name))
    existing = cursor.fetchone()
    
    if existing:
        # Update
        new_qty = existing["quantity"] + quantity
        new_price = price if price > 0 else existing["price"]
        new_category = category if category != "autres" else existing["category"]
        new_unit = unit if unit != "Unité" else existing["unit"]
        new_total = new_price * new_qty
        new_barcode = barcode if barcode else existing["barcode"]
        new_desc = description if description else existing["description"]
        
        cursor.execute('''
            UPDATE products SET price = ?, quantity = ?, total_value = ?,
            category = ?, unit = ?, barcode = ?, description = ?
            WHERE id = ?
        ''', (new_price, new_qty, new_total, new_category, new_unit, 
              new_barcode, new_desc, existing["id"]))
        product_id = existing["id"]
    else:
        # Insert
        total_value = price * quantity
        cursor.execute('''
            INSERT INTO products (user_id, name, category, unit, price, quantity, barcode, description, total_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, category, unit, price, quantity, barcode, description, total_value))
        product_id = cursor.lastrowid
        new_qty = quantity
        new_price = price
        new_total = total_value
        new_category = category
        new_unit = unit
        new_barcode = barcode
        new_desc = description
        
    conn.commit()
    conn.close()
    
    return Product(
        id=product_id, name=name, category=new_category, unit=new_unit,
        price=new_price, quantity=new_qty, barcode=new_barcode,
        description=new_desc, total_value=new_total
    )

def remove_product(user_id: str, name: str, quantity: int) -> Tuple[Optional[Product], str]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products WHERE user_id = ? AND name = ?", (user_id, name))
    existing = cursor.fetchone()
    
    if not existing:
        conn.close()
        return None, "Produit non trouvé."
        
    current_qty = existing["quantity"]
    if current_qty < quantity:
        conn.close()
        return Product(
            id=existing["id"], 
            name=existing["name"], 
            category=existing["category"], 
            unit=existing["unit"],
            price=existing["price"], 
            quantity=existing["quantity"], 
            barcode=existing["barcode"],
            description=existing["description"], 
            total_value=existing["total_value"]
        ), f"Stock insuffisant. Seulement {current_qty} en stock."
        
    new_qty = current_qty - quantity
    new_total = existing["price"] * new_qty
    
    cursor.execute('''
        UPDATE products SET quantity = ?, total_value = ? WHERE id = ?
    ''', (new_qty, new_total, existing["id"]))
    
    conn.commit()
    conn.close()
    
    return Product(
        id=existing["id"], 
        name=existing["name"], 
        category=existing["category"], 
        unit=existing["unit"],
        price=existing["price"], 
        quantity=new_qty, 
        barcode=existing["barcode"],
        description=existing["description"], 
        total_value=new_total
    ), "Stock mis à jour."

def get_all_products(user_id: str):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        Product(
            id=r["id"], 
            name=r["name"], 
            category=r["category"], 
            unit=r["unit"],
            price=r["price"], 
            quantity=r["quantity"], 
            barcode=r["barcode"],
            description=r["description"], 
            total_value=r["total_value"]
        ) for r in rows
    ]
