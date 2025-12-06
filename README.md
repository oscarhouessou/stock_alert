# StockAlert - Voice Inventory App

Application d'inventaire contrôlée par la voix utilisant FastAPI, Faster-Whisper et Ollama.

## Prérequis

1. **Python 3.9+**
2. **Ollama** installé et tournant (`ollama serve`).
3. Modèle Llama 3.2 téléchargé : `ollama pull llama3.2`
4. **FFmpeg** (requis pour Whisper, souvent installé par défaut ou via `brew install ffmpeg`).

## Installation

```bash
pip install -r requirements.txt
```

## Démarrage

Lancer le serveur API :

```bash
./run.sh
```
Ou manuellement :
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Utilisation

### Endpoint Vocal
`POST /command/audio`
- Envoyer un fichier audio (wav, mp3, etc.) dans le champ `file`.
- Réponse JSON avec l'action détectée et le résultat.

### Exemple de commandes vocales
- "Ajoute 15 boîtes de lait à 1200 francs l'unité"
- "Combien de riz il reste ?"
- "Retire 5 sacs de ciment"
- "Quel est le prix du sucre ?"

## Structure du Projet

- `main.py` : Point d'entrée de l'API.
- `database.py` : Gestion de la base de données SQLite.
- `core/transcriber.py` : Transcription audio avec Faster-Whisper.
- `core/parser.py` : Analyse d'intention avec Ollama.
- `models.py` : Modèles de données Pydantic.
# stock_alert
