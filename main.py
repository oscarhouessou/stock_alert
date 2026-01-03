from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import shutil
import os
import uuid
from typing import List, Optional

# Load environment variables
load_dotenv()
from models import VoiceCommandResponse, Product, ProductInput, CATEGORIES, UNITS
from database import (
    init_db, get_all_products, add_product, remove_product, 
    get_product, record_sale, get_sales_history
)
from core.transcriber import transcribe_audio
from core.parser import parse_intent

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(
    title="StockAlert API",
    description="API de gestion d'inventaire par la voix. Nécessite le header 'X-User-ID' pour isoler les données.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
init_db()

# Dependency to get user_id
async def get_user_id(x_user_id: str = Header(..., description="Unique ID of the user")):
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header is required")
    return x_user_id

@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

@app.get("/products", response_model=List[Product])
async def get_products(user_id: str = Depends(get_user_id)):
    """Get all products for the current user."""
    return get_all_products(user_id)

@app.post("/products/add", response_model=Product)
async def add_product_endpoint(product: ProductInput, user_id: str = Depends(get_user_id)):
    """Add or update a single product."""
    return add_product(
        user_id=user_id,
        name=product.name,
        price=product.price,
        quantity=product.quantity,
        category=product.category,
        unit=product.unit,
        barcode=product.barcode,
        description=product.description
    )

@app.post("/products/add-multiple", response_model=List[Product])
async def add_multiple_products(products: List[ProductInput], user_id: str = Depends(get_user_id)):
    """Add or update multiple products at once."""
    results = []
    for p in products:
        res = add_product(
            user_id=user_id,
            name=p.name,
            price=p.price,
            quantity=p.quantity,
            category=p.category,
            unit=p.unit,
            barcode=p.barcode,
            description=p.description
        )
        results.append(res)
    return results

@app.post("/command/audio", response_model=VoiceCommandResponse)
async def process_audio_command(
    file: UploadFile = File(...), 
    user_id: str = Depends(get_user_id)
):
    """
    Process an audio file (WebM/WAV) containing a voice command.
    Returns the parsed intent and products found.
    """
    # Save temp file
    temp_filename = f"temp_{uuid.uuid4()}.webm"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 1. Transcribe
        text = transcribe_audio(temp_filename)
        
        # 2. Parse Intent
        intent = parse_intent(text)
        
        # 3. Prepare response
        products_found = []
        if (intent["action"] == "add" or intent["action"] == "sell") and intent.get("products"):
            for p in intent["products"]:
                products_found.append(ProductInput(**p))
        
        # Customize message based on intent/transcription
        text_lower = text.lower()
        hallucinations = ["sous-titrage", "merci d'avoir regardé", "amara.org", "sous-titres", "st' 501"]
        
        is_hallucination = any(h in text_lower for h in hallucinations)
        
        if not text or len(text.strip()) < 2 or is_hallucination:
            msg = "🎤 Je n'ai rien entendu. Parlez un peu plus fort."
        elif intent["action"] == "unknown":
            msg = "🤔 Commande non comprise. Réessayez."
        else:
            msg = "✅ Confirmez les produits ci-dessous"

        return VoiceCommandResponse(
            original_text=text,
            action=intent["action"],
            products=products_found,
            message=msg
        )
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@app.get("/sales")
async def get_sales(user_id: str = Depends(get_user_id)):
    return get_sales_history(user_id)

@app.post("/sales/confirm")
async def confirm_sale(
    products: List[ProductInput], 
    user_id: str = Depends(get_user_id)
):
    # Convert ProductInput to dict for database function
    items = [{'name': p.name, 'quantity': p.quantity} for p in products]
    
    success, message, total = record_sale(user_id, items)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
        
    return {"status": "success", "message": message, "total_amount": total}

@app.get("/api/categories")
def get_categories():
    return CATEGORIES

@app.get("/api/units")
def get_units():
    return UNITS

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
