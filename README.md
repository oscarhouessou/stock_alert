# 📦 StockAlert API
API de gestion d'inventaire intelligente par la voix.

## 🚀 Démarrage Rapide

### Pré-requis
- Python 3.11+
- FFmpeg (pour le traitement audio)
- Clé API Groq (recommandé pour la prod) ou Ollama (local)

### Installation
```bash
./setup.sh
./run.sh
```

L'API sera accessible sur `http://localhost:8000`.
Documentation Swagger : `http://localhost:8000/docs`.

---

## 📱 Intégration Mobile

L'API est conçue pour être facilement intégrée dans des applications mobiles (Flutter, React Native, Swift, Kotlin).

### 🔐 Authentification & Isolation
L'API utilise un header simple pour isoler les données des utilisateurs.
**Header requis :** `X-User-ID`

Exemple :
```http
GET /products HTTP/1.1
Host: api.stockalert.com
X-User-ID: user_123456
```
*Générez un UUID unique sur le mobile lors de la première installation et stockez-le.*

### 🎤 Commande Vocale
Pour envoyer une commande vocale :

**Endpoint :** `POST /command/audio`
**Format :** `multipart/form-data`
**Fichier :** `file` (audio/webm ou audio/wav)

Exemple (cURL) :
```bash
curl -X POST "http://localhost:8000/command/audio" \
     -H "X-User-ID: user_123" \
     -F "file=@commande.wav"
```

**Réponse :**
```json
{
  "original_text": "Ajoute 5 sacs de riz",
  "action": "add",
  "products": [
    {
      "name": "riz",
      "category": "alimentation",
      "unit": "Sac",
      "quantity": 5,
      "price": 0
    }
  ],
  "message": "Confirmez les produits ci-dessous"
}
```

### 📦 Gestion des Produits

#### Récupérer le stock
`GET /products`

#### Ajouter/Mettre à jour un produit
`POST /products/add`
```json
{
  "name": "Riz Parfum",
  "quantity": 10,
  "price": 12500,
  "category": "alimentation",
  "unit": "Sac"
}
```

#### Ajout Multiple (Batch)
`POST /products/add-multiple`
Envoyez une liste de produits pour réduire les appels réseau.

---

## 🛠️ Stack Technique
- **Framework** : FastAPI (Python)
- **Transcription** : Groq Whisper (Prod) / faster-whisper (Local)
- **LLM** : Groq Llama 3 (Prod) / Ollama (Local)
- **Base de données** : SQLite (avec support multi-utilisateurs)
