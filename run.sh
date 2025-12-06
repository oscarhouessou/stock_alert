#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting StockAlert...${NC}"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama n'est pas installé. Installez-le depuis https://ollama.ai${NC}"
    exit 1
fi

# Check if Ollama is already running
if ! curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo -e "${YELLOW}📦 Démarrage d'Ollama en arrière-plan...${NC}"
    ollama serve > /dev/null 2>&1 &
    OLLAMA_PID=$!
    echo "   Ollama PID: $OLLAMA_PID"
    
    # Wait for Ollama to start
    echo -n "   Attente du démarrage"
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
else
    echo -e "${GREEN}✓ Ollama est déjà en cours d'exécution${NC}"
fi

# Check if llama3.2 model is available
echo -n "🔍 Vérification du modèle llama3.2..."
if ! ollama list | grep -q "llama3.2"; then
    echo ""
    echo -e "${YELLOW}📥 Téléchargement du modèle llama3.2 (première fois uniquement)...${NC}"
    ollama pull llama3.2
else
    echo -e " ${GREEN}✓${NC}"
fi

# Check if faster-whisper model exists
if [ ! -d "models/faster-whisper-small" ]; then
    echo -e "${YELLOW}📥 Téléchargement du modèle Whisper...${NC}"
    python download_model.py
else
    echo -e "${GREEN}✓ Modèle Whisper disponible${NC}"
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
