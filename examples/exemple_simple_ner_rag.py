"""
Exemple simple d'utilisation du NER + RAG pour les fiches de défauts

Ce script montre comment:
1. Extraire les entités d'un document OCR
2. Identifier les champs manquants
3. Utiliser le RAG pour compléter le document de manière interactive
"""

import sys
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ner_defaut_documents import extract_entities_from_defaut_document, display_entities
from rag_integration_ner import DefautDocumentRAG


def exemple_extraction_simple():
    """
    Exemple 1: Extraction simple des entités d'un document
    """
    print("\n" + "="*80)
    print("EXEMPLE 1: EXTRACTION SIMPLE")
    print("="*80 + "\n")
    
    # Charger un document OCR
    doc_path = Path(__file__).parent.parent / "data" / "ocr_results" / "2291 - GAEC DE VAULEON - DEFAUT_ocr.txt"
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        ocr_text = f.read()
    
    print(f"📄 Document: {doc_path.name}\n")
    
    # Extraire les entités
    print("🔍 Extraction des entités avec Azure GPT-4o...\n")
    entities = extract_entities_from_defaut_document(ocr_text)
    
    # Afficher les résultats
    display_entities(entities)
    
    return entities


def exemple_dialogue_rag():
    """
    Exemple 2: Dialogue RAG pour compléter un document
    """
    print("\n" + "="*80)
    print("EXEMPLE 2: DIALOGUE RAG")
    print("="*80 + "\n")
    
    # Charger le document
    doc_path = Path(__file__).parent.parent / "data" / "ocr_results" / "2291 - GAEC DE VAULEON - DEFAUT_ocr.txt"
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        ocr_text = f.read()
    
    # Initialiser le RAG
    rag = DefautDocumentRAG(ocr_text)
    
    # Afficher le prompt initial
    print("🤖 Assistant RAG:")
    print("-" * 80)
    print(rag.get_initial_prompt())
    print("-" * 80)
    
    # Simuler une conversation
    print("\n💬 Simulation de conversation:\n")
    
    # Message 1
    user_msg_1 = "Le numéro d'AO est AO-2022-0456"
    print(f"👤 Utilisateur: {user_msg_1}\n")
    
    response_1 = rag.chat(user_msg_1)
    print(f"🤖 Assistant: {response_1}\n")
    print("-" * 80 + "\n")
    
    # Message 2
    user_msg_2 = "Oui, le document est signé"
    print(f"👤 Utilisateur: {user_msg_2}\n")
    
    response_2 = rag.chat(user_msg_2)
    print(f"🤖 Assistant: {response_2}\n")
    print("-" * 80 + "\n")
    
    # Export des données
    output_path = Path(__file__).parent / "resultat_complete.json"
    rag.export_completed_data(str(output_path))
    
    return rag


def exemple_statistiques(entities):
    """
    Exemple 3: Calcul de statistiques sur le document
    """
    print("\n" + "="*80)
    print("EXEMPLE 3: STATISTIQUES")
    print("="*80 + "\n")
    
    # Statistiques Mise en Service
    mes = entities.get('mise_en_service', {})
    champs_remplis_mes = sum(1 for v in mes.values() if v)
    total_mes = len(mes)
    taux_mes = (champs_remplis_mes / total_mes * 100) if total_mes > 0 else 0
    
    print(f"📊 Mise en Service:")
    print(f"   - Champs remplis: {champs_remplis_mes}/{total_mes} ({taux_mes:.1f}%)")
    
    # Statistiques Tableau
    tableau = entities.get('tableau_defauts', [])
    lignes_avec_anomalie = sum(1 for item in tableau if item.get('anomalies') and item.get('anomalies').upper() != 'NULL')
    lignes_ras = sum(1 for item in tableau if item.get('anomalies', '').upper() == 'R.A.S')
    lignes_avec_temps = sum(1 for item in tableau if item.get('temps_passe'))
    total_lignes = len(tableau)
    
    print(f"\n📋 Tableau des Défauts:")
    print(f"   - Total de lignes: {total_lignes}")
    print(f"   - Avec anomalies: {lignes_avec_anomalie}")
    print(f"   - R.A.S (rien à signaler): {lignes_ras}")
    print(f"   - Avec temps passé: {lignes_avec_temps}")
    
    # Qualité
    qualite = entities.get('qualite_ocr', 'inconnue')
    qualite_emoji = {
        'bonne': '✅',
        'moyenne': '⚠️',
        'mauvaise': '❌',
        'inconnue': '❓'
    }
    
    print(f"\n📈 Qualité OCR: {qualite_emoji.get(qualite, '❓')} {qualite.upper()}")
    
    # Champs manquants
    champs_manquants = entities.get('champs_manquants', [])
    print(f"\n⚠️  Champs manquants: {len(champs_manquants)}")
    
    if champs_manquants:
        for i, champ in enumerate(champs_manquants, 1):
            print(f"   {i}. {champ}")


def exemple_batch_processing():
    """
    Exemple 4: Traitement batch de plusieurs documents
    """
    print("\n" + "="*80)
    print("EXEMPLE 4: TRAITEMENT BATCH")
    print("="*80 + "\n")
    
    from ner_defaut_documents import batch_process_ocr_results
    
    ocr_dir = Path(__file__).parent.parent / "data" / "ocr_results"
    output_dir = Path(__file__).parent.parent / "data" / "ner_results"
    
    print(f"📂 Répertoire source: {ocr_dir}")
    print(f"📁 Répertoire destination: {output_dir}\n")
    
    # Lancer le traitement batch
    batch_process_ocr_results(str(ocr_dir), str(output_dir))


def main():
    """
    Fonction principale avec menu
    """
    print("\n" + "="*80)
    print("🚀 EXEMPLES NER + RAG - FICHES DE DÉFAUTS")
    print("="*80)
    
    print("\nChoisissez un exemple:\n")
    print("1. Extraction simple d'entités")
    print("2. Dialogue RAG interactif")
    print("3. Statistiques et analyse")
    print("4. Traitement batch")
    print("5. Tout exécuter")
    print("q. Quitter\n")
    
    choix = input("Votre choix: ").strip()
    
    if choix == '1':
        exemple_extraction_simple()
    
    elif choix == '2':
        exemple_dialogue_rag()
    
    elif choix == '3':
        entities = exemple_extraction_simple()
        exemple_statistiques(entities)
    
    elif choix == '4':
        exemple_batch_processing()
    
    elif choix == '5':
        print("\n🎯 Exécution de tous les exemples...\n")
        entities = exemple_extraction_simple()
        exemple_statistiques(entities)
        exemple_dialogue_rag()
        
        print("\n💡 Note: Le traitement batch n'est pas exécuté automatiquement.")
        print("   Lancez-le manuellement avec l'option 4 si nécessaire.")
    
    elif choix.lower() == 'q':
        print("\n👋 Au revoir !")
        return
    
    else:
        print("\n❌ Choix invalide. Veuillez réessayer.")
        main()
    
    print("\n" + "="*80)
    print("✅ Exemple terminé !")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interruption utilisateur. Au revoir !")
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()


