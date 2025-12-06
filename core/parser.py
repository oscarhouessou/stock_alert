import ollama
import json
import re
from typing import Dict, Any, List

CATEGORIES = ["alimentation", "vêtements", "cosmétiques", "autres"]
UNITS = ["Unité", "Kg", "Litre", "Carton", "Sac", "Paquet"]

SYSTEM_PROMPT = """Tu es un assistant de gestion d'inventaire. Analyse la phrase et extrais les produits au format JSON.

IMPORTANT: Une commande peut contenir PLUSIEURS produits. Extrais-les tous.

Actions possibles: "add", "remove", "check_stock", "check_value", "unknown"

Catégories disponibles: alimentation, vêtements, cosmétiques, autres

Unités disponibles: Unité, Kg, Litre, Carton, Sac, Paquet

Format de réponse (JSON uniquement):
{
  "action": "add",
  "products": [
    {"name": "...", "category": "alimentation", "unit": "Sac", "quantity": 10, "price": 2500},
    {"name": "...", "category": "cosmétiques", "unit": "Unité", "quantity": 5, "price": 1000}
  ]
}

Exemples:
- "Ajoute 10 sacs de riz à 2500 francs et 5 bouteilles d'huile à 1500 francs" → 
  {"action": "add", "products": [{"name": "riz", "category": "alimentation", "unit": "Sac", "quantity": 10, "price": 2500}, {"name": "huile", "category": "alimentation", "unit": "Unité", "quantity": 5, "price": 1500}]}

- "Ajoute 20 robes à 5000 francs l'unité" →
  {"action": "add", "products": [{"name": "robes", "category": "vêtements", "unit": "Unité", "quantity": 20, "price": 5000}]}

- "Vendre 3 savons de beauté" →
  {"action": "remove", "products": [{"name": "savons de beauté", "category": "cosmétiques", "unit": "Unité", "quantity": 3, "price": null}]}

Règles pour deviner la catégorie:
- alimentation: riz, maïs, huile, sucre, sel, lait, farine, etc.
- vêtements: robe, pantalon, chemise, t-shirt, chaussures, etc.
- cosmétiques: savon, crème, parfum, maquillage, shampoing, etc.
- autres: tout le reste

Réponds UNIQUEMENT avec le JSON, rien d'autre."""

def parse_intent(text: str) -> Dict[str, Any]:
    print(f"[PARSER] Input text: '{text}'")
    
    # Handle empty or garbage text
    if not text or len(text) < 3:
        print("[PARSER] Text too short, returning unknown")
        return {"action": "unknown", "products": []}
    
    # Detect Whisper hallucinations
    hallucinations = ["sous-titres", "amara.org", "merci d'avoir regardé", "subscribe", "..."]
    if any(h in text.lower() for h in hallucinations):
        print("[PARSER] Detected Whisper hallucination, returning unknown")
        return {"action": "unknown", "products": []}
    
    try:
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': text},
        ])
        
        content = response['message']['content']
        print(f"[PARSER] Ollama response: {content}")
        
        # Clean up response
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
        if json_match:
            content = json_match.group()
        
        result = json.loads(content)
        
        # Ensure products array exists
        if 'products' not in result:
            # Convert old format to new format
            if 'product' in result:
                result['products'] = [{
                    'name': result.get('product'),
                    'category': result.get('category', 'autres'),
                    'unit': result.get('unit', 'Unité'),
                    'quantity': result.get('quantity'),
                    'price': result.get('price')
                }]
            else:
                result['products'] = []
        
        # Validate and clean products
        for p in result.get('products', []):
            if p.get('category') not in CATEGORIES:
                p['category'] = 'autres'
            if p.get('unit') not in UNITS:
                p['unit'] = 'Unité'
        
        print(f"[PARSER] Parsed result: {result}")
        return result
        
    except json.JSONDecodeError as e:
        print(f"[PARSER] JSON decode error: {e}")
        return {"action": "unknown", "products": []}
    except Exception as e:
        print(f"[PARSER] Error: {e}")
        return {"action": "unknown", "products": []}
