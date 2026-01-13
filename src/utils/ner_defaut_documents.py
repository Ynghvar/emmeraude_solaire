"""
Module de NER (Named Entity Recognition) hybride pour les fiches de défauts
Utilise un LLM (Azure GPT-4o) pour extraire et structurer les informations
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# Configuration Azure OpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)


def extract_entities_from_defaut_document(text: str, model: str = "gpt-4o") -> Dict:
    """
    Extrait les entités nommées d'une fiche de défauts en utilisant un LLM.
    
    Args:
        text: Le texte OCR de la fiche de défauts
        model: Le modèle Azure à utiliser (par défaut: gpt-4o)
    
    Returns:
        Dict contenant toutes les entités extraites et structurées
    """
    
    prompt = f"""Tu es un expert en extraction d'informations structurées.
Analyse ce document OCR d'une fiche de défauts de mise en service et extrait toutes les informations.

Le document contient:
1. Une section "Mise en service" avec:
   - Nom Chantier
   - AO (Appel d'Offres)
   - N° Chantier
   - Nom Technicien
   - Date
   - Signature Technicien

2. Un tableau de défauts avec:
   - En-têtes: "Localisation du problème", "Anomalies rencontrées", "Temps passé"
   - Lignes pour: "Partie DC", "Partie AC", "Partie Communication", "Liaison Equipotentielle; Mesure de terre", "Divers; Remarques"

Voici le document OCR:

{text}

Retourne un JSON structuré avec EXACTEMENT ce format:

{{
  "mise_en_service": {{
    "nom_chantier": "valeur extraite ou null",
    "ao": "valeur extraite ou null",
    "num_chantier": "valeur extraite ou null",
    "nom_technicien": "valeur extraite ou null",
    "date": "valeur extraite ou null",
    "signature": "présente/absente/null"
  }},
  "tableau_defauts": [
    {{
      "localisation": "Partie DC",
      "anomalies": "texte ou R.A.S ou null",
      "temps_passe": "durée ou null"
    }},
    {{
      "localisation": "Partie AC",
      "anomalies": "texte ou R.A.S ou null",
      "temps_passe": "durée ou null"
    }},
    {{
      "localisation": "Partie Communication",
      "anomalies": "texte ou R.A.S ou null",
      "temps_passe": "durée ou null"
    }},
    {{
      "localisation": "Liaison Equipotentielle / Mesure de terre",
      "anomalies": "texte ou R.A.S ou null",
      "temps_passe": "durée ou null"
    }},
    {{
      "localisation": "Divers / Remarques",
      "anomalies": "texte ou R.A.S ou null",
      "temps_passe": "durée ou null"
    }}
  ],
  "champs_manquants": ["liste des champs vides qui devraient être remplis"],
  "qualite_ocr": "bonne/moyenne/mauvaise (selon les erreurs détectées)"
}}

Règles importantes:
- Si une information n'est pas trouvée, mets null
- "R.A.S" signifie "Rien à Signaler" (pas d'anomalie)
- Corrige les erreurs d'OCR évidentes (ex: "AQO" -> "AO", "mon démuchés" -> "non dénudés")
- Liste tous les champs manquants dans "champs_manquants"
- Retourne UNIQUEMENT le JSON, sans texte additionnel
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant expert en extraction d'informations structurées. Tu réponds toujours en JSON valide."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Faible température pour des résultats plus déterministes
            response_format={"type": "json_object"}  # Force le retour en JSON
        )
        
        result = response.choices[0].message.content
        return json.loads(result)
        
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction: {str(e)}")
        return {
            "error": str(e),
            "mise_en_service": {},
            "tableau_defauts": [],
            "champs_manquants": [],
            "qualite_ocr": "erreur"
        }


def generate_rag_completion_prompt(entities: Dict) -> str:
    """
    Génère un prompt pour le RAG basé sur les champs manquants.
    
    Args:
        entities: Les entités extraites du document
    
    Returns:
        Un prompt texte à utiliser pour guider la complétion du document
    """
    champs_manquants = entities.get("champs_manquants", [])
    
    if not champs_manquants:
        return "✅ Toutes les informations nécessaires sont présentes dans le document."
    
    prompt = "📋 **Informations manquantes à compléter :**\n\n"
    
    # Catégoriser les champs manquants
    mes_fields = []
    defaut_fields = []
    
    for champ in champs_manquants:
        if any(x in champ.lower() for x in ["chantier", "technicien", "date", "ao", "signature"]):
            mes_fields.append(champ)
        else:
            defaut_fields.append(champ)
    
    if mes_fields:
        prompt += "**Section Mise en Service :**\n"
        for field in mes_fields:
            prompt += f"  - {field}\n"
        prompt += "\n"
    
    if defaut_fields:
        prompt += "**Tableau des défauts :**\n"
        for field in defaut_fields:
            prompt += f"  - {field}\n"
        prompt += "\n"
    
    prompt += "\n💡 **Questions à poser :**\n"
    prompt += "Pour compléter la fiche de défauts, veuillez fournir les informations suivantes :\n"
    
    for i, champ in enumerate(champs_manquants, 1):
        prompt += f"{i}. {champ}\n"
    
    return prompt


def process_defaut_document(file_path: str, output_json: Optional[str] = None) -> Dict:
    """
    Traite un document de fiche de défauts et extrait toutes les entités.
    
    Args:
        file_path: Chemin vers le fichier texte OCR
        output_json: Chemin optionnel pour sauvegarder le résultat en JSON
    
    Returns:
        Dict avec les entités extraites et le prompt de complétion
    """
    print(f"📄 Traitement du document: {file_path}")
    
    # Lire le fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Extraire les entités
    print("🔍 Extraction des entités avec le LLM...")
    entities = extract_entities_from_defaut_document(text)
    
    # Générer le prompt de complétion pour le RAG
    rag_prompt = generate_rag_completion_prompt(entities)
    
    # Ajouter le prompt au résultat
    result = {
        "fichier_source": file_path,
        "entites_extraites": entities,
        "prompt_completion_rag": rag_prompt
    }
    
    # Sauvegarder si demandé
    if output_json:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 Résultat sauvegardé dans: {output_json}")
    
    return result


def display_entities(entities: Dict):
    """
    Affiche les entités extraites de manière lisible.
    """
    print("\n" + "="*80)
    print("📊 RÉSULTATS DE L'EXTRACTION")
    print("="*80)
    
    # Section Mise en Service
    print("\n🔧 **MISE EN SERVICE**")
    mes = entities.get("mise_en_service", {})
    for key, value in mes.items():
        label = key.replace("_", " ").title()
        status = "✅" if value else "❌"
        print(f"  {status} {label}: {value if value else 'NON RENSEIGNÉ'}")
    
    # Tableau des défauts
    print("\n📋 **TABLEAU DES DÉFAUTS**")
    tableau = entities.get("tableau_defauts", [])
    for item in tableau:
        loc = item.get("localisation", "?")
        anom = item.get("anomalies", "?")
        temps = item.get("temps_passe", "-")
        
        status = "✅" if anom and anom.upper() != "NULL" else "❌"
        print(f"\n  {status} {loc}:")
        print(f"      Anomalies: {anom}")
        print(f"      Temps: {temps}")
    
    # Qualité et champs manquants
    print(f"\n📈 **QUALITÉ OCR**: {entities.get('qualite_ocr', 'inconnue').upper()}")
    
    champs_manquants = entities.get("champs_manquants", [])
    if champs_manquants:
        print(f"\n⚠️  **{len(champs_manquants)} CHAMPS MANQUANTS**:")
        for champ in champs_manquants:
            print(f"    - {champ}")
    else:
        print("\n✅ **AUCUN CHAMP MANQUANT**")
    
    print("\n" + "="*80)


def batch_process_ocr_results(ocr_dir: str, output_dir: str):
    """
    Traite tous les fichiers OCR d'un répertoire.
    
    Args:
        ocr_dir: Répertoire contenant les fichiers OCR .txt
        output_dir: Répertoire pour sauvegarder les résultats JSON
    """
    ocr_path = Path(ocr_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Trouver tous les fichiers _ocr.txt qui contiennent "DEFAUT" dans leur nom
    ocr_files = list(ocr_path.glob("*DEFAUT*_ocr.txt"))
    
    print(f"📂 Trouvé {len(ocr_files)} fichiers de défauts à traiter\n")
    
    results = []
    for ocr_file in ocr_files:
        output_json = output_path / f"{ocr_file.stem}_entities.json"
        
        try:
            result = process_defaut_document(str(ocr_file), str(output_json))
            results.append(result)
            
            # Afficher les résultats
            display_entities(result["entites_extraites"])
            print(f"\n{result['prompt_completion_rag']}\n")
            
        except Exception as e:
            print(f"❌ Erreur avec {ocr_file.name}: {str(e)}\n")
    
    # Créer un résumé global
    summary = {
        "total_fichiers": len(ocr_files),
        "fichiers_traites": len(results),
        "resultats": results
    }
    
    summary_path = output_path / "ner_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Résumé global sauvegardé dans: {summary_path}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Mode fichier unique
        file_path = sys.argv[1]
        output_json = sys.argv[2] if len(sys.argv) > 2 else None
        
        result = process_defaut_document(file_path, output_json)
        display_entities(result["entites_extraites"])
        print(f"\n{result['prompt_completion_rag']}")
        
    else:
        # Mode batch sur tous les fichiers de défauts
        print("🚀 Mode batch: traitement de tous les fichiers de défauts\n")
        
        # Déterminer les chemins
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        ocr_dir = project_root / "data" / "ocr_results"
        output_dir = project_root / "data" / "ner_results"
        
        batch_process_ocr_results(str(ocr_dir), str(output_dir))
