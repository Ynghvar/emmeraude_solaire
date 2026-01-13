"""
Module de gestion des fiches dans le chatbot Streamlit
Intègre le NER + RAG pour compléter les fiches via conversation
Support de plusieurs types de fiches
"""

import json
from typing import Dict, Optional, List
from pathlib import Path
import sys

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.ner_defaut_documents import extract_entities_from_defaut_document
from utils.fiche_types import (
    FicheType, 
    get_available_fiches, 
    get_fiche_structure,
    create_empty_fiche,
    format_fiche_type_list
)


class FicheDefautChatManager:
    """
    Gestionnaire de fiches pour intégration chatbot.
    Support de plusieurs types de fiches.
    Maintient l'état de la fiche et génère le contexte pour le LLM.
    """
    
    def __init__(self, ocr_text: Optional[str] = None, fiche_type: Optional[FicheType] = None):
        """
        Initialise le gestionnaire avec un texte OCR optionnel ou un type de fiche.
        
        Args:
            ocr_text: Texte OCR d'une fiche existante (optionnel)
            fiche_type: Type de fiche à créer (optionnel, si None demande à l'utilisateur)
        """
        self.fiche_type = fiche_type
        self.mode = "selection" if not fiche_type else "creation"
        
        if ocr_text:
            # Charger depuis OCR (pour l'instant, on suppose que c'est une fiche de défauts)
            self.entities = extract_entities_from_defaut_document(ocr_text)
            self.mode = "completion"
            self.fiche_type = FicheType.DEFAUTS
        elif fiche_type:
            # Créer une nouvelle fiche du type spécifié
            self.entities = create_empty_fiche(fiche_type)
            self.mode = "creation"
        else:
            # Mode sélection : l'utilisateur doit choisir le type
            self.entities = {}
            self.mode = "selection"
        
        self.champs_manquants = self.entities.get("champs_manquants", []) if self.entities else []
        self.conversation_updates = []  # Historique des mises à jour
    
    def set_fiche_type(self, fiche_type: FicheType):
        """
        Définit le type de fiche et initialise la structure.
        
        Args:
            fiche_type: Type de fiche choisi
        """
        self.fiche_type = fiche_type
        self.entities = create_empty_fiche(fiche_type)
        self.mode = "creation"
        self._update_champs_manquants()
    
    def _is_field_empty(self, value) -> bool:
        """
        Détermine si un champ est vraiment vide.
        Un champ est considéré comme REMPLI même s'il contient "RAS", "Non renseigné", "0 min", etc.
        """
        if value is None:
            return True
        if value == "":
            return True
        if value == "null":
            return True
        # Tout le reste est considéré comme rempli (y compris "RAS", "Non renseigné", etc.)
        return False
    
    def _update_champs_manquants(self):
        """Met à jour la liste des champs manquants selon le type de fiche"""
        if not self.fiche_type or not self.entities:
            self.champs_manquants = []
            return
        
        manquants = []
        structure = get_fiche_structure(self.fiche_type)
        
        if self.fiche_type == FicheType.DEFAUTS:
            # Logique spécifique pour les fiches de défauts
            mes = self.entities.get("mise_en_service", {})
            for key, value in mes.items():
                if self._is_field_empty(value):
                    manquants.append(key)
            
            tableau = self.entities.get("tableau_defauts", [])
            for ligne in tableau:
                loc = ligne.get("localisation", "")
                if self._is_field_empty(ligne.get("anomalies")):
                    manquants.append(f"{loc} - anomalies")
                if self._is_field_empty(ligne.get("temps_passe")):
                    manquants.append(f"{loc} - temps")
        else:
            # Logique générique pour les autres types
            for section_id, section_data in structure["sections"].items():
                if "champs" in section_data:
                    section_entity = self.entities.get(section_id, {})
                    for champ in section_data["champs"]:
                        if champ["obligatoire"] and self._is_field_empty(section_entity.get(champ["id"])):
                            manquants.append(f"{section_data['nom']} - {champ['label']}")
        
        self.champs_manquants = manquants
    
    def _get_section_summary(self) -> str:
        """Génère un résumé de l'état des sections selon le type de fiche"""
        if not self.fiche_type:
            return ""
        
        structure = get_fiche_structure(self.fiche_type)
        summary = []
        
        for section_id, section_data in structure["sections"].items():
            section_name = section_data.get("nom", section_id)
            section_entity = self.entities.get(section_id, {})
            
            if "lignes" in section_data:
                # Section tableau (ex: défauts)
                lignes = self.entities.get(section_id, [])
                for ligne in lignes:
                    loc = ligne.get("localisation", "?")
                    filled_count = sum(1 for champ in section_data["lignes"][0]["champs"] 
                                     if not self._is_field_empty(ligne.get(champ)))
                    total_count = len(section_data["lignes"][0]["champs"])
                    status = "✅" if filled_count == total_count else "⚠️" if filled_count > 0 else "❌"
                    summary.append(f"- {loc}: {status} ({filled_count}/{total_count})")
            elif "champs" in section_data:
                # Section normale
                filled_count = sum(1 for champ in section_data["champs"] 
                                 if not self._is_field_empty(section_entity.get(champ["id"])))
                total_count = len([c for c in section_data["champs"] if c.get("obligatoire", True)])
                status = "✅" if filled_count == total_count else "⚠️" if filled_count > 0 else "❌"
                summary.append(f"**{section_name}:** {status} ({filled_count}/{total_count})")
        
        return "\n".join(summary)
    
    def _get_specific_rules(self) -> str:
        """Retourne des règles spécifiques selon le type de fiche"""
        if self.fiche_type == FicheType.DEFAUTS:
            return """
⚠️ **RÈGLE CRITIQUE POUR LE TABLEAU DES DÉFAUTS:**
- Pour CHAQUE section, tu dois OBLIGATOIREMENT demander DEUX informations :
  1. Les ANOMALIES (ou RAS)
  2. Le TEMPS PASSÉ (ex: "15 min", "1h", ou RAS)
- NE PASSE JAMAIS à la section suivante sans avoir demandé le temps passé !
- Ordre : Anomalies → Temps → Section suivante"""
        
        elif self.fiche_type == FicheType.CONTROLE_MES:
            return """
⚠️ **RÈGLES POUR FICHE DE CONTRÔLE MES:**
- Pour chaque élément de contrôle, demande le statut : OK, NOK ou NA
- Pour les onduleurs, note bien les références et numéros de série
- Pour les mesures (terre, tension, etc.), demande les valeurs précises
- Avance section par section de manière logique"""
        
        elif self.fiche_type == FicheType.ELECTRICIENS:
            return """
⚠️ **RÈGLES POUR FICHE ÉLECTRICIENS:**
- Demande si la réception est sans réserve ou avec réserves
- Si avec réserves, demande la nature des réserves en détail
- Confirme si les mesures de tensions ont été effectuées"""
        
        elif self.fiche_type == FicheType.POSEURS:
            return """
⚠️ **RÈGLES POUR FICHE POSEURS:**
- Demande d'abord les infos du projet (client, chantier, dates)
- Pour la pochette documents, vérifie chaque élément (VALIDE/NA)
- Pour la configuration, demande les détails techniques (puissance, panneaux, onduleurs)
- Termine par la réception des travaux (pose et raccordement)"""
        
        else:
            return ""
    
    def get_system_prompt(self) -> str:
        """
        Génère le prompt système pour le LLM avec le contexte de la fiche.
        """
        # Mode sélection : demander le type de fiche
        if self.mode == "selection":
            fiches_list = format_fiche_type_list()
            return f"""Tu es un assistant spécialisé dans le remplissage de fiches pour installations solaires.

L'utilisateur veut remplir une fiche mais n'a PAS encore précisé le type.

{fiches_list}

**TON RÔLE:**
1. Demander QUEL TYPE de fiche l'utilisateur veut remplir
2. Être concis et clair
3. Proposer les options disponibles

**RÈGLES:**
- Présente les types de fiches de manière claire
- Demande une confirmation claire
- Ne commence PAS à remplir avant d'avoir le type

**EXEMPLE DE RÉPONSE:**

"Quel type de fiche veux-tu remplir ?

1. **Fiche de Défauts** - Pour noter les anomalies
2. **Fiche de Contrôle MES** - Contrôle de mise en service
3. **Fiche Électriciens** - Contrôle travaux électriques
4. **Fiche Poseurs** - Contrôle travaux de pose

Indique le numéro ou le nom de la fiche."
"""
        
        # Mode création ou complétion
        completude = self.get_completion_percentage()
        
        # Récupérer le nom de la fiche de manière sécurisée
        fiche_nom = "Fiche"
        if self.fiche_type:
            fiche_structure = get_fiche_structure(self.fiche_type)
            if fiche_structure:
                fiche_nom = fiche_structure["nom"]
        
        section_summary = self._get_section_summary()
        
        prompt = f"""Tu es un assistant SPÉCIALISÉ dans le remplissage de **{fiche_nom.upper()}** pour installations solaires.

🎯 **IMPORTANT:** Tu dois ABSOLUMENT te concentrer UNIQUEMENT sur le remplissage de cette fiche. Ne parle PAS d'autres sujets.

**MODE:** {self.mode.upper()}
**COMPLÉTUDE:** {completude:.0f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 **ÉTAT DE LA FICHE:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{section_summary}

**CHAMPS ENCORE MANQUANTS:** {len(self.champs_manquants)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 **TON RÔLE PRÉCIS:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **EXTRAIRE** les informations de fiche dans chaque message
2. **CONFIRMER** ce que tu as compris (ex: "J'ai noté: Chantier = X ✅")
3. **DEMANDER** le prochain champ manquant de manière logique
4. **NE JAMAIS** parler d'autre chose que cette fiche
5. **NE JAMAIS** expliquer ce qu'est cette fiche - juste la remplir !

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ **RÈGLES STRICTES:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Pose UNE question à la fois maximum
- Extrais TOUTES les infos mentionnées (même si plusieurs)
- "RAS" ou "pas d'AO" ou "aucun" = valeur null ou "Non renseigné"
- Sois BREF dans tes réponses (2-3 lignes max)
- Confirme ce que tu notes + demande le suivant
- NE crée PAS de templates ou modèles - remplis la vraie fiche !

⚠️ **RÈGLE CRITIQUE POUR LE TABLEAU DES DÉFAUTS:**
- Pour CHAQUE section, tu dois OBLIGATOIREMENT demander DEUX informations :
  1. Les ANOMALIES (ou RAS)
  2. Le TEMPS PASSÉ (ex: "15 min", "1h", ou RAS)
- NE PASSE JAMAIS à la section suivante sans avoir demandé le temps passé !
- Ordre : Anomalies → Temps → Section suivante

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 **EXEMPLES DE BONNES RÉPONSES:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Exemple 1 - Mise en service:**

Utilisateur: "Le chantier s'appelle GAEC de Vauleon et il n'y a pas d'AO"

✅ TOI: "Parfait ! J'ai noté :
- Chantier : GAEC de Vauleon ✅
- AO : Non renseigné ✅

Quel est le numéro de chantier ?"

**Exemple 2 - Tableau des défauts (IMPORTANT):**

Utilisateur: "Pour la Partie DC, RAS"

✅ TOI: "Compris, rien à signaler pour la Partie DC. 
Et combien de temps as-tu passé sur cette partie ?"

Utilisateur: "5 minutes"

✅ TOI: "Noté ! Partie DC complète ✅
Passons à la Partie AC, as-tu rencontré des anomalies ?"

❌ PAS ÇA: "OK pour la Partie DC. Et pour la Partie AC ?" 
   (Tu as OUBLIÉ de demander le temps passé !)

❌ PAS ÇA: "Voici comment structurer votre fiche: [long template]"
❌ PAS ÇA: "Une fiche de défauts est un document qui..."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 **STRATÉGIE D'ACTION:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Identifie ce qui est déjà rempli dans l'état actuel
2. Note ce que l'utilisateur vient de dire
3. Confirme brièvement
4. Demande le PROCHAIN champ manquant
5. Continue jusqu'à 100%

RAPPEL CRITIQUE: Tu remplis une VRAIE fiche, pas un modèle théorique !
"""
        return prompt
    
    def get_completion_percentage(self) -> float:
        """Calcule le pourcentage de complétion de la fiche"""
        if not self.fiche_type:
            return 0
        
        structure = get_fiche_structure(self.fiche_type)
        total_champs = 0
        champs_remplis = 0
        
        for section_id, section_data in structure["sections"].items():
            if "lignes" in section_data:
                # Section tableau
                lignes = self.entities.get(section_id, [])
                for ligne in lignes:
                    for champ in section_data["lignes"][0]["champs"]:
                        total_champs += 1
                        if not self._is_field_empty(ligne.get(champ)):
                            champs_remplis += 1
            elif "champs" in section_data:
                # Section normale - COMPTER TOUS LES CHAMPS (pas seulement obligatoires)
                section_entity = self.entities.get(section_id, {})
                for champ in section_data["champs"]:
                    # Pour la Fiche FC MES et autres: compter tous les champs
                    # Les champs obligatoires seront juste prioritaires dans les questions
                    total_champs += 1
                    if not self._is_field_empty(section_entity.get(champ["id"])):
                        champs_remplis += 1
        
        return (champs_remplis / total_champs * 100) if total_champs > 0 else 0
    
    def get_next_question(self) -> Optional[str]:
        """
        Génère la prochaine question à poser basée sur les champs manquants.
        Retourne None si la fiche est complète.
        """
        if not self.champs_manquants or not self.fiche_type:
            return None
        
        # Pour les fiches de défauts, utiliser la logique spécifique
        if self.fiche_type == FicheType.DEFAUTS:
            return self._get_next_question_defauts()
        
        # Pour les autres types, logique générique
        structure = get_fiche_structure(self.fiche_type)
        
        # Parcourir les sections dans l'ordre
        for section_id, section_data in structure["sections"].items():
            section_name = section_data.get("nom", section_id)
            
            if "champs" in section_data:
                section_entity = self.entities.get(section_id, {})
                for champ in section_data["champs"]:
                    if champ.get("obligatoire", True) and self._is_field_empty(section_entity.get(champ["id"])):
                        # Générer une question appropriée
                        label = champ["label"]
                        if champ["type"] == "boolean":
                            return f"{label} ? (Oui/Non)"
                        elif champ["type"] == "select":
                            options = champ.get("options", [])
                            return f"{label} ? ({'/'.join(options)})"
                        elif champ["type"] == "date":
                            return f"{label} ? (format JJ/MM/AAAA)"
                        else:
                            return f"{label} ?"
        
        return None
    
    def _get_next_question_defauts(self) -> Optional[str]:
        """Logique spécifique pour les fiches de défauts"""
        # Prioriser les champs de mise en service
        mes_fields = {
            "nom_chantier": "Quel est le nom du chantier ?",
            "ao": "Quel est le numéro d'Appel d'Offres (AO) ?",
            "num_chantier": "Quel est le numéro de chantier ?",
            "nom_technicien": "Qui est le technicien intervenant ?",
            "date": "Quelle est la date d'intervention ? (format JJ/MM/AAAA)",
            "signature": "Le document a-t-il été signé ?"
        }
        
        for champ, question in mes_fields.items():
            if champ in self.champs_manquants:
                return question
        
        # Pour le tableau : traiter section par section (anomalies + temps ensemble)
        sections_ordre = [
            "Partie DC",
            "Partie AC", 
            "Partie Communication",
            "Liaison Equipotentielle / Mesure de terre",
            "Divers / Remarques"
        ]
        
        for section in sections_ordre:
            section_anomalies = f"{section} - anomalies"
            section_temps = f"{section} - temps"
            
            if section_anomalies in self.champs_manquants:
                return f"Pour la section '{section}', as-tu rencontré des anomalies ? (RAS si rien à signaler)"
            
            if section_temps in self.champs_manquants:
                return f"Combien de temps as-tu passé sur '{section}' ?"
        
        return None
    
    def _update_from_conversation_generic(self, user_message: str, last_question: str = "") -> List[str]:
        """
        Version générique de l'extraction qui s'adapte au type de fiche.
        Utilisée pour tous les types sauf DEFAUTS.
        """
        from utils.LLM import get_chat_response
        import json
        
        if not self.fiche_type:
            return []
        
        structure = get_fiche_structure(self.fiche_type)
        fiche_nom = structure["nom"]
        
        # Construire le JSON template basé sur la structure réelle
        json_template = {}
        for section_id, section_data in structure["sections"].items():
            if "champs" in section_data:
                json_template[section_id] = {}
                for champ in section_data["champs"]:
                    champ_id = champ["id"]
                    champ_type = champ["type"]
                    
                    if champ_type == "boolean":
                        json_template[section_id][champ_id] = "true/false/null"
                    elif champ_type == "select":
                        options = champ.get("options", [])
                        json_template[section_id][champ_id] = f"'{'/'.join(options)}' ou null"
                    else:
                        json_template[section_id][champ_id] = "valeur ou null"
        
        json_template_str = json.dumps(json_template, indent=2, ensure_ascii=False)
        
        # Prompt d'extraction générique
        extraction_prompt = f"""Tu es un extracteur d'informations pour une {fiche_nom}.

**CONTEXTE:**
Dernière question posée: "{last_question}"

**MESSAGE UTILISATEUR:**
{user_message}

**STRUCTURE ATTENDUE (retourne UNIQUEMENT les champs mentionnés):**

{json_template_str}

**RÈGLES:**
- Si l'utilisateur dit "oui", "OK", "d'accord" pour un champ boolean: retourne true
- Si l'utilisateur dit "non", "pas de", "aucun" pour un boolean: retourne false  
- Si l'utilisateur dit "RAS", "rien", "rien à signaler": mets "RAS" comme valeur
- Si l'utilisateur dit "pas de", "aucun", "non renseigné": mets "Non renseigné"
- Pour les options OK/NOK/NA: retourne exactement "OK", "NOK" ou "NA"
- Extrait TOUTES les informations pertinentes du message
- Ne retourne QUE les champs mentionnés (ne mets pas tous les champs à null)

**FORMAT:**
Retourne UNIQUEMENT le JSON, rien d'autre (pas de texte avant ou après, pas de markdown).

JSON:"""
        
        try:
            # Appeler le LLM
            response = get_chat_response([{"role": "user", "content": extraction_prompt}])
            
            # Nettoyer la réponse
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            print(f"📝 Réponse extraction: {response[:300]}...")
            
            # Parser le JSON
            extracted = json.loads(response)
            print(f"✅ JSON parsé: {extracted}")
            
            champs_mis_a_jour = []
            
            # Mettre à jour les sections
            for section_id, section_values in extracted.items():
                if section_id not in self.entities:
                    self.entities[section_id] = {}
                
                current_section = self.entities[section_id]
                
                for champ_id, value in section_values.items():
                    if value is not None and value != "null" and value != "":
                        # Convertir les strings "true"/"false" en boolean
                        if isinstance(value, str):
                            if value.lower() == "true":
                                value = True
                            elif value.lower() == "false":
                                value = False
                        
                        current_section[champ_id] = value
                        champs_mis_a_jour.append(f"{section_id}.{champ_id}")
                        print(f"✓ Mis à jour: {section_id}.{champ_id} = {value}")
            
            # Mettre à jour les champs manquants
            self._update_champs_manquants()
            
            return champs_mis_a_jour
            
        except json.JSONDecodeError as e:
            print(f"❌ Erreur JSON: {e}")
            print(f"Réponse brute: {response}")
            return []
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction: {e}")
            return []

    def update_from_conversation(self, user_message: str, assistant_response: str = "", last_question: str = "") -> List[str]:
        """
        Met à jour la fiche basé sur la conversation.
        Utilise un LLM pour extraire les informations structurées.
        
        Args:
            user_message: Message de l'utilisateur
            assistant_response: Réponse de l'assistant (non utilisé pour l'instant)
            last_question: Dernière question posée pour avoir le contexte
        
        Returns:
            Liste des champs mis à jour
        """
        from utils.LLM import get_chat_response
        import json
        
        # Obtenir la prochaine question pour le contexte
        if not last_question:
            last_question = self.get_next_question() or ""
        
        print(f"🔍 Extraction avec contexte: '{last_question[:100]}...'")
        print(f"📝 Message utilisateur: '{user_message}'")
        
        # NOUVEAU: Utiliser la structure réelle de la fiche pour l'extraction
        if self.fiche_type and self.fiche_type != FicheType.DEFAUTS:
            return self._update_from_conversation_generic(user_message, last_question)
        
        # Ancien code pour les fiches de défauts (conservé pour compatibilité)
        extraction_prompt = f"""Tu es un extracteur d'informations pour des fiches de défauts.
        
**CONTEXTE DE LA CONVERSATION:**
Dernière question posée: "{last_question}"

Extrait UNIQUEMENT les informations pertinentes du message suivant et retourne un JSON.

**MESSAGE DE L'UTILISATEUR:**
{user_message}

**STRUCTURE ATTENDUE (retourne UNIQUEMENT les champs mentionnés):**

{{
  "mise_en_service": {{
    "nom_chantier": "valeur ou null",
    "ao": "valeur ou null",
    "num_chantier": "valeur ou null",
    "nom_technicien": "valeur ou null",
    "date": "valeur ou null",
    "signature": "présente/absente/null"
  }},
  "tableau_defauts": [
    {{
      "localisation": "Partie DC/AC/Communication/etc.",
      "anomalies": "texte ou RAS ou null",
      "temps_passe": "durée ou null"
    }}
  ]
}}

**RÈGLES IMPORTANTES:**
- Si l'utilisateur dit "RAS", "rien", "rien à signaler", "pas de problème", "aucun", mets "RAS"
- Si l'utilisateur dit "pas d'AO", "pas de", "aucun", "non", mets "Non renseigné"
- Pour le temps: "5 minutes" → "5 min", "1 heure" → "1h", "RAS" → "0 min", "rien" → "0 min"
- Pour la signature: "oui", "signée" → "présente", "non", "pas encore" → "absente"

**DÉTECTION DE LA SECTION (TRÈS IMPORTANT):**
- Si la dernière question mentionne "Partie DC", alors localisation = "Partie DC"
- Si la dernière question mentionne "Partie AC", alors localisation = "Partie AC"
- Si la dernière question mentionne "Partie Communication" ou "Communication", alors localisation = "Partie Communication"
- Si la dernière question mentionne "Liaison Equipotentielle" ou "Mesure de terre", alors localisation = "Liaison Equipotentielle / Mesure de terre"
- Si la dernière question mentionne "Divers" ou "Remarques", alors localisation = "Divers / Remarques"
- TOUJOURS renseigner le champ "localisation" quand tu détectes une anomalie ou un temps pour le tableau

**EXEMPLES:**
Question: "Pour la section 'Partie DC', as-tu rencontré des anomalies ?"
Réponse utilisateur: "RAS"
→ {{"tableau_defauts": [{{"localisation": "Partie DC", "anomalies": "RAS", "temps_passe": null}}]}}

Question: "Combien de temps as-tu passé sur 'Partie AC' ?"
Réponse utilisateur: "5 minutes"
→ {{"tableau_defauts": [{{"localisation": "Partie AC", "anomalies": null, "temps_passe": "5 min"}}]}}

- Ne retourne QUE les champs explicitement mentionnés dans le message
- Retourne UNIQUEMENT le JSON, rien d'autre (pas de texte avant ou après)

RETOURNE LE JSON:"""
        
        try:
            # Appeler le LLM pour extraire
            response = get_chat_response([{"role": "user", "content": extraction_prompt}])
            
            # Nettoyer la réponse pour extraire le JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            print(f"📝 Réponse extraction: {response[:200]}...")  # Debug
            
            # Parser le JSON
            extracted = json.loads(response)
            print(f"✅ JSON parsé: {extracted}")  # Debug
            
            champs_mis_a_jour = []
            
            # Mettre à jour mise_en_service
            if "mise_en_service" in extracted:
                mes = extracted["mise_en_service"]
                current_mes = self.entities.get("mise_en_service", {})
                
                for key, value in mes.items():
                    if value and value != "null":
                        current_mes[key] = value
                        champs_mis_a_jour.append(f"mise_en_service.{key}")
                
                self.entities["mise_en_service"] = current_mes
            
            # Mettre à jour tableau_defauts
            if "tableau_defauts" in extracted and extracted["tableau_defauts"]:
                current_tableau = self.entities.get("tableau_defauts", [])
                print(f"📋 Tableau actuel ({len(current_tableau)} lignes): {[l.get('localisation') for l in current_tableau]}")
                
                for new_ligne in extracted["tableau_defauts"]:
                    loc = new_ligne.get("localisation")
                    if not loc:
                        print(f"⚠️ Localisation manquante dans l'extraction: {new_ligne}")
                        continue
                    
                    print(f"🔍 Recherche de la ligne pour localisation: '{loc}'")
                    
                    # Trouver la ligne correspondante dans le tableau
                    ligne_existante = None
                    for ligne in current_tableau:
                        ligne_loc = ligne.get("localisation")
                        # Essayer une correspondance exacte
                        if ligne_loc == loc:
                            ligne_existante = ligne
                            break
                        # Essayer une correspondance partielle (fallback)
                        if loc in ligne_loc or ligne_loc in loc:
                            ligne_existante = ligne
                            print(f"✓ Correspondance partielle trouvée: '{ligne_loc}'")
                            break
                    
                    if ligne_existante:
                        # Mettre à jour les champs
                        if new_ligne.get("anomalies"):
                            ligne_existante["anomalies"] = new_ligne["anomalies"]
                            champs_mis_a_jour.append(f"{ligne_existante.get('localisation')} - anomalies")
                        if new_ligne.get("temps_passe"):
                            ligne_existante["temps_passe"] = new_ligne["temps_passe"]
                            champs_mis_a_jour.append(f"{ligne_existante.get('localisation')} - temps")
                    else:
                        print(f"❌ Aucune ligne trouvée pour localisation: '{loc}'")
                
                self.entities["tableau_defauts"] = current_tableau
            
            # Recalculer les champs manquants
            self._update_champs_manquants()
            
            return champs_mis_a_jour
            
        except Exception as e:
            print(f"Erreur lors de l'extraction: {e}")
            return []
    
    def get_completion_summary(self) -> str:
        """Génère un résumé visuel de la complétion (adapté au type de fiche)"""
        completude = self.get_completion_percentage()
        
        # Version générique pour tous les types de fiches
        if self.fiche_type and self.fiche_type != FicheType.DEFAUTS:
            structure = get_fiche_structure(self.fiche_type)
            fiche_nom = structure["nom"]
            
            summary = f"📊 **{fiche_nom}** ({completude:.0f}% complète)\n\n"
            
            # Parcourir toutes les sections
            for section_id, section_data in structure["sections"].items():
                section_name = section_data.get("nom", section_id)
                section_entity = self.entities.get(section_id, {})
                
                if "champs" in section_data:
                    # Compter les champs remplis vs total
                    total = len([c for c in section_data["champs"] if c.get("obligatoire", True)])
                    remplis = sum(1 for c in section_data["champs"] 
                                if c.get("obligatoire", True) and 
                                not self._is_field_empty(section_entity.get(c["id"])))
                    
                    icon = "✅" if remplis == total else "⚠️" if remplis > 0 else "❌"
                    summary += f"{icon} **{section_name}:** {remplis}/{total}\n"
            
            return summary
        
        # Code original pour les fiches de défauts (conservé)
        mes = self.entities.get("mise_en_service", {})
        tableau = self.entities.get("tableau_defauts", [])
        
        summary = f"📊 **État de la fiche** ({completude:.0f}% complète)\n\n"
        
        # Mise en service
        summary += "**🔧 Mise en Service:**\n"
        for key, value in mes.items():
            label = key.replace("_", " ").title()
            status = "✅" if not self._is_field_empty(value) else "❌"
            summary += f"{status} {label}\n"
        
        # Tableau
        summary += "\n**📋 Tableau des Défauts:**\n"
        for ligne in tableau:
            loc = ligne.get("localisation", "?")
            has_anom = not self._is_field_empty(ligne.get("anomalies"))
            has_temps = not self._is_field_empty(ligne.get("temps_passe"))
            
            if has_anom and has_temps:
                status = "✅"
            elif has_anom or has_temps:
                status = "⚠️"
            else:
                status = "❌"
            
            summary += f"{status} {loc}\n"
        
        return summary
    
    def export_json(self) -> str:
        """Exporte la fiche en JSON"""
        return json.dumps({
            "entities": self.entities,
            "completion_percentage": self.get_completion_percentage(),
            "mode": self.mode
        }, indent=2, ensure_ascii=False)
    
    def export_txt(self) -> str:
        """Exporte la fiche en format texte brut"""
        from datetime import datetime
        
        if not self.fiche_type:
            return "Erreur: Type de fiche non défini"
        
        structure = get_fiche_structure(self.fiche_type)
        fiche_nom = structure["nom"].upper()
        
        txt = "=" * 60 + "\n"
        txt += f"{fiche_nom}\n"
        txt += "=" * 60 + "\n"
        txt += f"Exporté le: {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n"
        txt += f"Complétion: {self.get_completion_percentage():.0f}%\n"
        txt += "=" * 60 + "\n\n"
        
        # Parcourir toutes les sections
        for section_id, section_data in structure["sections"].items():
            section_name = section_data.get("nom", section_id)
            txt += f"📋 {section_name.upper()}\n"
            txt += "-" * 60 + "\n"
            
            section_entity = self.entities.get(section_id, {})
            
            if "lignes" in section_data:
                # Section tableau
                txt += "\n"
                lignes = self.entities.get(section_id, [])
                for ligne in lignes:
                    loc = ligne.get("localisation", "?")
                    txt += f"🔹 {loc}\n"
                    for champ in section_data["lignes"][0]["champs"]:
                        valeur = ligne.get(champ, "N/A")
                        champ_label = champ.replace("_", " ").title()
                        txt += f"   {champ_label:15}: {valeur}\n"
                    txt += "\n"
            elif "champs" in section_data:
                # Section normale
                for champ in section_data["champs"]:
                    label = champ["label"]
                    valeur = section_entity.get(champ["id"], "N/A")
                    # Formater la valeur selon le type
                    if champ["type"] == "boolean":
                        valeur = "Oui" if valeur else "Non" if valeur is False else "N/A"
                    txt += f"{label:30}: {valeur}\n"
                txt += "\n"
        
        txt += "=" * 60 + "\n"
        txt += "FIN DE LA FICHE\n"
        txt += "=" * 60 + "\n"
        
        return txt
    
    def is_complete(self) -> bool:
        """Vérifie si la fiche est complète"""
        return len(self.champs_manquants) == 0


