# 📦 StockAlert API
API de gestion d'inventaire intelligente par la voix.

## 🚀 Démarrage Rapide

### Pré-requis
- Python 3.11+
- FFmpeg (indispensable pour le traitement audio)
- Clé API Groq (obligatoire)

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

## 🤝 Partage & Intégration Équipe

Pour permettre à l'équipe mobile d'intégrer l'API, vous pouvez utiliser les méthodes suivantes :

### 1. Documentation Interactive (Swagger)
La documentation complète des endpoints, des modèles de données et des tests est disponible en direct :
- **Swagger UI :** `http://localhost:8000/docs` (Le plus recommandé)
- **Redoc :** `http://localhost:8000/redoc`

### 2. Partage sur le réseau local
Si vos collègues sont sur le même réseau Wi-Fi :
1. Trouvez votre IP locale (ex: `192.168.1.15`).
2. Partagez l'URL : `http://192.168.1.15:8000/docs`.

### 3. Partage externe rapide (ngrok)
Pour un accès distant sans déploiement :
```bash
ngrok http 8000
```
Puis communiquez l'URL fournie par ngrok (ex: `https://abcd-123.ngrok-free.app/docs`).

### 4. Import dans Postman
Pour les développeurs préférant Postman :
1. Allez sur `http://localhost:8000/openapi.json`.
2. Enregistrez le fichier JSON.
3. Dans Postman, cliquez sur **Import** et sélectionnez ce fichier. Cela créera automatiquement toute la collection.

---

## 🛠️ Stack Technique
- **Framework** : FastAPI (Python)
- **Transcription** : Groq Whisper (Cloud)
- **LLM** : Groq Llama 3 (Cloud)
- **Base de données** : SQLite (support multi-utilisateurs via le header `X-User-ID`)
