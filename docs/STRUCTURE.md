# Structure du Projet

## 📁 Organisation des Fichiers

```
diag-emeraude-solaire/
│
├── src/                          # 🎯 Code source de l'application
│   ├── app.py                    # Application Streamlit principale
│   └── utils/                    # Modules utilitaires
│       ├── LLM.py               # Interface avec les modèles LLM
│       ├── fiche_types.py       # Définition des types de fiches
│       ├── fiche_defaut_manager.py  # Gestionnaire de fiches
│       └── ner_defaut_documents.py  # Extraction NER des documents
│
├── examples/                     # 📝 Tests et exemples
│   ├── ner_defaut_documents.py  # Exemple NER
│   ├── exemple_simple_ner_rag.py
│   ├── test_azure_models.py
│   ├── test_nouveaux_types_fiches.py
│   ├── validate_ner_setup.py
│   └── ocr_pdfs.py
│
├── docs/                         # 📚 Documentation
│   ├── 01_DEMARRAGE_RAPIDE.md    # Guide de démarrage rapide
│   ├── 02_GUIDE_UTILISATEUR.md   # Guide utilisateur complet
│   ├── 03_GUIDE_NER_RAG.md       # Guide NER + RAG
│   ├── 04_ARCHITECTURE_TECHNIQUE.md  # Architecture technique
│   ├── 05_HISTORIQUE_CHANGEMENTS.md  # Historique des changements
│   ├── STRUCTURE.md              # Ce fichier
│   └── ARCHIVE/                  # Documentation archivée
│
├── notebooks/                    # 📓 Jupyter notebooks
│   └── demo_ner_rag.ipynb
│
├── data/                         # 💾 Données
│   ├── ocr_results/             # Résultats OCR
│   ├── *.pdf                    # Fichiers PDF source
│   └── *.xlsm                   # Fichiers Excel
│
├── por_maria/                    # 👩‍💻 Travaux de Maria
│
└── venv/                         # 🐍 Environnement virtuel Python
```

## 🎯 Règles d'Organisation

### `/src/utils/`
**Contient :** Tous les modules Python importés par `app.py`
- Modules réutilisables
- Classes et fonctions utilitaires
- Intégrations avec services externes

### `/examples/`
**Contient :** Tests, exemples et scripts de validation
- Scripts de test
- Exemples d'utilisation
- Scripts de validation et démonstration
- Pas importés par `app.py`

### `/docs/`
**Contient :** Documentation consolidée du projet (Décembre 2024)
- **01_DEMARRAGE_RAPIDE.md** : Guide de démarrage en 30 secondes
- **02_GUIDE_UTILISATEUR.md** : Guide utilisateur complet multi-fiches
- **03_GUIDE_NER_RAG.md** : Guide technique NER + RAG
- **04_ARCHITECTURE_TECHNIQUE.md** : Architecture et développement
- **05_HISTORIQUE_CHANGEMENTS.md** : Historique complet du projet
- **ARCHIVE/** : Ancienne documentation (référence historique)

### `/notebooks/`
**Contient :** Jupyter notebooks
- Expérimentations
- Analyses
- Démonstrations interactives

### `/data/`
**Contient :** Données et fichiers
- Résultats OCR
- PDFs source
- Fichiers Excel
- Données de test

## 🔧 Imports

### Dans `app.py`
```python
from utils.LLM import get_chat_response
from utils.fiche_defaut_manager import (
    FicheDefautChatManager,
    create_fiche_system_message,
    get_initial_fiche_message,
    detect_fiche_type_from_message
)
from utils.fiche_types import FicheType, get_fiche_structure
```

### Dans les modules utils
```python
# Imports relatifs au sein de utils/
from utils.ner_defaut_documents import extract_entities_from_defaut_document
from utils.fiche_types import FicheType, get_fiche_structure
```

## 🚀 Démarrage

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer l'application
streamlit run src/app.py

# Lancer un exemple
python examples/exemple_simple_ner_rag.py

# Lancer les tests
python examples/test_nouveaux_types_fiches.py
```

## 📝 Notes

- Les fichiers `__pycache__/` sont automatiquement générés par Python
- Le dossier `venv/` n'est pas versionné (dans `.gitignore`)
- Les données sensibles sont dans `.env` (non versionné)

---

**Dernière mise à jour :** 17/12/2024 (Consolidation de la documentation)

