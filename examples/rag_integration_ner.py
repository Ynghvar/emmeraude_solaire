"""
Intégration du NER avec le système RAG pour la complétion interactive des fiches de défauts
"""

import json
from pathlib import Path
from typing import Dict, List
from ner_defaut_documents import extract_entities_from_defaut_document, generate_rag_completion_prompt
from utils.LLM import get_chat_response


class DefautDocumentRAG:
    """
    Classe pour gérer l'interaction RAG avec les fiches de défauts.
    Utilise le NER pour identifier les champs manquants et guide l'utilisateur.
    """
    
    def __init__(self, ocr_text: str):
        """
        Initialise le RAG avec un document OCR.
        
        Args:
            ocr_text: Le texte OCR de la fiche de défauts
        """
        self.ocr_text = ocr_text
        self.entities = extract_entities_from_defaut_document(ocr_text)
        self.champs_manquants = self.entities.get("champs_manquants", [])
        self.conversation_history = []
        
    def get_system_prompt(self) -> str:
        """
        Génère le prompt système pour le RAG basé sur les entités extraites.
        """
        return f"""Tu es un assistant intelligent spécialisé dans l'aide à la complétion de fiches de défauts pour des installations solaires.

Tu as accès à une fiche de défauts partiellement remplie avec les informations suivantes:

**MISE EN SERVICE:**
{json.dumps(self.entities.get('mise_en_service', {}), indent=2, ensure_ascii=False)}

**TABLEAU DES DÉFAUTS:**
{json.dumps(self.entities.get('tableau_defauts', []), indent=2, ensure_ascii=False)}

**CHAMPS MANQUANTS:** {len(self.champs_manquants)} champs
{json.dumps(self.champs_manquants, indent=2, ensure_ascii=False)}

**QUALITÉ OCR:** {self.entities.get('qualite_ocr', 'inconnue')}

Ton rôle est de:
1. Identifier ce qui manque dans la fiche
2. Poser des questions claires et précises pour obtenir les informations manquantes
3. Reformuler les informations fournies pour validation
4. Aider à comprendre les erreurs ou anomalies détectées
5. Suggérer des valeurs standard quand c'est pertinent (ex: "R.A.S" pour aucune anomalie)

Sois professionnel, concis et bienveillant. Pose une question à la fois pour ne pas submerger l'utilisateur.
"""
    
    def get_initial_prompt(self) -> str:
        """
        Génère le prompt initial pour démarrer la conversation.
        """
        if not self.champs_manquants:
            return """✅ **Fiche de défauts complète !**

Toutes les informations nécessaires ont été extraites du document. 
Y a-t-il quelque chose que vous souhaitez modifier ou vérifier ?"""
        
        # Compter les catégories de champs manquants
        mes_fields = sum(1 for c in self.champs_manquants 
                         if any(x in c.lower() for x in ["chantier", "technicien", "date", "ao", "signature"]))
        defaut_fields = len(self.champs_manquants) - mes_fields
        
        prompt = f"""📋 **Analyse de la fiche de défauts**

J'ai analysé votre document et extrait les informations disponibles.

**État de la fiche:**
- ✅ Informations présentes: {sum(1 for v in self.entities.get('mise_en_service', {}).values() if v)}
- ⚠️  Informations manquantes: {len(self.champs_manquants)} champs

**Sections incomplètes:**
"""
        
        if mes_fields > 0:
            prompt += f"- 🔧 Mise en service: {mes_fields} champ(s) manquant(s)\n"
        if defaut_fields > 0:
            prompt += f"- 📋 Tableau des défauts: {defaut_fields} champ(s) manquant(s)\n"
        
        # Identifier le premier champ manquant le plus important
        premier_champ = self.champs_manquants[0] if self.champs_manquants else None
        
        if premier_champ:
            if "ao" in premier_champ.lower():
                prompt += f"\n**Commençons par le numéro d'Appel d'Offres (AO):**\nQuel est le numéro d'AO pour ce chantier ?"
            elif "signature" in premier_champ.lower():
                prompt += f"\n**La signature du technicien:**\nLe document a-t-il été signé par le technicien ? (Oui/Non)"
            elif "temps" in premier_champ.lower():
                localisation = premier_champ.replace("temps passé pour ", "")
                prompt += f"\n**Temps passé - {localisation}:**\nCombien de temps a été passé sur cette section ? (ex: 15 min, 1h, R.A.S si non applicable)"
            else:
                prompt += f"\n**Première information manquante:**\nPouvez-vous fournir: {premier_champ} ?"
        
        return prompt
    
    def chat(self, user_message: str) -> str:
        """
        Traite un message utilisateur et retourne la réponse du RAG.
        
        Args:
            user_message: Le message de l'utilisateur
            
        Returns:
            La réponse du système RAG
        """
        # Ajouter le contexte système au premier message
        if not self.conversation_history:
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "assistant", "content": self.get_initial_prompt()},
                {"role": "user", "content": user_message}
            ]
        else:
            messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ] + self.conversation_history + [
                {"role": "user", "content": user_message}
            ]
        
        # Obtenir la réponse du LLM
        response = get_chat_response(messages)
        
        # Sauvegarder dans l'historique
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def update_entity(self, field_path: str, value: str):
        """
        Met à jour une entité dans la structure.
        
        Args:
            field_path: Chemin vers le champ (ex: "mise_en_service.ao")
            value: Nouvelle valeur
        """
        parts = field_path.split(".")
        target = self.entities
        
        for part in parts[:-1]:
            target = target[part]
        
        target[parts[-1]] = value
        
        # Retirer des champs manquants si applicable
        if field_path in self.champs_manquants:
            self.champs_manquants.remove(field_path)
    
    def export_completed_data(self, output_path: str):
        """
        Exporte les données complétées vers un fichier JSON.
        
        Args:
            output_path: Chemin vers le fichier de sortie
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "entites": self.entities,
                "champs_restants": self.champs_manquants,
                "conversation": self.conversation_history
            }, f, indent=2, ensure_ascii=False)
        print(f"✅ Données exportées vers: {output_path}")


def demo_interactive():
    """
    Démonstration interactive du système RAG avec NER.
    """
    # Lire le document exemple
    doc_path = Path(__file__).parent.parent / "data" / "ocr_results" / "2291 - GAEC DE VAULEON - DEFAUT_ocr.txt"
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        ocr_text = f.read()
    
    # Initialiser le RAG
    rag = DefautDocumentRAG(ocr_text)
    
    print("="*80)
    print("🤖 ASSISTANT RAG - COMPLÉTION DE FICHE DE DÉFAUTS")
    print("="*80)
    print("\nTapez 'quit' pour quitter, 'export' pour exporter les données\n")
    
    # Afficher le prompt initial
    print(f"\n🤖 Assistant:\n{rag.get_initial_prompt()}\n")
    
    while True:
        user_input = input("👤 Vous: ").strip()
        
        if user_input.lower() == 'quit':
            print("\n👋 Au revoir !")
            break
        
        if user_input.lower() == 'export':
            output_path = "data/ner_results/completed_defaut.json"
            rag.export_completed_data(output_path)
            continue
        
        if not user_input:
            continue
        
        response = rag.chat(user_input)
        print(f"\n🤖 Assistant:\n{response}\n")


def process_document_with_rag_suggestions(file_path: str) -> Dict:
    """
    Traite un document et retourne les suggestions RAG pour le compléter.
    
    Args:
        file_path: Chemin vers le fichier OCR
        
    Returns:
        Dict avec les entités et les suggestions de questions
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        ocr_text = f.read()
    
    # Extraire les entités
    entities = extract_entities_from_defaut_document(ocr_text)
    
    # Générer les suggestions de questions pour le RAG
    rag_suggestions = {
        "questions_a_poser": [],
        "validations_necessaires": [],
        "corrections_ocr": []
    }
    
    # Questions basées sur les champs manquants
    champs_manquants = entities.get("champs_manquants", [])
    
    for champ in champs_manquants:
        if "ao" in champ.lower():
            rag_suggestions["questions_a_poser"].append({
                "champ": champ,
                "question": "Quel est le numéro d'Appel d'Offres (AO) pour ce chantier ?",
                "type": "text"
            })
        elif "signature" in champ.lower():
            rag_suggestions["questions_a_poser"].append({
                "champ": champ,
                "question": "Le document a-t-il été signé par le technicien ?",
                "type": "boolean"
            })
        elif "temps" in champ.lower():
            section = champ.replace("temps passé pour ", "")
            rag_suggestions["questions_a_poser"].append({
                "champ": champ,
                "question": f"Combien de temps a été passé sur la section '{section}' ?",
                "type": "duration",
                "suggestions": ["R.A.S", "15 min", "30 min", "1h"]
            })
    
    # Validations pour les champs avec données
    mes = entities.get("mise_en_service", {})
    if mes.get("nom_chantier") and len(mes.get("nom_chantier", "")) < 5:
        rag_suggestions["validations_necessaires"].append({
            "champ": "nom_chantier",
            "valeur": mes.get("nom_chantier"),
            "raison": "Nom de chantier très court, vérifier l'exactitude"
        })
    
    # Qualité OCR
    if entities.get("qualite_ocr") in ["moyenne", "mauvaise"]:
        rag_suggestions["corrections_ocr"].append({
            "message": "La qualité OCR est moyenne. Vérifier manuellement les valeurs extraites.",
            "priorite": "haute"
        })
    
    return {
        "entites": entities,
        "rag_suggestions": rag_suggestions,
        "prompt_completion": generate_rag_completion_prompt(entities)
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Mode interactif
        demo_interactive()
    else:
        # Mode analyse simple
        print("🚀 Mode analyse avec suggestions RAG\n")
        
        doc_path = Path(__file__).parent.parent / "data" / "ocr_results" / "2291 - GAEC DE VAULEON - DEFAUT_ocr.txt"
        
        result = process_document_with_rag_suggestions(str(doc_path))
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print("\n\n💡 Pour lancer le mode interactif:")
        print("   python src/rag_integration_ner.py --interactive")
