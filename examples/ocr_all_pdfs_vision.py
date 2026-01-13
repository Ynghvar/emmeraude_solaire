"""
Script pour effectuer l'OCR avec GPT-4 Vision sur tous les PDFs
et comparer avec les résultats de Mistral Document AI
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
    """
    Extrait les pages d'un PDF en images haute résolution
    """
    print(f"\n📄 Extraction des images de: {pdf_path.name}")
    
    pdf_document = fitz.open(pdf_path)
    page_count = pdf_document.page_count
    print(f"  ✓ Nombre de pages: {page_count}")
    
    # Créer un dossier pour ce PDF
    pdf_image_dir = Path(output_dir) / pdf_path.stem
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
        
        print(f"    Page {page_num + 1}: {pix.width}x{pix.height}px -> {img_path.name}")
    
    pdf_document.close()
    return image_paths

def ocr_image_with_vision(image_path):
    """
    Effectue l'OCR sur une image avec GPT-4 Vision
    """
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

def process_pdf_with_vision(pdf_path, temp_dir, output_dir):
    """
    Traite un PDF complet avec GPT-4 Vision
    """
    print(f"\n{'='*80}")
    print(f"📄 Traitement de: {pdf_path.name}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    # Extraire les images
    image_paths = extract_images_from_pdf(pdf_path, temp_dir)
    
    # OCR sur chaque page
    print(f"\n  📤 OCR avec GPT-4 Vision...")
    full_text = ""
    page_results = []
    
    for i, img_path in enumerate(image_paths, 1):
        print(f"    Page {i}/{len(image_paths)}...", end=" ", flush=True)
        
        text, error = ocr_image_with_vision(img_path)
        
        if error:
            print(f"❌ Erreur: {error}")
            text = f"[ERREUR OCR: {error}]"
        else:
            print(f"✅ {len(text)} caractères")
        
        page_results.append({
            "page": i,
            "text": text,
            "error": error
        })
        
        full_text += f"--- Page {i} ---\n{text}\n\n"
        
        # Pause pour éviter rate limiting
        if i < len(image_paths):
            time.sleep(1)
    
    # Sauvegarder
    output_file = Path(output_dir) / f"{pdf_path.stem}_ocr_vision.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    elapsed_time = time.time() - start_time
    
    print(f"\n  ✅ Terminé en {elapsed_time:.1f}s")
    print(f"  📊 Total: {len(full_text)} caractères")
    print(f"  💾 Sauvegardé: {output_file.name}")
    
    return {
        "file": str(pdf_path),
        "total_pages": len(image_paths),
        "total_chars": len(full_text),
        "elapsed_time": elapsed_time,
        "output_file": str(output_file),
        "page_results": page_results
    }

def compare_with_mistral(pdf_path, vision_result):
    """
    Compare les résultats Vision avec ceux de Mistral
    """
    mistral_file = Path("data/ocr_results") / f"{pdf_path.stem}_ocr.txt"
    
    if not mistral_file.exists():
        return None
    
    with open(mistral_file, "r", encoding="utf-8") as f:
        mistral_text = f.read()
    
    return {
        "mistral_chars": len(mistral_text),
        "vision_chars": vision_result["total_chars"],
        "difference": vision_result["total_chars"] - len(mistral_text),
        "percent_increase": ((vision_result["total_chars"] - len(mistral_text)) / len(mistral_text) * 100) if len(mistral_text) > 0 else 0
    }

if __name__ == "__main__":
    print("\n🔍 OCR avec GPT-4 Vision - Traitement complet")
    print(f"   Endpoint: {AZURE_ENDPOINT}")
    print()
    
    # Trouver tous les PDFs
    data_dir = Path("data")
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ Aucun fichier PDF trouvé")
        sys.exit(1)
    
    print(f"📚 {len(pdf_files)} fichier(s) PDF trouvé(s):")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    
    # Créer les dossiers
    temp_dir = Path("data/temp_images")
    output_dir = Path("data/ocr_results")
    temp_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Traiter chaque PDF
    all_results = []
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        result = process_pdf_with_vision(pdf_path, temp_dir, output_dir)
        
        # Comparer avec Mistral
        comparison = compare_with_mistral(pdf_path, result)
        if comparison:
            result["comparison"] = comparison
            print(f"\n  📊 Comparaison avec Mistral:")
            print(f"     Mistral: {comparison['mistral_chars']} caractères")
            print(f"     Vision:  {comparison['vision_chars']} caractères")
            print(f"     Gain:    {comparison['difference']:+d} ({comparison['percent_increase']:+.1f}%)")
        
        all_results.append(result)
    
    # Sauvegarder le rapport
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_files": len(pdf_files),
        "results": all_results
    }
    
    report_file = output_dir / "ocr_vision_summary.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Afficher le résumé
    print(f"\n{'='*80}")
    print("📊 RÉSUMÉ GÉNÉRAL")
    print(f"{'='*80}")
    
    total_pages = sum(r["total_pages"] for r in all_results)
    total_chars = sum(r["total_chars"] for r in all_results)
    total_time = sum(r["elapsed_time"] for r in all_results)
    
    print(f"\n  ✅ {len(pdf_files)} fichiers traités")
    print(f"  📄 {total_pages} pages au total")
    print(f"  📝 {total_chars:,} caractères extraits")
    print(f"  ⏱️  Temps total: {total_time:.1f}s")
    print(f"  💾 Rapport: {report_file}")
    
    # Comparaisons
    comparisons = [r.get("comparison") for r in all_results if r.get("comparison")]
    if comparisons:
        avg_gain = sum(c["percent_increase"] for c in comparisons) / len(comparisons)
        print(f"\n  📈 Gain moyen vs Mistral: {avg_gain:+.1f}%")
    
    print("\n✅ Traitement terminé!")
