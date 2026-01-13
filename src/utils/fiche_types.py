"""
Définition des différents types de fiches et leurs structures
"""

from typing import Dict, List
from enum import Enum


class FicheType(Enum):
    """Types de fiches disponibles"""
    DEFAUTS = "defauts"
    CONTROLE_MES = "controle_mes"
    ELECTRICIENS = "electriciens"
    POSEURS = "poseurs"


# Structures de chaque type de fiche
FICHE_STRUCTURES = {
    FicheType.DEFAUTS: {
        "nom": "Fiche de Défauts",
        "description": "Pour noter les anomalies et défauts constatés lors d'une intervention",
        "sections": {
            "mise_en_service": {
                "nom": "Mise en Service",
                "champs": [
                    {"id": "nom_chantier", "label": "Nom du chantier", "type": "text", "obligatoire": True},
                    {"id": "ao", "label": "Numéro d'Appel d'Offres (AO)", "type": "text", "obligatoire": False},
                    {"id": "num_chantier", "label": "Numéro de chantier", "type": "text", "obligatoire": True},
                    {"id": "nom_technicien", "label": "Nom du technicien", "type": "text", "obligatoire": True},
                    {"id": "date", "label": "Date d'intervention", "type": "date", "obligatoire": True},
                    {"id": "signature", "label": "Signature", "type": "boolean", "obligatoire": False}
                ]
            },
            "tableau_defauts": {
                "nom": "Tableau des Défauts",
                "lignes": [
                    {"localisation": "Partie DC", "champs": ["anomalies", "temps_passe"]},
                    {"localisation": "Partie AC", "champs": ["anomalies", "temps_passe"]},
                    {"localisation": "Partie Communication", "champs": ["anomalies", "temps_passe"]},
                    {"localisation": "Liaison Equipotentielle / Mesure de terre", "champs": ["anomalies", "temps_passe"]},
                    {"localisation": "Divers / Remarques", "champs": ["anomalies", "temps_passe"]}
                ]
            }
        }
    },
    
    FicheType.CONTROLE_MES: {
        "nom": "Fiche de Contrôle MES",
        "description": "Fiche de contrôle pour la mise en service d'une installation photovoltaïque",
        "sections": {
            "en_tete": {
                "nom": "En-tête",
                "champs": [
                    {"id": "nom_chantier", "label": "Nom Chantier", "type": "text", "obligatoire": True},
                    {"id": "ao", "label": "AO (Appel d'Offres)", "type": "boolean", "obligatoire": False},
                    {"id": "num_chantier", "label": "N° Chantier", "type": "text", "obligatoire": True},
                    {"id": "date", "label": "Date", "type": "date", "obligatoire": True},
                    {"id": "nom_technicien", "label": "Nom Technicien", "type": "text", "obligatoire": True},
                    {"id": "avec_bridage", "label": "Avec Bridage", "type": "boolean", "obligatoire": False},
                    {"id": "avec_revente", "label": "Avec Revente", "type": "boolean", "obligatoire": False},
                    {"id": "revente_totale", "label": "Revente Totale", "type": "boolean", "obligatoire": False},
                    {"id": "supervision_ok", "label": "Supervision serveur fonctionnelle", "type": "boolean", "obligatoire": True},
                    {"id": "signature_technicien", "label": "Signature Technicien", "type": "text", "obligatoire": False}
                ]
            },
            "local_technique": {
                "nom": "Local Technique",
                "type": "checklist",
                "champs": [
                    {"id": "arret_urgence", "label": "Arrêt d'urgence", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "serrages_armoire_ac", "label": "Serrages armoire AC", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "serrages_coffret_dc", "label": "Serrages coffret DC et/ou PE DC", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "parametres_onduleurs", "label": "Paramètres fonctionnement onduleurs", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "bridage_onduleurs", "label": "Bridage des onduleurs", "type": "text", "obligatoire": True},
                    {"id": "reglage_cos_phi", "label": "Réglage Cos Phi Onduleurs", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "section_cable", "label": "Section câble de puissance", "type": "text", "obligatoire": True},
                    {"id": "mesure_terre", "label": "Mesure de terre", "type": "text", "obligatoire": True},
                    {"id": "concordance_schema", "label": "Concordance Schéma Unifilaire", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "presence_reperages", "label": "Présence repérages et numéros de série", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "presence_documents", "label": "Présence des documents", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "distance_onduleurs", "label": "Distance entre onduleurs", "type": "text", "obligatoire": True},
                    {"id": "verification_courant", "label": "Vérification courant chaînes", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True}
                ]
            },
            "point_livraison": {
                "nom": "Point de Livraison",
                "champs": [
                    # Serrages
                    {"id": "serrages_bretelles", "label": "Serrages Bretelles et câbles PDL", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "serrages_remarque", "label": "Serrages - Remarque", "type": "textarea", "obligatoire": False},
                    
                    # Continuité
                    {"id": "absence_continuite", "label": "Absence de continuité (Entre phases & Entre neutre et phase)", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "continuite_remarque", "label": "Continuité - Remarque", "type": "textarea", "obligatoire": False},
                    
                    # Réglage Disjoncteur NSX
                    {"id": "disjoncteur_type_3dn2", "label": "Disjoncteur NSX - Type 3D-N/2", "type": "boolean", "obligatoire": False},
                    {"id": "disjoncteur_type_4p4d", "label": "Disjoncteur NSX - Type 4P4D", "type": "boolean", "obligatoire": False},
                    {"id": "disjoncteur_ir", "label": "Disjoncteur NSX - Ir (en A)", "type": "text", "obligatoire": True},
                    {"id": "disjoncteur_isd", "label": "Disjoncteur NSX - Isd (facteur X)", "type": "text", "obligatoire": True},
                    {"id": "disjoncteur_etat", "label": "Disjoncteur NSX - État", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    
                    # Réglage Vigi
                    {"id": "vigi_calibre_03", "label": "Vigi - Calibre 0.3A", "type": "boolean", "obligatoire": False},
                    {"id": "vigi_calibre_1a", "label": "Vigi - Calibre 1A", "type": "boolean", "obligatoire": False},
                    {"id": "vigi_calibre_3a", "label": "Vigi - Calibre 3A", "type": "boolean", "obligatoire": False},
                    {"id": "vigi_calibre_5a", "label": "Vigi - Calibre 5A", "type": "boolean", "obligatoire": False},
                    {"id": "vigi_etat", "label": "Vigi - État", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    
                    # Type d'installation (selon puissance)
                    {"id": "installation_type", "label": "Type d'installation", "type": "select", 
                     "options": [
                         "0-36 Kva (100 Ω / 0.03 à 0.5 mA)",
                         "36-100 Kva (50 Ω / 1A)",
                         "100-250 Kva (16 Ω / 3A)",
                         "250-500 Kva (10 Ω / 5A)"
                     ], "obligatoire": True},
                    {"id": "installation_etat", "label": "Installation - État", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    
                    # ΔT Différentiel
                    {"id": "dt_differentiel", "label": "ΔT Différentiel (60 ms avec différentiel sur disjoncteur onduleur / 0 ms IMPERATIF sans différentiel)", "type": "text", "obligatoire": True},
                    {"id": "dt_differentiel_etat", "label": "ΔT Différentiel - État", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "dt_differentiel_remarque", "label": "ΔT Différentiel - Remarque", "type": "textarea", "obligatoire": False}
                ]
            },
            "administratif": {
                "nom": "Administratif",
                "champs": [
                    {"id": "signature_pv", "label": "Signature PV Réception Travaux", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "satisfaction_client", "label": "Remplissage Satisfaction client", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "document_apepha", "label": "Remplissage document APEPHA", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "explications_client", "label": "Explications de fonctionnement au client", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "procedure_apres_mes", "label": "Remise Procédure après MES", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True},
                    {"id": "signature_enedis", "label": "Signature Fin de MES avec Enedis", "type": "select", "options": ["OK", "NOK", "NA"], "obligatoire": True}
                ]
            },
            "equipements": {
                "nom": "Informations Équipements",
                "champs": [
                    {"id": "onduleur_1_ref", "label": "Onduleur N°1 - Référence", "type": "text", "obligatoire": False},
                    {"id": "onduleur_1_serie", "label": "Onduleur N°1 - N° Série", "type": "text", "obligatoire": False},
                    {"id": "onduleur_1_id", "label": "Onduleur N°1 - N° ID", "type": "text", "obligatoire": False},
                    {"id": "onduleur_1_ip", "label": "Onduleur N°1 - Adresse IP Fixe", "type": "text", "obligatoire": False},
                    
                    {"id": "onduleur_2_ref", "label": "Onduleur N°2 - Référence", "type": "text", "obligatoire": False},
                    {"id": "onduleur_2_serie", "label": "Onduleur N°2 - N° Série", "type": "text", "obligatoire": False},
                    {"id": "onduleur_2_id", "label": "Onduleur N°2 - N° ID", "type": "text", "obligatoire": False},
                    {"id": "onduleur_2_ip", "label": "Onduleur N°2 - Adresse IP Fixe", "type": "text", "obligatoire": False},
                    
                    {"id": "onduleur_3_ref", "label": "Onduleur N°3 - Référence", "type": "text", "obligatoire": False},
                    {"id": "onduleur_3_serie", "label": "Onduleur N°3 - N° Série", "type": "text", "obligatoire": False},
                    {"id": "onduleur_3_id", "label": "Onduleur N°3 - N° ID", "type": "text", "obligatoire": False},
                    {"id": "onduleur_3_ip", "label": "Onduleur N°3 - Adresse IP Fixe", "type": "text", "obligatoire": False},
                    
                    {"id": "onduleur_4_ref", "label": "Onduleur N°4 - Référence", "type": "text", "obligatoire": False},
                    {"id": "onduleur_4_serie", "label": "Onduleur N°4 - N° Série", "type": "text", "obligatoire": False},
                    {"id": "onduleur_4_id", "label": "Onduleur N°4 - N° ID", "type": "text", "obligatoire": False},
                    {"id": "onduleur_4_ip", "label": "Onduleur N°4 - Adresse IP Fixe", "type": "text", "obligatoire": False},
                    
                    # Outils de communication
                    {"id": "smart_logger_ref", "label": "SMART LOGGER 3000A - Référence", "type": "text", "obligatoire": False},
                    {"id": "smart_logger_acces", "label": "SMART LOGGER 3000A - Accès", "type": "boolean", "obligatoire": False},
                    {"id": "smart_logger_ip", "label": "SMART LOGGER 3000A - IP", "type": "text", "obligatoire": False},
                    {"id": "smart_logger_mdp", "label": "SMART LOGGER 3000A - Mot de passe", "type": "text", "obligatoire": False},
                    {"id": "smart_logger_serie", "label": "SMART LOGGER 3000A - N° Série", "type": "text", "obligatoire": False},
                    
                    {"id": "smart_dongle_ref", "label": "SMART DONGLE 4G/RJ45 - Référence", "type": "text", "obligatoire": False},
                    {"id": "smart_dongle_acces", "label": "SMART DONGLE 4G/RJ45 - Accès", "type": "boolean", "obligatoire": False},
                    {"id": "smart_dongle_ip", "label": "SMART DONGLE 4G/RJ45 - IP", "type": "text", "obligatoire": False},
                    {"id": "smart_dongle_mdp", "label": "SMART DONGLE 4G/RJ45 - Mot de passe", "type": "text", "obligatoire": False},
                    {"id": "smart_dongle_serie", "label": "SMART DONGLE 4G/RJ45 - N° Série", "type": "text", "obligatoire": False},
                    
                    {"id": "webdynsun_ref", "label": "WEBDYNSUN - Référence", "type": "text", "obligatoire": False},
                    {"id": "webdynsun_acces", "label": "WEBDYNSUN - Accès", "type": "boolean", "obligatoire": False},
                    {"id": "webdynsun_ip", "label": "WEBDYNSUN - IP", "type": "text", "obligatoire": False},
                    {"id": "webdynsun_mdp", "label": "WEBDYNSUN - Mot de passe", "type": "text", "obligatoire": False},
                    {"id": "webdynsun_serie", "label": "WEBDYNSUN - N° Série", "type": "text", "obligatoire": False},
                    
                    {"id": "data_manager_ref", "label": "DATA MANAGER - Référence", "type": "text", "obligatoire": False},
                    {"id": "data_manager_acces", "label": "DATA MANAGER - Accès", "type": "boolean", "obligatoire": False},
                    {"id": "data_manager_ip", "label": "DATA MANAGER - IP", "type": "text", "obligatoire": False},
                    {"id": "data_manager_mdp", "label": "DATA MANAGER - Mot de passe", "type": "text", "obligatoire": False},
                    {"id": "data_manager_pic", "label": "DATA MANAGER - PIC", "type": "text", "obligatoire": False},
                    {"id": "data_manager_rid", "label": "DATA MANAGER - RID", "type": "text", "obligatoire": False},
                    
                    {"id": "compteur_1_ref", "label": "COMPTEUR N°1 - Référence", "type": "text", "obligatoire": False},
                    {"id": "compteur_1_acces", "label": "COMPTEUR N°1 - Accès", "type": "boolean", "obligatoire": False},
                    {"id": "compteur_1_ip", "label": "COMPTEUR N°1 - IP", "type": "text", "obligatoire": False},
                    {"id": "compteur_1_mdp", "label": "COMPTEUR N°1 - Mot de passe", "type": "text", "obligatoire": False},
                    {"id": "compteur_1_serie", "label": "COMPTEUR N°1 - N° Série", "type": "text", "obligatoire": False},
                    
                    {"id": "ecran_deporte_ref", "label": "ECRAN DEPORTE - Référence", "type": "text", "obligatoire": False},
                    {"id": "ecran_deporte_acces", "label": "ECRAN DEPORTE - Accès", "type": "boolean", "obligatoire": False},
                    {"id": "ecran_deporte_ip", "label": "ECRAN DEPORTE - IP", "type": "text", "obligatoire": False},
                    {"id": "ecran_deporte_mdp", "label": "ECRAN DEPORTE - Mot de passe", "type": "text", "obligatoire": False},
                    {"id": "ecran_deporte_serie", "label": "ECRAN DEPORTE - N° Série", "type": "text", "obligatoire": False}
                ]
            }
        }
    },
    
    FicheType.ELECTRICIENS: {
        "nom": "Fiche de Contrôle Électriciens",
        "description": "Fiche de contrôle pour les travaux électriques",
        "sections": {
            "en_tete": {
                "nom": "Procès Verbal",
                "champs": [
                    {"id": "num_chantier", "label": "N° de chantier", "type": "text", "obligatoire": True},
                    {"id": "date", "label": "Date", "type": "date", "obligatoire": False}
                ]
            },
            "reception_pose": {
                "nom": "Réception Pose Centrale",
                "champs": [
                    {"id": "pose_reception_sans_reserve", "label": "Réception sans réserve", "type": "boolean", "obligatoire": True},
                    {"id": "pose_nature_reserves", "label": "Nature des réserves (pose)", "type": "textarea", "obligatoire": False}
                ]
            },
            "reception_raccordement": {
                "nom": "Réception Raccordement",
                "champs": [
                    {"id": "raccordement_reception_sans_reserve", "label": "Réception sans réserve", "type": "boolean", "obligatoire": True},
                    {"id": "raccordement_nature_reserves", "label": "Nature des réserves (raccordement)", "type": "textarea", "obligatoire": False}
                ]
            },
            "mesures_tensions": {
                "nom": "Mesure des tensions des chaînes DC",
                "champs": [
                    {"id": "mesures_effectuees", "label": "Mesures effectuées", "type": "boolean", "obligatoire": True},
                    {"id": "remarques_mesures", "label": "Remarques sur les mesures", "type": "textarea", "obligatoire": False}
                ]
            }
        }
    },
    
    FicheType.POSEURS: {
        "nom": "Fiche de Contrôle Poseurs",
        "description": "Fiche de contrôle pour les travaux de pose",
        "sections": {
            "informations_projet": {
                "nom": "Informations Projet",
                "champs": [
                    {"id": "nom_dossier", "label": "Nom du Dossier", "type": "text", "obligatoire": True},
                    {"id": "num_chantier", "label": "Numéro du chantier", "type": "text", "obligatoire": True},
                    {"id": "semaine_pose", "label": "Semaine de Pose", "type": "text", "obligatoire": True},
                    {"id": "nom_client", "label": "Nom du client", "type": "text", "obligatoire": True},
                    {"id": "telephone", "label": "Numéro de téléphone", "type": "text", "obligatoire": False},
                    {"id": "adresse_projet", "label": "Adresse du projet", "type": "text", "obligatoire": True},
                    {"id": "commercial", "label": "Commercial", "type": "text", "obligatoire": False},
                    {"id": "charge_etudes", "label": "Chargé d'études", "type": "text", "obligatoire": False},
                    {"id": "conducteur_travaux", "label": "Conducteur de travaux", "type": "text", "obligatoire": False}
                ]
            },
            "type_installation": {
                "nom": "Type d'Installation",
                "champs": [
                    {"id": "vente_totale", "label": "Vente totale", "type": "boolean", "obligatoire": True},
                    {"id": "vente_surplus", "label": "Vente de surplus", "type": "boolean", "obligatoire": True},
                    {"id": "autoconsommation", "label": "Autoconsommation", "type": "boolean", "obligatoire": True},
                    {"id": "option_shelter", "label": "Option Shelter", "type": "boolean", "obligatoire": False}
                ]
            },
            "pochette_documents": {
                "nom": "Pochette Documents",
                "type": "checklist",
                "champs": [
                    {"id": "plan_prevention", "label": "Plan de prévention / PPSPL", "type": "select", "options": ["VALIDE", "NA"], "obligatoire": True},
                    {"id": "schemas_unifilaire", "label": "Schémas unifilaire", "type": "select", "options": ["VALIDE", "NA"], "obligatoire": True},
                    {"id": "carnet_plan", "label": "Carnet de plan", "type": "select", "options": ["VALIDE", "NA"], "obligatoire": True},
                    {"id": "nomenclature", "label": "Nomenclature", "type": "select", "options": ["VALIDE", "NA"], "obligatoire": True},
                    {"id": "photos_chantier", "label": "Photos vitrines chantiers", "type": "select", "options": ["VALIDE", "NA"], "obligatoire": False},
                    {"id": "pv_reception", "label": "Procès verbal de réception de travaux", "type": "select", "options": ["VALIDE", "NA"], "obligatoire": True},
                    {"id": "fiche_fin_chantier", "label": "Fiche de fin de chantier", "type": "select", "options": ["VALIDE", "NA"], "obligatoire": True}
                ]
            },
            "configuration": {
                "nom": "Configuration du chantier",
                "champs": [
                    {"id": "puissance_installation", "label": "Puissance installation (kWc)", "type": "text", "obligatoire": True},
                    {"id": "panneaux", "label": "Panneaux (nombre x modèle)", "type": "text", "obligatoire": True},
                    {"id": "systeme_integration", "label": "Système d'intégration", "type": "text", "obligatoire": True},
                    {"id": "onduleur", "label": "Onduleur(s)", "type": "text", "obligatoire": True}
                ]
            },
            "reception": {
                "nom": "Réception des Travaux",
                "champs": [
                    {"id": "pose_reception_sans_reserve", "label": "Pose - Réception sans réserve", "type": "boolean", "obligatoire": True},
                    {"id": "pose_nature_reserves", "label": "Pose - Nature des réserves", "type": "textarea", "obligatoire": False},
                    {"id": "raccordement_reception_sans_reserve", "label": "Raccordement - Réception sans réserve", "type": "boolean", "obligatoire": True},
                    {"id": "raccordement_nature_reserves", "label": "Raccordement - Nature des réserves", "type": "textarea", "obligatoire": False},
                    {"id": "date_signature", "label": "Date de signature", "type": "date", "obligatoire": True},
                    {"id": "lieu", "label": "Fait à", "type": "text", "obligatoire": False}
                ]
            },
            "remarques": {
                "nom": "Remarques",
                "champs": [
                    {"id": "remarques_generales", "label": "Remarques générales", "type": "textarea", "obligatoire": False}
                ]
            }
        }
    }
}


def get_available_fiches() -> List[Dict]:
    """
    Retourne la liste des fiches disponibles.
    
    Returns:
        Liste de dicts avec id, nom et description
    """
    return [
        {
            "id": fiche_type.value,
            "nom": structure["nom"],
            "description": structure["description"]
        }
        for fiche_type, structure in FICHE_STRUCTURES.items()
    ]


def get_fiche_structure(fiche_type: FicheType) -> Dict:
    """
    Retourne la structure d'un type de fiche.
    
    Args:
        fiche_type: Type de fiche
        
    Returns:
        Structure de la fiche
    """
    return FICHE_STRUCTURES.get(fiche_type)


def create_empty_fiche(fiche_type: FicheType) -> Dict:
    """
    Crée une structure de fiche vide pour un type donné.
    
    Args:
        fiche_type: Type de fiche
        
    Returns:
        Structure vide avec tous les champs à None
    """
    structure = get_fiche_structure(fiche_type)
    if not structure:
        raise ValueError(f"Type de fiche inconnu: {fiche_type}")
    
    fiche = {
        "type": fiche_type.value,
        "nom": structure["nom"]
    }
    
    # Créer les sections vides
    for section_id, section_data in structure["sections"].items():
        if "champs" in section_data:
            # Section avec champs définis
            fiche[section_id] = {
                champ["id"]: None 
                for champ in section_data["champs"]
            }
        elif "lignes" in section_data:
            # Section tableau (comme défauts)
            fiche[section_id] = [
                {
                    "localisation": ligne["localisation"],
                    **{champ: None for champ in ligne["champs"]}
                }
                for ligne in section_data["lignes"]
            ]
    
    return fiche


def get_fiche_questions(fiche_type: FicheType) -> List[str]:
    """
    Génère la liste des questions à poser pour un type de fiche.
    
    Args:
        fiche_type: Type de fiche
        
    Returns:
        Liste de questions
    """
    structure = get_fiche_structure(fiche_type)
    questions = []
    
    for section_id, section_data in structure["sections"].items():
        if "champs" in section_data:
            for champ in section_data["champs"]:
                if champ["obligatoire"]:
                    questions.append(f"{champ['label']} ?")
    
    return questions


def format_fiche_type_list() -> str:
    """
    Formate la liste des types de fiches pour l'affichage.
    
    Returns:
        Texte formaté avec la liste des fiches
    """
    fiches = get_available_fiches()
    
    text = "**Types de fiches disponibles :**\n\n"
    for i, fiche in enumerate(fiches, 1):
        text += f"{i}. **{fiche['nom']}**\n"
        text += f"   _{fiche['description']}_\n\n"
    
    return text
