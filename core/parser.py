import os
import json
import re
from typing import Dict, Any

# Ensure we have Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("[PARSER] WARNING: GROQ_API_KEY not found in environment variables.")

CATEGORIES = ["alimentation", "vêtements", "cosmétiques", "autres"]
UNITS = ["Unité", "Kg", "Litre", "Carton", "Sac", "Paquet"]

SYSTEM_PROMPT = """Tu es un assistant de gestion d'inventaire. Analyse la phrase et extrais les produits au format JSON.

ACTION CRITIQUE: Si la phrase n'a aucun sens, est du bruit, concerne des "sous-titres", ou n'a aucun rapport avec l'inventaire (ex: "Merci d'avoir regardé", "Sous-titrage"), tu DOIS répondre EXACTEMENT ceci :
{"action": "unknown", "products": []}

IMPORTANT: Une commande peut contenir PLUSIEURS produits. Extrais-les tous.

Actions possibles: "add" (entrée stock), "sell" (vente/sortie), "check_stock", "check_value", "unknown"

Catégories: alimentation, vêtements, cosmétiques, autres
Unités: Unité, Kg, Litre, Carton, Sac, Paquet

Format de réponse (JSON uniquement):
{
  "action": "add",
  "products": [
    {"name": "...", "category": "alimentation", "unit": "Sac", "quantity": 10, "price": 2500}
  ]
}

Réponds UNIQUEMENT avec le JSON."""


def parse_with_groq(text: str) -> Dict[str, Any]:
    """Use Groq API for parsing (production)"""
    from groq import Groq
    
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY est requis pour le parsing.")

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


def parse_intent(text: str) -> Dict[str, Any]:
    print(f"[PARSER] Input text: '{text}'")
    
    # Handle empty or garbage text
    if not text or len(text) < 3:
        print("[PARSER] Text too short, returning unknown")
        return {"action": "unknown", "products": []}
    
    # Detect Whisper hallucinations
    hallucinations = [
        "sous-titrage", "sous-titres", "amara.org", "merci d'avoir regardé", 
        "subscribe", "abonnez-vous", "regardez la vidéo", "st' 501", "st'",
        "traduction de", "transcription de"
    ]
    low_text = text.lower()
    if any(h in low_text for h in hallucinations):
        print("[PARSER] Detected Whisper hallucination, returning unknown")
        return {"action": "unknown", "products": []}
    
    try:
        # Use Groq backend
        content = parse_with_groq(text)
        
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
