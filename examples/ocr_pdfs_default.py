"""
Script OCR par défaut utilisant GPT-4 Vision
Traite tous les PDFs du dossier data/ et génère les fichiers *_ocr.txt
"""
import os
import sys
import time
import base64
from pathlib import Path
import json
from datetime import datetime

try:
    import fitz  # PyMuPDF
except ImportError:
    print("⚠️  PyMuPDF n'est pas installé. Installation en cours...")
    os.system(f"{sys.executable} -m pip install pymupdf")
    import fitz

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

# Variables d'environnement
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

if not AZURE_API_KEY:
    raise ValueError("AZURE_OPENAI_API_KEY n'est pas définie")

def extract_images_from_pdf(pdf_path, output_dir):
    """Extrait les pages d'un PDF en images haute résolution"""
    pdf_document = fitz.open(pdf_path)
    page_count = pdf_document.page_count
    
    # Créer un dossier temporaire pour ce PDF
    pdf_image_dir = Path(output_dir) / "temp" / pdf_path.stem
    pdf_image_dir.mkdir(parents=True, exist_ok=True)
    
    image_paths = []
    
    for page_num in range(page_count):
        page = pdf_document[page_num]
        
        # Convertir en image haute résolution (3x)
        mat = fitz.Matrix(3.0, 3.0)
        pix = page.get_pixmap(matrix=mat)
        
        # Sauvegarder
        img_path = pdf_image_dir / f"page_{page_num + 1}.png"
        pix.save(img_path)
        image_paths.append(img_path)
    
    pdf_document.close()
    return image_paths, page_count

def ocr_image_with_vision(image_path):
    """Effectue l'OCR sur une image avec GPT-4 Vision"""
    # Lire et encoder l'image
    with open(image_path, "rb") as img_file:
        image_data = img_file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # API GPT-4 Vision
    url = f"{AZURE_ENDPOINT}/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_API_KEY
    }
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "Tu es un système OCR expert. Extrais tout le texte visible de l'image fournie. Préserve la structure, les tableaux, les cases à cocher et la mise en forme autant que possible. Retourne uniquement le texte extrait, sans commentaire."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extrais tout le texte de cette image de document. Préserve les tableaux, la structure et tous les détails. Pour les cases à cocher, utilise ☐ pour les cases vides et ☑ ou ☒ pour les cases cochées."
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
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            text = result['choices'][0]['message']['content']
            return text, None
        else:
            error_msg = f"Erreur {response.status_code}: {response.text[:200]}"
            return None, error_msg
    except Exception as e:
        return None, str(e)

def process_pdf(pdf_path, output_dir):
    """Traite un PDF complet avec GPT-4 Vision"""
    print(f"\n📄 Traitement de: {pdf_path.name}")
    
    start_time = time.time()
    
    # Extraire les images
    print(f"  📸 Extraction des images...")
    image_paths, page_count = extract_images_from_pdf(pdf_path, output_dir)
    print(f"  ✓ {page_count} page(s) extraite(s)")
    
    # OCR sur chaque page
    print(f"  🔍 OCR avec GPT-4 Vision...")
    full_text = ""
    
    for i, img_path in enumerate(image_paths, 1):
        print(f"    Page {i}/{len(image_paths)}...", end=" ", flush=True)
        
        text, error = ocr_image_with_vision(img_path)
        
        if error:
            print(f"❌ Erreur: {error}")
            text = f"[ERREUR OCR: {error}]"
        else:
            print(f"✅ {len(text)} caractères")
        
        full_text += f"--- Page {i} ---\n{text}\n\n"
        
        # Pause pour éviter rate limiting
        if i < len(image_paths):
            time.sleep(1)
    
    # Sauvegarder
    output_file = Path(output_dir) / f"{pdf_path.stem}_ocr.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    elapsed_time = time.time() - start_time
    
    print(f"  ✅ Terminé en {elapsed_time:.1f}s")
    print(f"  💾 {len(full_text)} caractères -> {output_file.name}")
    
    return {
        "file": str(pdf_path),
        "pages": page_count,
        "chars": len(full_text),
        "time": elapsed_time
    }

if __name__ == "__main__":
    print("\n🔍 OCR avec GPT-4 Vision")
    print(f"   Endpoint: {AZURE_ENDPOINT}\n")
    
    # Trouver tous les PDFs dans data/
    data_dir = Path("data")
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ Aucun fichier PDF trouvé dans data/")
        sys.exit(1)
    
    print(f"📚 {len(pdf_files)} fichier(s) PDF trouvé(s):")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    
    # Créer le dossier de sortie
    output_dir = Path("data/ocr_results")
    output_dir.mkdir(exist_ok=True)
    
    # Traiter chaque PDF
    results = []
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] {'='*60}")
        
        result = process_pdf(pdf_path, output_dir)
        results.append(result)
    
    # Nettoyer les fichiers temporaires
    import shutil
    temp_dir = output_dir / "temp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        print(f"\n🗑️  Fichiers temporaires supprimés")
    
    # Résumé
    print(f"\n{'='*60}")
    print("📊 RÉSUMÉ")
    print(f"{'='*60}")
    
    total_pages = sum(r["pages"] for r in results)
    total_chars = sum(r["chars"] for r in results)
    total_time = sum(r["time"] for r in results)
    
    print(f"\n  ✅ {len(pdf_files)} fichiers traités")
    print(f"  📄 {total_pages} pages au total")
    print(f"  📝 {total_chars:,} caractères extraits")
    print(f"  ⏱️  Temps total: {total_time:.1f}s")
    print(f"  💾 Fichiers dans: {output_dir}/")
    
    print("\n✅ Traitement terminé!")