def detect_fiche_type_from_message(message: str) -> Optional[FicheType]:
    """
    Détecte le type de fiche demandé dans un message utilisateur.
    
    Args:
        message: Message de l'utilisateur
        
    Returns:
        FicheType détecté ou None
    """
    message_lower = message.lower()
    
    # Patterns pour chaque type
    patterns = {
        FicheType.DEFAUTS: ["défaut", "defaut", "anomalie", "problème", "probleme", "1"],
        FicheType.CONTROLE_MES: ["contrôle mes", "controle mes", "fc mes", "fiche controle mes", "mes", "mise en service", "2"],
        FicheType.ELECTRICIENS: ["électricien", "electricien", "travaux électrique", "travaux electrique", "3"],
        FicheType.POSEURS: ["poseur", "pose", "installation panneaux", "4"]
    }
    
    for fiche_type, keywords in patterns.items():
        if any(keyword in message_lower for keyword in keywords):
            return fiche_type
    
    return None


def create_fiche_system_message(manager: FicheDefautChatManager) -> Dict:
    """
    Crée le message système pour le chatbot avec le contexte de la fiche.
    
    Args:
        manager: Le gestionnaire de fiche
        
    Returns:
        Dict avec role="system" et content=prompt
    """
    return {
        "role": "system",
        "content": manager.get_system_prompt()
    }


