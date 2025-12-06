from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch
import os

client = TestClient(app)

def test_api_add_product():
    # Mock transcriber to return specific text
    with patch("main.transcribe_audio") as mock_transcribe:
        mock_transcribe.return_value = "Ajoute 10 stylos à 500 francs"
        
        # Create a dummy file
        with open("dummy.wav", "wb") as f:
            f.write(b"dummy audio content")
            
        with open("dummy.wav", "rb") as f:
            response = client.post("/command/audio", files={"file": ("dummy.wav", f, "audio/wav")})
            
        print(response.json())
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "add"
        assert data["product_data"]["name"] == "stylos"
        assert data["product_data"]["quantity"] == 10
        assert data["product_data"]["price"] == 500.0
        
        os.remove("dummy.wav")

def test_api_check_stock():
    # First ensure product exists (using DB directly or via API)
    # Let's rely on previous test or add it again
    # Mock transcriber
    with patch("main.transcribe_audio") as mock_transcribe:
        mock_transcribe.return_value = "Combien de stylos il reste ?"
        
        with open("dummy.wav", "wb") as f:
            f.write(b"dummy")
            
        with open("dummy.wav", "rb") as f:
            response = client.post("/command/audio", files={"file": ("dummy.wav", f, "audio/wav")})
            
        print(response.json())
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "check_stock"
        assert "stylos" in data["message"]
        
        os.remove("dummy.wav")

if __name__ == "__main__":
    try:
        test_api_add_product()
        print("API Add Test Passed")
        test_api_check_stock()
        print("API Check Stock Test Passed")
    except Exception as e:
        print(f"API Test Failed: {e}")
