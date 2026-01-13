"""
Script de validation de l'installation et configuration du système NER + RAG

Ce script vérifie:
1. Les dépendances Python
2. Les variables d'environnement
3. La connexion à Azure OpenAI
4. Les fichiers OCR disponibles
5. Le fonctionnement de base du NER
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple

# Couleurs pour le terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Affiche un en-tête"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")


def print_success(text: str):
    """Affiche un message de succès"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    """Affiche un message d'erreur"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str):
    """Affiche un avertissement"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text: str):
    """Affiche une information"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


def check_python_version() -> bool:
    """Vérifie la version de Python"""
    print_info("Vérification de la version Python...")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (version 3.8+ requise)")
        return False


def check_dependencies() -> Tuple[bool, List[str]]:
    """Vérifie les dépendances Python"""
    print_info("Vérification des dépendances...")
    
    required_packages = [
        ("openai", "Azure OpenAI client"),
        ("dotenv", "Gestion des variables d'environnement"),
        ("pathlib", "Manipulation de chemins (built-in)"),
    ]
    
    missing = []
    for package, description in required_packages:
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print_success(f"{package}: {description}")
        except ImportError:
            print_error(f"{package}: {description} - NON INSTALLÉ")
            missing.append(package)
    
    return len(missing) == 0, missing