def _get_fiche_info_summary(manager: FicheDefautChatManager) -> str:
    """Génère un résumé des informations à fournir pour un type de fiche"""
    if not manager.fiche_type:
        return ""
    
    structure = get_fiche_structure(manager.fiche_type)
    summary = "\n**📝 Informations à fournir :**\n\n"
    
    if manager.fiche_type == FicheType.DEFAUTS:
        summary += "**1️⃣ Mise en Service** (7 champs)\n"
        summary += "   • Nom du chantier\n"
        summary += "   • N° d'Appel d'Offres (AO)\n"
        summary += "   • N° de chantier\n"
        summary += "   • Nom du technicien\n"
        summary += "   • Date d'intervention (format JJ/MM/AAAA)\n"
        summary += "   • Signature technicien\n"
        summary += "   • Remarques générales\n\n"
        summary += "**2️⃣ Tableau des Défauts** (5 sections détaillées)\n"
        summary += "   Pour chaque section : Localisation + Anomalies + Temps passé\n\n"
        summary += "   **Partie DC :**\n"
        summary += "   • Anomalies rencontrées (ou RAS)\n"
        summary += "   • Temps passé (en minutes)\n\n"
        summary += "   **Partie AC :**\n"
        summary += "   • Anomalies rencontrées (ou RAS)\n"
        summary += "   • Temps passé (en minutes)\n\n"
        summary += "   **Partie Communication :**\n"
        summary += "   • Anomalies (ex: câblage, fils non dénudés/serrés)\n"
        summary += "   • Temps passé (en minutes)\n\n"
        summary += "   **Liaison Equipotentielle / Mesure de terre :**\n"
        summary += "   • Anomalies (ex: résistance ohmétrique élevée)\n"
        summary += "   • Temps passé (en minutes)\n\n"
        summary += "   **Divers / Remarques :**\n"
        summary += "   • Autres problèmes (ex: pochette non remplie)\n"
        summary += "   • Temps passé (en minutes)\n"
    
    elif manager.fiche_type == FicheType.CONTROLE_MES:
        summary += "**1️⃣ En-tête** (8 champs)\n"
        summary += "   • Nom chantier, N° chantier, Date\n"
        summary += "   • Nom technicien, Signature\n"
        summary += "   • AO (Oui/Non)\n"
        summary += "   • Avec Bridage / Revente / Revente Totale\n"
        summary += "   • Supervision serveur fonctionnelle (Oui/Non)\n\n"
        summary += "**2️⃣ Local Technique** (13 points de contrôle)\n"
        summary += "   Chaque élément : OK / NOK / NA + Remarques\n"
        summary += "   • Arrêt d'urgence (nombre présent)\n"
        summary += "   • Serrages armoire AC\n"
        summary += "   • Serrages coffret DC et/ou PE DC\n"
        summary += "   • Paramètres onduleurs (RCD, IP fixe)\n"
        summary += "   • Bridage onduleurs (conformité KVA, valeurs Ond 1-4)\n"
        summary += "   • Réglage Cos Phi (directive Enedis 0.94)\n"
        summary += "   • Section câble puissance (mm², ALU/CUI)\n"
        summary += "   • Mesure de terre (valeur en Ω)\n"
        summary += "   • Concordance Schéma Unifilaire / Armoire AC\n"
        summary += "   • Présence repérages et N° série\n"
        summary += "   • Présence documents (schémas plastifiés)\n"
        summary += "   • Distance entre onduleurs (cm) / Option Shelter\n"
        summary += "   • Vérification courant chaînes panneaux\n\n"
        summary += "**3️⃣ Point de Livraison** (6 points)\n"
        summary += "   Chaque élément : OK / NOK / NA + Remarques\n"
        summary += "   • Serrages bretelles et câbles PDL\n"
        summary += "   • Absence continuité (entre phases & neutre-phase)\n"
        summary += "   • Réglage Disjoncteur NSX (3D-N/2 ou 4P4D, Ir, Isd)\n"
        summary += "   • Réglage Vigi (calibre 0.3/1A/3A/5A selon KVA)\n"
        summary += "   • Installations (0-36, 36-100, 100-250, 250-500 KVA)\n"
        summary += "   • ΔT Différentiel (60ms ou 0ms selon config)\n\n"
        summary += "**4️⃣ Administratif** (6 points)\n"
        summary += "   Chaque élément : OK / NOK / NA\n"
        summary += "   • Signature PV Réception Travaux\n"
        summary += "   • Remplissage Satisfaction client\n"
        summary += "   • Remplissage document APEPHA\n"
        summary += "   • Explications fonctionnement au client\n"
        summary += "   • Remise Procédure après MES\n"
        summary += "   • Signature Fin MES avec Enedis\n\n"
        summary += "**5️⃣ Informations Équipements** (détaillé)\n"
        summary += "   • Onduleurs 1-4 (Référence, N° Série, N° ID, IP Fixe)\n"
        summary += "   • Outils Communication (10+ types possibles)\n"
        summary += "     - Smart Logger, Smart Dongle, Webdynsun\n"
        summary += "     - Compteurs N°1-3, Data Manager, Écran déporté\n"
        summary += "     - Pour chaque : Accès serveur, IP, MDP, N° Série, PIC, RID\n"
    
    elif manager.fiche_type == FicheType.ELECTRICIENS:
        summary += "**1️⃣ Informations Projet** (9 champs)\n"
        summary += "   • Nom du dossier, N° chantier, Semaine de pose\n"
        summary += "   • Nom client, Téléphone, Adresse\n"
        summary += "   • Commercial, Chargé d'études, Conducteur travaux\n\n"
        summary += "**2️⃣ Réception Pose Centrale**\n"
        summary += "   • Réception sans réserve (Oui/Non)\n"
        summary += "   • Nature des réserves (si avec réserves)\n\n"
        summary += "**3️⃣ Réception Raccordement**\n"
        summary += "   • Réception sans réserve (Oui/Non)\n"
        summary += "   • Nature des réserves (si avec réserves)\n\n"
        summary += "**4️⃣ Configuration Chantier**\n"
        summary += "   • Puissance installation (kWc)\n"
        summary += "   • Panneaux (nombre x modèle)\n"
        summary += "   • Système d'intégration, Onduleur(s)\n"
        summary += "   • Option Shelter, Type vente\n\n"
        summary += "**5️⃣ État Chantier**\n"
        summary += "   • Chantier Terminé (Oui/Non)\n"
        summary += "   • NSX Raccordé (Oui/Non)\n"
        summary += "   • Com Onduleur Terminé (Oui/Non)\n\n"
        summary += "**6️⃣ Mesures Tensions Chaînes DC** (jusqu'à 50 strings)\n"
        summary += "   Pour chaque string : N°, PV, Vdc, Conformité\n"
        summary += "   • Strings N°1 à N°50\n\n"
        summary += "**7️⃣ Vérifications** (4 catégories)\n"
        summary += "   Chaque vérification : OK / NOK / Remarques\n"
        summary += "   • Vérification DC (compatibilité connecteurs, tensions, distances)\n"
        summary += "   • Vérification armoires AC (serrages, PE, terre, câbles)\n"
        summary += "   • Vérification repérage (strings, câbles, étiquetage)\n"
        summary += "   • Vérification communication (câblages, alimentation)\n\n"
        summary += "**8️⃣ Documents & Photos**\n"
        summary += "   • Présence schéma électrique et calepinage\n"
        summary += "   • Photos locaux onduleurs et coffrets\n"
    
    elif manager.fiche_type == FicheType.POSEURS:
        summary += "**1️⃣ Informations Projet** (9 champs)\n"
        summary += "   • Nom dossier, N° chantier, Semaine pose\n"
        summary += "   • Nom client, Téléphone, Adresse\n"
        summary += "   • Commercial, Chargé d'études, Conducteur travaux\n\n"
        summary += "**2️⃣ Type d'Installation**\n"
        summary += "   • Vente totale / surplus / Autoconsommation\n"
        summary += "   • Option Shelter (Oui/Non)\n\n"
        summary += "**3️⃣ Pochette Documents** (7 documents)\n"
        summary += "   Chaque doc : VALIDE / NA\n"
        summary += "   • Plan prévention / PPSPS\n"
        summary += "   • Schéma unifilaire\n"
        summary += "   • Carnet de plan\n"
        summary += "   • Nomenclature\n"
        summary += "   • Photos visites chantiers\n"
        summary += "   • PV réception travaux\n"
        summary += "   • Fiche fin de chantier\n\n"
        summary += "**4️⃣ Configuration Chantier**\n"
        summary += "   • Puissance installation (kWc)\n"
        summary += "   • Panneaux (nombre x modèle)\n"
        summary += "   • Système d'intégration (ex: FIBRO SOLAR)\n"
        summary += "   • Onduleur(s) (modèle et quantité)\n\n"
        summary += "**5️⃣ Réception des Travaux**\n"
        summary += "   • Pose centrale : sans réserve ou avec réserves\n"
        summary += "   • Raccordement électrique : sans réserve ou avec réserves\n"
        summary += "   • Date signature, Lieu\n"
        summary += "   • Signatures : Client, Conducteur, Chef équipe\n\n"
        summary += "**6️⃣ Contrôle des Panneaux** (jusqu'à 35 strings)\n"
        summary += "   Pour chaque string : N°, Nb panneaux, Tension, Mesure RISO\n"
        summary += "   • Strings N°1 à N°35 avec tensions (ex: 628-661 Vdc)\n"
        summary += "   • Conformité O/N pour chaque string\n\n"
        summary += "**7️⃣ Pose Bac Acier** (8 contrôles)\n"
        summary += "   Chaque contrôle : OUI / NON\n"
        summary += "   • Sens recouvrement selon vent\n"
        summary += "   • Démoussage feutre\n"
        summary += "   • Recouvrements transversal/longitudinal\n"
        summary += "   • Type fixation, Nb tirefonds, Vis couture\n\n"
        summary += "**8️⃣ Pose Kit Intégration & Panneaux** (7 contrôles)\n"
        summary += "   Chaque contrôle : OUI / NON\n"
        summary += "   • Pose conforme notice constructeur\n"
        summary += "   • Pose strings (éviter boucles induction)\n"
        summary += "   • Bon nombre panneaux par string\n"
        summary += "   • Serrage modules, Nettoyage\n"
        summary += "   • Bons de livraison, Photos installation\n"
    
    return summary

