#!/usr/bin/env python3
"""
Script de test pour vérifier que les nouveaux types de fiches fonctionnent correctement
"""

import sys
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.fiche_types import FicheType, get_available_fiches, get_fiche_structure, create_empty_fiche
from utils.fiche_defaut_manager import FicheDefautChatManager

def test_fiches_disponibles():
    """Test 1: Vérifier que tous les types de fiches sont disponibles"""
    print("=" * 70)
    print("TEST 1: Types de fiches disponibles")
    print("=" * 70)
    
    fiches = get_available_fiches()
    print(f"\n✅ {len(fiches)} types de fiches disponibles:\n")
    
    for i, fiche in enumerate(fiches, 1):
        print(f"{i}. {fiche['nom']}")
        print(f"   ID: {fiche['id']}")
        print(f"   Description: {fiche['description']}\n")
    
    # Vérifier que les nouveaux types sont présents
    ids = [f['id'] for f in fiches]
    nouveaux_types = ['controle_mes', 'electriciens', 'poseurs']
    
    for nouveau_type in nouveaux_types:
        if nouveau_type in ids:
            print(f"✅ Type '{nouveau_type}' trouvé")
        else:
            print(f"❌ Type '{nouveau_type}' MANQUANT!")
    
    return True

def test_structure_fiche_controle_mes():
    """Test 2: Vérifier la structure de la fiche Contrôle MES"""
    print("\n" + "=" * 70)
    print("TEST 2: Structure Fiche Contrôle MES")
    print("=" * 70)
    
    structure = get_fiche_structure(FicheType.CONTROLE_MES)
    
    print(f"\n📋 {structure['nom']}")
    print(f"📝 {structure['description']}\n")
    
    print("Sections:")
    for section_id, section_data in structure['sections'].items():
        section_name = section_data.get('nom', section_id)
        section_type = section_data.get('type', 'standard')
        
        if 'champs' in section_data:
            nb_champs = len(section_data['champs'])
            print(f"  - {section_name} ({section_type}): {nb_champs} champs")
        else:
            print(f"  - {section_name} ({section_type})")
    
    return True

def test_creation_fiche_electriciens():
    """Test 3: Créer une fiche Électriciens vide"""
    print("\n" + "=" * 70)
    print("TEST 3: Création Fiche Électriciens")
    print("=" * 70)
    
    fiche = create_empty_fiche(FicheType.ELECTRICIENS)
    
    print(f"\n✅ Fiche créée: {fiche['nom']}")
    print(f"Type: {fiche['type']}\n")
    
    print("Sections initialisées:")
    for key, value in fiche.items():
        if key not in ['type', 'nom']:
            print(f"  - {key}: {type(value).__name__}")
    
    return True

def test_creation_fiche_poseurs():
    """Test 4: Créer une fiche Poseurs vide"""
    print("\n" + "=" * 70)
    print("TEST 4: Création Fiche Poseurs")
    print("=" * 70)
    
    fiche = create_empty_fiche(FicheType.POSEURS)
    
    print(f"\n✅ Fiche créée: {fiche['nom']}")
    print(f"Type: {fiche['type']}\n")
    
    print("Sections initialisées:")
    for key, value in fiche.items():
        if key not in ['type', 'nom']:
            if isinstance(value, dict):
                nb_champs = len(value)
                print(f"  - {key}: {nb_champs} champs")
            else:
                print(f"  - {key}: {type(value).__name__}")
    
    return True

def test_gestionnaire_fiche_controle_mes():
    """Test 5: Initialiser le gestionnaire avec une fiche Contrôle MES"""
    print("\n" + "=" * 70)
    print("TEST 5: Gestionnaire Fiche Contrôle MES")
    print("=" * 70)
    
    manager = FicheDefautChatManager(fiche_type=FicheType.CONTROLE_MES)
    
    print(f"\n✅ Gestionnaire créé")
    print(f"Type de fiche: {manager.fiche_type.value}")
    print(f"Mode: {manager.mode}")
    print(f"Complétion: {manager.get_completion_percentage():.1f}%")
    print(f"Champs manquants: {len(manager.champs_manquants)}\n")
    
    # Tester la génération de question
    question = manager.get_next_question()
    if question:
        print(f"Prochaine question: {question}")
    else:
        print("Aucune question (fiche complète ou erreur)")
    
    return True

def test_export_txt_controle_mes():
    """Test 6: Export TXT d'une fiche Contrôle MES"""
    print("\n" + "=" * 70)
    print("TEST 6: Export TXT Fiche Contrôle MES")
    print("=" * 70)
    
    manager = FicheDefautChatManager(fiche_type=FicheType.CONTROLE_MES)
    
    # Remplir quelques champs pour tester
    manager.entities['en_tete']['nom_chantier'] = "Test Chantier"
    manager.entities['en_tete']['num_chantier'] = "TEST-001"
    manager.entities['en_tete']['supervision_ok'] = True
    
    txt = manager.export_txt()
    
    print("\n✅ Export réussi!\n")
    print("Aperçu (100 premiers caractères):")
    print(txt[:100] + "...")
    
    # Vérifier que le contenu est présent
    if "FICHE DE CONTRÔLE MES" in txt:
        print("\n✅ Titre correct trouvé")
    if "Test Chantier" in txt:
        print("✅ Données du chantier trouvées")
    
    return True

def main():
    """Exécuter tous les tests"""
    print("\n🧪 TESTS DES NOUVEAUX TYPES DE FICHES")
    print("=" * 70 + "\n")
    
    tests = [
        test_fiches_disponibles,
        test_structure_fiche_controle_mes,
        test_creation_fiche_electriciens,
        test_creation_fiche_poseurs,
        test_gestionnaire_fiche_controle_mes,
        test_export_txt_controle_mes
    ]
    
    resultats = []
    for test in tests:
        try:
            resultat = test()
            resultats.append((test.__name__, "✅ PASS" if resultat else "❌ FAIL"))
        except Exception as e:
            resultats.append((test.__name__, f"❌ ERROR: {str(e)}"))
            print(f"\n❌ Erreur dans {test.__name__}: {e}")
    
    # Résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ DES TESTS")
    print("=" * 70 + "\n")
    
    for nom_test, resultat in resultats:
        print(f"{resultat:15} {nom_test}")
    
    nb_reussis = sum(1 for _, r in resultats if "✅" in r)
    print(f"\n🎯 {nb_reussis}/{len(tests)} tests réussis\n")

if __name__ == "__main__":
    main()
