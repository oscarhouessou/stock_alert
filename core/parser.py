import os
import json
import re
from typing import Dict, Any

# Check if we're in production (Groq) or local (Ollama)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
USE_GROQ = GROQ_API_KEY is not None

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
    {"name": "...", "category": "alimentation", "unit": "Sac", "quantity": 10, "price": 2500}
  ]
}

Exemples:
- "Ajoute 10 sacs de riz à 2500 francs" → 
  {"action": "add", "products": [{"name": "riz", "category": "alimentation", "unit": "Sac", "quantity": 10, "price": 2500}]}

Règles pour deviner la catégorie:
- alimentation: riz, maïs, huile, sucre, sel, lait, farine, etc.
- vêtements: robe, pantalon, chemise, t-shirt, chaussures, etc.
- cosmétiques: savon, crème, parfum, maquillage, shampoing, etc.
- autres: tout le reste

Réponds UNIQUEMENT avec le JSON, rien d'autre."""


def parse_with_groq(text: str) -> Dict[str, Any]:
    """Use Groq API for parsing (production)"""
    from groq import Groq
    
    client = Groq(api_key=GROQ_API_KEY)
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0.1,
        max_tokens=500
    )
    
    return response.choices[0].message.content


def parse_with_ollama(text: str) -> str:
    """Use Ollama for parsing (local development)"""
    import ollama
    
    response = ollama.chat(model='llama3.2', messages=[
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': text},
    ])
    
    return response['message']['content']


def parse_intent(text: str) -> Dict[str, Any]:
    print(f"[PARSER] Input text: '{text}'")
    print(f"[PARSER] Using: {'Groq API' if USE_GROQ else 'Ollama (local)'}")
    
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
        # Choose backend based on environment
        if USE_GROQ:
            content = parse_with_groq(text)
        else:
            content = parse_with_ollama(text)
        
        print(f"[PARSER] LLM response: {content}")
        
        # Clean up response
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
        if json_match:
            content = json_match.group()
        
        result = json.loads(content)
        
        # Ensure products array exists
        if 'products' not in result:
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
