#!/bin/bash

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting StockAlert (Cloud Mode)...${NC}"

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${RED}❌ Erreur: Fichier .env manquant.${NC}"
    echo "Copiez .env.example vers .env et ajoutez votre GROQ_API_KEY."
    exit 1
fi

# Check if Groq is configured
if ! grep -q "GROQ_API_KEY=gsk_" .env 2>/dev/null; then
    echo -e "${RED}❌ Erreur: GROQ_API_KEY non configurée dans .env${NC}"
    echo "L'API nécessite Groq pour le parsing et la transcription."
    exit 1
fi

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}⚠️  Attention: ffmpeg n'est pas installé. La transcription audio risque d'échouer.${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   StockAlert - Gestion d'inventaire par la voix${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "🌐 Ouvrez http://localhost:8000 dans votre navigateur"
echo ""

# Run the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
