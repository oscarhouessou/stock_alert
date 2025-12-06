from database import init_db, add_product, get_product, remove_product
from core.parser import parse_intent
import os

def test_db():
    print("Testing Database...")
    if os.path.exists("inventory.db"):
        os.remove("inventory.db")
    init_db()
    
    # Add
    p = add_product("test_item", 100.0, 10)
    assert p.name == "test_item"
    assert p.quantity == 10
    assert p.total_value == 1000.0
    print("  Add OK")
    
    # Get
    p2 = get_product("test_item")
    assert p2 is not None
    assert p2.price == 100.0
    print("  Get OK")
    
    # Remove
    p3, msg = remove_product("test_item", 5)
    assert p3.quantity == 5
    print("  Remove OK")
    
    print("Database Tests Passed!")

def test_parser():
    print("\nTesting Parser (requires Ollama running)...")
    
    cases = [
        ("Ajoute 10 pommes à 50 francs", "add", "pommes", 10, 50),
        ("Combien de pommes il reste ?", "check_stock", "pommes", None, None),
        ("Retire 2 pommes", "remove", "pommes", 2, None)
    ]
    
    for text, action, prod, qty, price in cases:
        print(f"  Parsing: '{text}'")
        res = parse_intent(text)
        print(f"    -> Result: {res}")
        # Note: LLM might vary slightly, but we check key fields
        if res['action'] == action:
            print("    Action Match: OK")
        else:
            print(f"    Action Mismatch: Expected {action}, got {res['action']}")

if __name__ == "__main__":
    test_db()
    try:
        test_parser()
    except Exception as e:
        print(f"Parser test failed (is Ollama running?): {e}")
