import sqlite3
from typing import Optional, List, Tuple
from models import Product, ProductInput

DB_NAME = "inventory.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if we need to migrate (add new columns)
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'category' not in columns:
        # Need to recreate table with new columns
        cursor.execute('DROP TABLE IF EXISTS products')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT DEFAULT 'autres',
            unit TEXT DEFAULT 'Unité',
            price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 0,
            barcode TEXT,
            description TEXT,
            total_value REAL NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_product(name: str) -> Optional[Product]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Product(
            id=row[0], name=row[1], category=row[2], unit=row[3],
            price=row[4], quantity=row[5], barcode=row[6], 
            description=row[7], total_value=row[8]
        )
    return None

def add_product(name: str, price: float, quantity: int, 
                category: str = "autres", unit: str = "Unité",
                barcode: str = None, description: str = None) -> Product:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT * FROM products WHERE name = ?", (name,))
    existing = cursor.fetchone()
    
    if existing:
        # Update
        new_qty = existing[5] + quantity
        new_price = price if price > 0 else existing[4]
        new_category = category if category != "autres" else existing[2]
        new_unit = unit if unit != "Unité" else existing[3]
        new_total = new_price * new_qty
        new_barcode = barcode if barcode else existing[6]
        new_desc = description if description else existing[7]
        
        cursor.execute('''
            UPDATE products SET price = ?, quantity = ?, total_value = ?,
            category = ?, unit = ?, barcode = ?, description = ?
            WHERE id = ?
        ''', (new_price, new_qty, new_total, new_category, new_unit, 
              new_barcode, new_desc, existing[0]))
        product_id = existing[0]
    else:
        # Insert
        total_value = price * quantity
        cursor.execute('''
            INSERT INTO products (name, category, unit, price, quantity, barcode, description, total_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, category, unit, price, quantity, barcode, description, total_value))
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

def remove_product(name: str, quantity: int) -> Tuple[Optional[Product], str]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products WHERE name = ?", (name,))
    existing = cursor.fetchone()
    
    if not existing:
        conn.close()
        return None, "Produit non trouvé."
        
    current_qty = existing[5]
    if current_qty < quantity:
        conn.close()
        return Product(
            id=existing[0], name=existing[1], category=existing[2], unit=existing[3],
            price=existing[4], quantity=existing[5], barcode=existing[6],
            description=existing[7], total_value=existing[8]
        ), f"Stock insuffisant. Seulement {current_qty} en stock."
        
    new_qty = current_qty - quantity
    new_total = existing[4] * new_qty
    
    cursor.execute('''
        UPDATE products SET quantity = ?, total_value = ? WHERE id = ?
    ''', (new_qty, new_total, existing[0]))
    
    conn.commit()
    conn.close()
    
    return Product(
        id=existing[0], name=existing[1], category=existing[2], unit=existing[3],
        price=existing[4], quantity=new_qty, barcode=existing[6],
        description=existing[7], total_value=new_total
    ), "Stock mis à jour."

def get_all_products():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    conn.close()
    return [
        Product(
            id=r[0], name=r[1], category=r[2], unit=r[3],
            price=r[4], quantity=r[5], barcode=r[6],
            description=r[7], total_value=r[8]
        ) for r in rows
    ]
