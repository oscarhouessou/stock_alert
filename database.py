import sqlite3
from typing import List, Optional, Tuple, Dict
from models import Product, ProductInput
from datetime import datetime

DB_NAME = "inventory.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check current schema
    cursor.execute("PRAGMA table_info(products)")
    columns = {col[1]: col for col in cursor.fetchall()}
    
    # Check if we need to migrate (if UNIQUE is only on name or user_id is missing)
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='products'")
    table_sql = cursor.fetchone()
    
    needs_migration = False
    if table_sql:
        sql = table_sql[0].lower()
        if 'unique (user_id, name)' not in sql and 'unique(user_id, name)' not in sql:
            needs_migration = True
            print("📦 Migration de la table 'products' nécessaire...")

    if needs_migration:
        # 1. Rename old table
        cursor.execute("ALTER TABLE products RENAME TO products_old")
        
        # 2. Create new table with correct schema
        cursor.execute('''
            CREATE TABLE products (
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
        
        # 3. Migrate data
        # Mapping old columns to new ones. Handle missing user_id.
        old_cols = columns.keys()
        cols_to_copy = [c for c in old_cols if c in ['id', 'name', 'category', 'unit', 'price', 'quantity', 'barcode', 'description', 'total_value', 'user_id']]
        cols_str = ", ".join(cols_to_copy)
        
        cursor.execute(f"INSERT INTO products ({cols_str}) SELECT {cols_str} FROM products_old")
        
        # 4. Drop old table
        cursor.execute("DROP TABLE products_old")
        print("✅ Migration terminée !")
    else:
        # Standard creation if doesn't exist
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

    # Table des ventes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            total_amount REAL NOT NULL DEFAULT 0
        )
    ''')

    # Détail des ventes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY(sale_id) REFERENCES sales(id)
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
    
    # Clean input
    name = name.strip()
    
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
    # Clean input
    name = name.strip()
    
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

def record_sale(user_id: str, items: List[Dict]) -> Tuple[bool, str, float]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    total_sale_amount = 0
    sale_items_data = []
    
    try:
        for item in items:
            p_name = item['name'].strip()
            cursor.execute("SELECT * FROM products WHERE user_id = ? AND name = ?", (user_id, p_name))
            product = cursor.fetchone()
            
            if not product:
                return False, f"Produit inconnu : {item['name']}", 0
            
            if product['quantity'] < item['quantity']:
                return False, f"Stock insuffisant pour {item['name']}", 0
            
            item_total = product['price'] * item['quantity']
            total_sale_amount += item_total
            
            sale_items_data.append({
                'product_id': product['id'],
                'name': product['name'],
                'quantity': item['quantity'],
                'unit_price': product['price'],
                'total_price': item_total,
                'new_stock': product['quantity'] - item['quantity']
            })
            
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO sales (user_id, date, total_amount) VALUES (?, ?, ?)", 
                       (user_id, date_str, total_sale_amount))
        sale_id = cursor.lastrowid
        
        for item_data in sale_items_data:
            cursor.execute('''
                INSERT INTO sale_items (sale_id, product_name, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (sale_id, item_data['name'], item_data['quantity'], 
                  item_data['unit_price'], item_data['total_price']))
            
            cursor.execute("UPDATE products SET quantity = ?, total_value = ? WHERE id = ?",
                           (item_data['new_stock'], item_data['unit_price'] * item_data['new_stock'], item_data['product_id']))
            
        conn.commit()
        return True, "Vente enregistrée", total_sale_amount
        
    except Exception as e:
        conn.rollback()
        return False, str(e), 0
    finally:
        conn.close()

def get_sales_history(user_id: str):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales WHERE user_id = ? ORDER BY date DESC LIMIT 50", (user_id,))
    sales = cursor.fetchall()
    conn.close()
    return [dict(s) for s in sales]
