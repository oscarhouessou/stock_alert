from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import shutil
import os
import uuid

# Load environment variables
load_dotenv()
from models import VoiceCommandResponse, Product, ProductInput, CATEGORIES, UNITS
from database import init_db, add_product, remove_product, get_product, get_all_products
from core.transcriber import transcribe_audio
from core.parser import parse_intent
from pydantic import BaseModel
from typing import List, Optional

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Voice Inventory App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/api/categories")
def get_categories():
    """Return available categories"""
    return CATEGORIES

@app.get("/api/units")
def get_units():
    """Return available units"""
    return UNITS

@app.post("/command/audio")
async def process_audio_command(file: UploadFile = File(...)):
    print(f"\n{'='*50}")
    print(f"[API] Received audio file: {file.filename}")
    print(f"[API] Content type: {file.content_type}")
    
    # Save temp file
    temp_filename = f"temp_{uuid.uuid4()}.webm"
    with open(temp_filename, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        print(f"[API] Saved temp file: {temp_filename} ({len(content)} bytes)")
        
    try:
        # 1. Transcribe
        print(f"[API] Starting transcription...")
        text = transcribe_audio(temp_filename)
        print(f"[API] Transcribed: '{text}'")
        
        # 2. Parse Intent (now supports multiple products)
        print(f"[API] Parsing intent with Ollama...")
        intent = parse_intent(text)
        print(f"[API] Intent: {intent}")
        
        action = intent.get("action", "unknown")
        products = intent.get("products", [])
        
        # Convert to ProductInput list
        product_inputs = []
        for p in products:
            product_inputs.append(ProductInput(
                name=p.get('name', ''),
                category=p.get('category', 'autres'),
                unit=p.get('unit', 'Unité'),
                quantity=p.get('quantity') or 0,
                price=p.get('price') or 0,
                description=p.get('description')
            ))
        
        # Build message
        if action == "add" and product_inputs:
            product_names = [f"{p.quantity} {p.name}" for p in product_inputs]
            message = f"Produits à ajouter: {', '.join(product_names)}"
        elif action == "remove" and product_inputs:
            product_names = [f"{p.quantity} {p.name}" for p in product_inputs]
            message = f"Produits à retirer: {', '.join(product_names)}"
        elif action == "unknown":
            message = "Commande non comprise. Veuillez réessayer."
        else:
            message = f"Action: {action}"

        return {
            "original_text": text,
            "action": action,
            "products": [p.dict() for p in product_inputs],
            "message": message
        }
        
    except Exception as e:
        print(f"[API] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@app.get("/products")
def list_products():
    return get_all_products()

class AddProductRequest(BaseModel):
    name: str
    category: str = "autres"
    unit: str = "Unité"
    price: float = 0
    quantity: int = 0
    barcode: Optional[str] = None
    description: Optional[str] = None

class AddMultipleProductsRequest(BaseModel):
    products: List[AddProductRequest]

@app.post("/products/add")
def add_product_endpoint(req: AddProductRequest):
    """Add or update a single product"""
    product = add_product(
        name=req.name, 
        price=req.price, 
        quantity=req.quantity,
        category=req.category,
        unit=req.unit,
        barcode=req.barcode,
        description=req.description
    )
    return product

@app.post("/products/add-multiple")
def add_multiple_products(req: AddMultipleProductsRequest):
    """Add or update multiple products at once"""
    results = []
    for p in req.products:
        product = add_product(
            name=p.name,
            price=p.price,
            quantity=p.quantity,
            category=p.category,
            unit=p.unit,
            barcode=p.barcode,
            description=p.description
        )
        results.append(product)
    return results