def check_env_variables() -> bool:
    """Vérifie les variables d'environnement"""
    print_info("Vérification des variables d'environnement...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    all_ok = True
    
    if api_key:
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        print_success(f"AZURE_OPENAI_API_KEY: {masked_key}")
    else:
        print_error("AZURE_OPENAI_API_KEY: NON DÉFINIE")
        all_ok = False
    
    if endpoint:
        print_success(f"AZURE_OPENAI_ENDPOINT: {endpoint}")
    else:
        print_error("AZURE_OPENAI_ENDPOINT: NON DÉFINIE")
        all_ok = False
    
    if not all_ok:
        print_warning("Créez un fichier .env à la racine du projet avec ces variables")
    
    return all_ok


def check_azure_connection() -> bool:
    """Vérifie la connexion à Azure OpenAI"""
    print_info("Vérification de la connexion à Azure OpenAI...")
    
    try:
        from openai import AzureOpenAI
        from dotenv import load_dotenv
        
        load_dotenv()
        
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        # Test simple
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print_success("Connexion à Azure OpenAI établie")
        print_success(f"Modèle 'gpt-4o' accessible")
        return True
        
    except Exception as e:
        print_error(f"Erreur de connexion: {str(e)[:200]}")
        return False


def check_ocr_files() -> Tuple[bool, List[Path]]:
    """Vérifie la présence de fichiers OCR"""
    print_info("Vérification des fichiers OCR...")
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    ocr_dir = project_root / "data" / "ocr_results"
    
    if not ocr_dir.exists():
        print_error(f"Répertoire OCR non trouvé: {ocr_dir}")
        return False, []
    
    # Trouver les fichiers de défauts
    defaut_files = list(ocr_dir.glob("*DEFAUT*_ocr.txt"))
    
    if defaut_files:
        print_success(f"Répertoire OCR: {ocr_dir}")
        print_success(f"{len(defaut_files)} fichier(s) de défauts trouvé(s):")
        for f in defaut_files:
            print(f"   - {f.name}")
        return True, defaut_files
    else:
        print_warning(f"Aucun fichier de défauts trouvé dans {ocr_dir}")
        print_warning("Les fichiers doivent contenir 'DEFAUT' dans leur nom et finir par '_ocr.txt'")
        return False, []


def check_modules() -> bool:
    """Vérifie que les modules NER et RAG sont importables"""
    print_info("Vérification des modules NER et RAG...")
    
    try:
        from ner_defaut_documents import extract_entities_from_defaut_document
        print_success("Module NER: ner_defaut_documents.py")
    except ImportError as e:
        print_error(f"Module NER non trouvé: {e}")
        return False
    
    try:
        from rag_integration_ner import DefautDocumentRAG
        print_success("Module RAG: rag_integration_ner.py")
    except ImportError as e:
        print_error(f"Module RAG non trouvé: {e}")
        return False
    
    return True


def test_basic_extraction(ocr_files: List[Path]) -> bool:
    """Test basique d'extraction NER"""
    if not ocr_files:
        return False
    
    print_info("Test d'extraction NER sur un document...")
    
    try:
        from ner_defaut_documents import extract_entities_from_defaut_document
        
        # Prendre le premier fichier
        test_file = ocr_files[0]
        print_info(f"Fichier de test: {test_file.name}")
        
        with open(test_file, 'r', encoding='utf-8') as f:
            ocr_text = f.read()
        
        # Extraire les entités
        entities = extract_entities_from_defaut_document(ocr_text)
        
        # Vérifications
        if not entities:
            print_error("Aucune entité extraite")
            return False
        
        if "mise_en_service" not in entities:
            print_error("Section 'mise_en_service' manquante")
            return False
        
        if "tableau_defauts" not in entities:
            print_error("Section 'tableau_defauts' manquante")
            return False
        
        print_success("Extraction NER réussie")
        
        # Afficher quelques statistiques
        mes = entities.get("mise_en_service", {})
        champs_mes = sum(1 for v in mes.values() if v)
        print_info(f"Mise en service: {champs_mes}/{len(mes)} champs remplis")
        
        tableau = entities.get("tableau_defauts", [])
        print_info(f"Tableau: {len(tableau)} lignes")
        
        champs_manquants = entities.get("champs_manquants", [])
        if champs_manquants:
            print_warning(f"{len(champs_manquants)} champ(s) manquant(s)")
        else:
            print_success("Tous les champs sont remplis")
        
        return True
        
    except Exception as e:
        print_error(f"Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Fonction principale de validation"""
    print_header("🔍 VALIDATION DU SYSTÈME NER + RAG")
    
    results = {}
    
    # 1. Version Python
    print_header("1. Version Python")
    results["python"] = check_python_version()
    
    # 2. Dépendances
    print_header("2. Dépendances Python")
    results["dependencies"], missing = check_dependencies()
    
    if not results["dependencies"]:
        print_warning("\nPour installer les dépendances manquantes:")
        print(f"pip install {' '.join(missing)}")
    
    # 3. Variables d'environnement
    print_header("3. Variables d'environnement")
    results["env"] = check_env_variables()
    
    # 4. Connexion Azure
    print_header("4. Connexion Azure OpenAI")
    if results["env"]:
        results["azure"] = check_azure_connection()
    else:
        print_warning("Test ignoré (variables d'environnement manquantes)")
        results["azure"] = False
    
    # 5. Fichiers OCR
    print_header("5. Fichiers OCR")
    results["ocr_files"], ocr_files = check_ocr_files()
    
    # 6. Modules
    print_header("6. Modules NER et RAG")
    results["modules"] = check_modules()
    
    # 7. Test d'extraction
    print_header("7. Test d'extraction")
    if all([results["dependencies"], results["env"], results["azure"], 
            results["ocr_files"], results["modules"]]):
        results["extraction"] = test_basic_extraction(ocr_files)
    else:
        print_warning("Test ignoré (prérequis non satisfaits)")
        results["extraction"] = False
    
    # Résumé final
    print_header("📊 RÉSUMÉ")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for name, status in results.items():
        if status:
            print_success(f"{name.upper()}")
        else:
            print_error(f"{name.upper()}")
    
    print(f"\n{Colors.BOLD}Résultat: {passed}/{total} tests passés{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SYSTÈME OPÉRATIONNEL{Colors.END}")
        print(f"\n{Colors.BLUE}Vous pouvez maintenant utiliser:{Colors.END}")
        print("   - python src/ner_defaut_documents.py")
        print("   - python src/rag_integration_ner.py --interactive")
        print("   - python examples/exemple_simple_ner_rag.py")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ CONFIGURATION INCOMPLÈTE{Colors.END}")
        print(f"\n{Colors.YELLOW}Corrigez les erreurs ci-dessus avant de continuer{Colors.END}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
