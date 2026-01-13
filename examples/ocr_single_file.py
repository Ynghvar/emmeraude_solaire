"""
Script pour effectuer l'OCR sur un seul fichier PDF spécifique
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
MISTRAL_OCR_URL = os.getenv("MISTRAL_OCR_URL")

if not AZURE_MISTRAL_API_KEY:
    raise ValueError("AZURE_MISTRAL_API_KEY n'est pas définie dans les variables d'environnement")
if not AZURE_MISTRAL_ENDPOINT:
    raise ValueError("AZURE_MISTRAL_ENDPOINT n'est pas définie dans les variables d'environnement")

# Nettoyer l'endpoint
AZURE_MISTRAL_ENDPOINT = AZURE_MISTRAL_ENDPOINT.rstrip('/')

def extract_text_from_pdf_azure_mistral(pdf_path):
    """
    Extrait le texte d'un PDF en utilisant Azure mistral-document-ai-2505
    """
    results = {
        "file": str(pdf_path),
        "total_pages": 0,
        "pages_with_ocr": 0,
        "text_by_page": [],
        "full_text": ""
    }
    
    try:
        print(f"\n📄 Lecture du fichier: {pdf_path}")
        # Lire le fichier PDF et l'encoder en base64
        with open(pdf_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        print(f"  ✓ Taille du fichier: {len(pdf_content)} bytes")
        print(f"  ✓ Taille base64: {len(pdf_base64)} caractères")
        
        # Préparer la requête pour l'API Azure Mistral Document AI
        if "/inference" not in AZURE_MISTRAL_ENDPOINT:
            api_url = f"{MISTRAL_OCR_URL}"
        else:
            api_url = MISTRAL_OCR_URL
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AZURE_MISTRAL_API_KEY}"
        }
        
        payload = {
            "model": "mistral-document-ai-2505",
            "document": {
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{pdf_base64}"
            },
            "include_image_base64": True
        }
        
        print(f"\n  📤 Envoi de la requête à: {api_url}")
        print(f"  ⏳ Timeout: 300 secondes")
        
        # Faire l'appel API avec un timeout plus long
        response = requests.post(api_url, headers=headers, json=payload, timeout=300)
        
        print(f"\n  📥 Réponse reçue - Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Debug: afficher la structure de la réponse
            print(f"  🔍 Clés de la réponse: {list(result.keys())}")
            
            # Format 1: Réponse avec "pages"
            if "pages" in result:
                print(f"  ✓ Format détecté: pages")
                results["total_pages"] = len(result["pages"])
                print(f"  ✓ Nombre de pages: {results['total_pages']}")
                
                for i, page_data in enumerate(result["pages"], 1):
                    page_num = page_data.get("index", i)
                    page_text = page_data.get("markdown", page_data.get("text", ""))
                    if not page_text:
                        page_text = page_data.get("content", "")
                    
                    print(f"    Page {page_num}: {len(page_text)} caractères extraits")
                    
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
            # Format 2: Réponse avec "choices"
            elif "choices" in result and len(result["choices"]) > 0:
                print(f"  ✓ Format détecté: choices")
                content = result["choices"][0].get("message", {}).get("content", "")
                if not content:
                    content = result.get("text", "")
                
                print(f"  ✓ Contenu extrait: {len(content)} caractères")
                
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
                            results["total_pages"] = 1
                            results["text_by_page"].append({
                                "page": 1,
                                "text": content,
                                "ocr_used": True
                            })
                            results["pages_with_ocr"] = 1
                            results["full_text"] = content
                    except json.JSONDecodeError:
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
            # Format 3: Autres formats
            elif "text" in result:
                print(f"  ✓ Format détecté: text")
                results["full_text"] = result["text"]
                results["total_pages"] = 1
                results["text_by_page"].append({
                    "page": 1,
                    "text": result["text"],
                    "ocr_used": True
                })
                results["pages_with_ocr"] = 1
            elif "content" in result:
                print(f"  ✓ Format détecté: content")
                results["full_text"] = result["content"]
                results["total_pages"] = 1
                results["text_by_page"].append({
                    "page": 1,
                    "text": result["content"],
                    "ocr_used": True
                })
                results["pages_with_ocr"] = 1
            else:
                print(f"  ⚠️  Format de réponse inattendu")
                results["error"] = f"Format de réponse inattendu"
                results["raw_response"] = result
                # Sauvegarder la réponse brute pour debug
                with open("debug_response.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"  💾 Réponse brute sauvegardée dans debug_response.json")
        else:
            error_msg = f"Erreur API: {response.status_code}"
            if response.text:
                error_msg += f" - {response.text[:500]}"
            results["error"] = error_msg
            print(f"  ❌ {error_msg}")
            
    except requests.exceptions.Timeout:
        results["error"] = "Timeout lors de l'appel à l'API (délai dépassé)"
        print(f"  ❌ Timeout lors de l'appel à l'API")
    except Exception as e:
        results["error"] = f"Erreur lors du traitement: {str(e)}"
        print(f"  ❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return results

if __name__ == "__main__":
    print("\n🔍 OCR avec Azure mistral-document-ai-2505")
    print(f"   Endpoint: {AZURE_MISTRAL_ENDPOINT}")
    print(f"   OCR URL: {MISTRAL_OCR_URL}")
    
    # Traiter le fichier spécifique
    pdf_path = Path("data/POCHCETTE ELECTRICIENS.pdf")
    
    if not pdf_path.exists():
        print(f"\n❌ Fichier non trouvé: {pdf_path}")
        sys.exit(1)
    
    print(f"\n📄 Traitement de: {pdf_path.name}")
    
    results = extract_text_from_pdf_azure_mistral(pdf_path)
    
    # Sauvegarder le texte complet
    output_dir = Path("data/ocr_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_txt = output_dir / f"{pdf_path.stem}_ocr.txt"
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(results["full_text"])
    
    print(f"\n✅ Traitement terminé!")
    print(f"  ✓ {results['total_pages']} page(s) détectées")
    print(f"  ✓ {results['pages_with_ocr']} page(s) traitées par OCR")
    print(f"  ✓ {len(results['full_text'])} caractères extraits")
    print(f"  💾 Résultat sauvegardé: {output_txt}")
    
    if "error" in results:
        print(f"\n⚠️  Erreur: {results['error']}")