def get_initial_fiche_message(manager: FicheDefautChatManager) -> str:
    """
    Génère le message initial du chatbot pour démarrer la complétion.
    
    Args:
        manager: Le gestionnaire de fiche
        
    Returns:
        Message d'accueil adapté au mode (sélection/création/complétion)
    """
    # Mode sélection : demander le type
    if manager.mode == "selection":
        fiches_list = format_fiche_type_list()
        return f"""📋 **Mode Fiches activé**

Quel type de fiche veux-tu remplir ?

{fiches_list}

💡 *Indique le numéro ou le nom de la fiche que tu veux créer.*"""
    
    # Mode création
    completude = manager.get_completion_percentage()
    
    # Récupérer le nom de la fiche de manière sécurisée
    fiche_nom = "Fiche"
    if manager.fiche_type:
        fiche_structure = get_fiche_structure(manager.fiche_type)
        if fiche_structure:
            fiche_nom = fiche_structure["nom"]
    
    if manager.mode == "creation":
        info_summary = _get_fiche_info_summary(manager)
        
        return f"""📋 **{fiche_nom} activée**

Je vais t'aider à remplir ta {fiche_nom.lower()}. Donne-moi les informations au fur et à mesure, je note tout !

{info_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**🚀 Commençons !**

{manager.get_next_question()}

💡 *Tu peux donner plusieurs infos à la fois si tu veux !*"""
    
    # Mode complétion
    else:
        if completude >= 100:
            return f"""✅ **{fiche_nom} complète !**

J'ai analysé le document et toutes les informations sont présentes.

{manager.get_completion_summary()}

Y a-t-il quelque chose que tu souhaites modifier ou vérifier ?"""
        else:
            champs_manquants_count = len(manager.champs_manquants)
            return f"""📋 **{fiche_nom} analysée** ({completude:.0f}% complet)

J'ai extrait ce qui était disponible. Il manque encore **{champs_manquants_count} information(s)**.

{manager.get_next_question()}

💡 *Donne-moi les infos manquantes et je complète la fiche !*"""
