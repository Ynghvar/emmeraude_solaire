"""
Script pour effectuer l'OCR avec Azure Document Intelligence
sur les images extraites du PDF
"""
import os
import sys
import time
import base64

try:
    import requests
except ImportError:
    print("⚠️  requests n'est pas installé. Installation en cours...")
    os.system(f"{sys.executable} -m pip install requests")
    import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv n'est pas installé. Installation en cours...")
    os.system(f"{sys.executable} -m pip install python-dotenv")
    from dotenv import load_dotenv
    load_dotenv()

# Vérification des variables d'environnement
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

if not AZURE_API_KEY:
    raise ValueError("AZURE_OPENAI_API_KEY n'est pas définie")

print(f"Endpoint: {AZURE_ENDPOINT}")

def ocr_with_azure_vision(image_path):
    """
    Effectue l'OCR sur une image avec Azure Computer Vision via OpenAI
    """
    print(f"\n📷 Traitement de: {image_path}")
    
    # Lire et encoder l'image
    with open(image_path, "rb") as img_file:
        image_data = img_file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    print(f"  ✓ Taille de l'image: {len(image_data)} bytes")
    
    # Utiliser GPT-4 Vision pour l'OCR
    url = f"{AZURE_ENDPOINT}/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_API_KEY
    }
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "Tu es un système OCR expert. Extrais tout le texte visible de l'image fournie. Préserve la structure, les tableaux et la mise en forme autant que possible. Retourne uniquement le texte extrait, sans commentaire."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extrais tout le texte de cette image de document. Préserve les tableaux, la structure et tous les détails."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 4000,
        "temperature": 0
    }
    
    print(f"  📤 Envoi à GPT-4 Vision...")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            text = result['choices'][0]['message']['content']
            print(f"  ✅ Texte extrait: {len(text)} caractères")
            return text
        else:
            print(f"  ❌ Erreur: {response.status_code} - {response.text[:200]}")
            return f"ERREUR: {response.status_code}"
    except Exception as e:
        print(f"  ❌ Exception: {str(e)}")
        return f"ERREUR: {str(e)}"

if __name__ == "__main__":
    print("\n🔍 OCR avec Azure GPT-4 Vision")
    
    # Traiter les deux images
    image_dir = "data/temp_images"
    output_file = "data/ocr_results/POCHCETTE ELECTRICIENS_ocr_vision.txt"
    
    full_text = ""
    
    for i in range(1, 3):  # Pages 1 et 2
        image_path = f"{image_dir}/page_{i}.png"
        if os.path.exists(image_path):
            text = ocr_with_azure_vision(image_path)
            full_text += f"--- Page {i} ---\n{text}\n\n"
        else:
            print(f"⚠️  Image non trouvée: {image_path}")
    
    # Sauvegarder
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    print(f"\n✅ OCR terminé!")
    print(f"  Total: {len(full_text)} caractères")
    print(f"  💾 Sauvegardé dans: {output_file}")
