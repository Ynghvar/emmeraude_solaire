"""
Script pour effectuer l'OCR sur les fichiers PDF du dossier data
en utilisant Azure mistral-document-ai-2505
"""
import os
import sys
from pathlib import Path
import json
import base64
from datetime import datetime

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

# Vérification des variables d'environnement pour Azure Mistral Document AI
AZURE_MISTRAL_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_MISTRAL_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
MISTRAL_OCR_URL=os.getenv("MISTRAL_OCR_URL")

if not AZURE_MISTRAL_API_KEY:
    raise ValueError("AZURE_MISTRAL_API_KEY n'est pas définie dans les variables d'environnement")
if not AZURE_MISTRAL_ENDPOINT:
    raise ValueError("AZURE_MISTRAL_ENDPOINT n'est pas définie dans les variables d'environnement")

# Nettoyer l'endpoint (enlever le slash final si présent)
AZURE_MISTRAL_ENDPOINT = AZURE_MISTRAL_ENDPOINT.rstrip('/')

def extract_text_from_pdf_azure_mistral(pdf_path):
    """
    Extrait le texte d'un PDF en utilisant Azure mistral-document-ai-2505
    
    Args:
        pdf_path: Chemin vers le fichier PDF
        
    Returns:
        dict: Dictionnaire avec les résultats de l'extraction
    """
    results = {
        "file": str(pdf_path),
        "total_pages": 0,
        "pages_with_ocr": 0,
        "text_by_page": [],
        "full_text": ""
    }
    
    try:
        # Lire le fichier PDF et l'encoder en base64
        with open(pdf_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        # Préparer la requête pour l'API Azure Mistral Document AI
        # L'endpoint peut être directement l'endpoint d'inférence ou nécessiter /inference
        if "/inference" not in AZURE_MISTRAL_ENDPOINT:
            api_url = f"{MISTRAL_OCR_URL}"
        else:
            api_url = MISTRAL_OCR_URL
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AZURE_MISTRAL_API_KEY}"
        }
        
        # Construire le payload pour l'API
        # Format: document_url avec data URI base64
        payload = {
            "model": "mistral-document-ai-2505",
            "document": {
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{pdf_base64}"
            },
            "include_image_base64": True  # Pas besoin des images en base64 pour l'OCR texte
        }
        print(api_url)
        print(f"  📤 Envoi du PDF à l'API Azure Mistral Document AI...")
        
        # Faire l'appel API
        response = requests.post(api_url, headers=headers, json=payload, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            
            # Extraire le texte de la réponse
            # Le format de réponse de l'API Mistral Document AI peut varier
            # On essaie différents formats possibles
            
            # Format 1: Réponse avec "pages"
            if "pages" in result:
                results["total_pages"] = len(result["pages"])
                for page_data in result["pages"]:
                    page_num = page_data.get("index", len(results["text_by_page"])) + 1
                    page_text = page_data.get("markdown", page_data.get("text", ""))
                    if not page_text:
                        page_text = page_data.get("content", "")
                    results["text_by_page"].append({
                        "page": page_num,
                        "text": page_text,
                        "ocr_used": True
                    })
                    results["pages_with_ocr"] += 1
                results["full_text"] = "\n\n".join([
                    f"--- Page {p['page']} ---\n{p['text']}" 
                    for p in results["text_by_page"]
                ])
            # Format 2: Réponse avec "choices" (format chat completions)
            elif "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                if not content:
                    content = result.get("text", "")
                
                # Essayer de parser si c'est du JSON
                if isinstance(content, str):
                    try:
                        parsed = json.loads(content)
                        if "pages" in parsed:
                            results["total_pages"] = len(parsed["pages"])
                            for page_data in parsed["pages"]:
                                page_num = page_data.get("index", len(results["text_by_page"])) + 1
                                page_text = page_data.get("markdown", page_data.get("text", ""))
                                results["text_by_page"].append({
                                    "page": page_num,
                                    "text": page_text,
                                    "ocr_used": True
                                })
                                results["pages_with_ocr"] += 1
                            results["full_text"] = "\n\n".join([
                                f"--- Page {p['page']} ---\n{p['text']}" 
                                for p in results["text_by_page"]
                            ])
                        else:
                            # JSON mais pas de pages, traiter comme texte unique
                            results["total_pages"] = 1
                            results["text_by_page"].append({
                                "page": 1,
                                "text": content,
                                "ocr_used": True
                            })
                            results["pages_with_ocr"] = 1
                            results["full_text"] = content
                    except json.JSONDecodeError:
                        # Ce n'est pas du JSON, c'est du texte brut
                        results["total_pages"] = 1
                        results["text_by_page"].append({
                            "page": 1,
                            "text": content,
                            "ocr_used": True
                        })
                        results["pages_with_ocr"] = 1
                        results["full_text"] = content
                else:
                    results["full_text"] = str(content)
                    results["total_pages"] = 1
                    results["text_by_page"].append({
                        "page": 1,
                        "text": str(content),
                        "ocr_used": True
                    })
                    results["pages_with_ocr"] = 1
            # Format 3: Réponse directe avec "text" ou "content"
            elif "text" in result:
                results["full_text"] = result["text"]
                results["total_pages"] = 1
                results["text_by_page"].append({
                    "page": 1,
                    "text": result["text"],
                    "ocr_used": True
                })
                results["pages_with_ocr"] = 1
            elif "content" in result:
                results["full_text"] = result["content"]
                results["total_pages"] = 1
                results["text_by_page"].append({
                    "page": 1,
                    "text": result["content"],
                    "ocr_used": True
                })
                results["pages_with_ocr"] = 1
            else:
                # Format inconnu, sauvegarder la réponse brute pour debug
                results["error"] = f"Format de réponse inattendu: {json.dumps(result, indent=2)[:500]}"
                print(f"  ⚠️  Format de réponse inattendu, réponse brute sauvegardée")
                results["raw_response"] = result
        else:
            error_msg = f"Erreur API: {response.status_code}"
            if response.text:
                error_msg += f" - {response.text}"
            results["error"] = error_msg
            print(f"  ❌ {error_msg}")
            
    except requests.exceptions.Timeout:
        results["error"] = "Timeout lors de l'appel à l'API (délai dépassé)"
        print(f"  ❌ Timeout lors de l'appel à l'API")
    except Exception as e:
        results["error"] = f"Erreur lors du traitement: {str(e)}"
        print(f"  ❌ Erreur avec {pdf_path}: {str(e)}")
    
    return results

def process_all_pdfs(data_dir="data", output_dir="data/ocr_results"):
    """
    Traite tous les fichiers PDF du dossier data
    
    Args:
        data_dir: Dossier contenant les PDFs
        output_dir: Dossier pour sauvegarder les résultats
    """
    # Créer le dossier de sortie
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Trouver tous les PDFs
    data_path = Path(data_dir)
    pdf_files = list(data_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ Aucun fichier PDF trouvé dans {data_dir}")
        return
    
    print(f"📄 {len(pdf_files)} fichier(s) PDF trouvé(s)\n")
    
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "total_files": len(pdf_files),
        "files": []
    }
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Traitement de: {pdf_path.name}")
        
        results = extract_text_from_pdf_azure_mistral(pdf_path)
        all_results["files"].append(results)
        
        # Sauvegarder le texte complet dans un fichier .txt
        output_txt = Path(output_dir) / f"{pdf_path.stem}_ocr.txt"
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(results["full_text"])
        
        print(f"  ✓ {results['total_pages']} page(s)")
        print(f"  ✓ {results['pages_with_ocr']} page(s) traitées par OCR")
        print(f"  ✓ Résultat sauvegardé: {output_txt}\n")
    
    # Sauvegarder le résumé JSON
    output_json = Path(output_dir) / "ocr_summary.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"📊 Résumé sauvegardé: {output_json}")
    print(f"\n✅ Traitement terminé!")

if __name__ == "__main__":
    print("\n🔍 OCR avec Azure mistral-document-ai-2505")
    print(f"   Endpoint: {AZURE_MISTRAL_ENDPOINT}")
    print()
    
    process_all_pdfs()
