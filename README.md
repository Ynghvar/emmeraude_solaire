# Diag IA - Emeraude Solaire

Application de diagIA pour Emeraude Solaire dont le sujet est la réalisation de comptes-rendus vocaux guidés.

## 📋 Description

Cette application web permet de réaliser des diagnostics assistés par IA avec support vocal. L'utilisateur peut interagir avec l'IA via différents modes d'entrée (texte, fichier audio, enregistrement vocal) pour créer des comptes-rendus de diagnostic de manière guidée et conversationnelle.

## 🎯 Fonctionnalités

### UC 13 : CR Vocal Guidé

- 💬 **Chat conversationnel** : Interaction naturelle avec l'IA pour guider la création du compte-rendu
- 🎤 **Entrée vocale** : Enregistrement direct de la voix pour dicter les informations
- 📁 **Import audio** : Upload de fichiers audio (.wav, .mp3, .m4a) pour transcription
- ✍️ **Saisie texte** : Mode classique de saisie textuelle
- 🔊 **Synthèse vocale** : Réponses de l'IA lues automatiquement à voix haute
- 📝 **Historique de conversation** : Conservation du contexte pour des échanges cohérents

### 🆕 NER + RAG : Extraction et Complétion de Fiches de Défauts

- 🤖 **NER Hybride** : Extraction intelligente d'entités avec Azure GPT-4o
- 📋 **Analyse structurée** : Identification automatique des champs manquants
- 💬 **RAG conversationnel** : Dialogue guidé pour compléter les documents
- 🔍 **Détection d'erreurs OCR** : Correction automatique des erreurs courantes
- 📊 **Statistiques et qualité** : Évaluation de la complétude des documents
- 💾 **Export JSON** : Sauvegarde des données structurées

## 🛠️ Technologies utilisées

- **Streamlit** : Interface web interactive
- **OpenAI Whisper** : Transcription audio en texte
- **Azure OpenAI (GPT-4o)** : Modèle de langage pour les réponses intelligentes
- **Edge-TTS** : Synthèse vocale pour les réponses audio
- **PyTorch** : Backend pour Whisper

## 📦 Prérequis

- Python 3.8+
- ffmpeg (pour le traitement audio)
- Compte Azure OpenAI avec clé API et endpoint

## 🚀 Installation

1. **Cloner le dépôt** (si applicable) ou naviguer dans le répertoire du projet

2. **Créer un environnement virtuel** :
```bash
python -m venv venv
# ou
python -m venv .venv
```

3. **Activer l'environnement virtuel** :
```bash
source venv/bin/activate  # Linux/Mac
# ou
source .venv/bin/activate
```

4. **Installer les dépendances** :
```bash
pip install -r requirements.txt
```

5. **Installer ffmpeg** :
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg

# macOS
brew install ffmpeg

# Windows
# Télécharger depuis https://ffmpeg.org/download.html
```

## ⚙️ Configuration

Créer un fichier `.env` à la racine du projet avec les variables suivantes :

```env
AZURE_OPENAI_API_KEY = "votre_clé_api_azure"
AZURE_OPENAI_ENDPOINT = "https://votre-endpoint.openai.azure.com/"
MISTRAL_OCR_URL = "https://votre-endpoint.mistral.com"
```

## 🎮 Utilisation

### Application Streamlit - Chat Vocal

Lancer l'application Streamlit :

```bash
# Penser à activer l'environnement virtuel d'abord
source venv/bin/activate  # ou source .venv/bin/activate

streamlit run src/app.py
```

L'application s'ouvrira automatiquement dans votre navigateur (généralement sur `http://localhost:8501`).

### NER + RAG - Extraction de Fiches de Défauts

#### Extraction simple d'un document

```bash
# Activer l'environnement virtuel
source venv/bin/activate  # ou source .venv/bin/activate

# Extraire les entités d'une fiche de défauts
python src/ner_defaut_documents.py "data/ocr_results/VOTRE_FICHIER_ocr.txt"
```

#### Traitement batch de tous les documents

```bash
# Traiter tous les fichiers de défauts dans data/ocr_results/
python src/ner_defaut_documents.py
```

#### Mode interactif RAG

```bash
# Lancer l'assistant conversationnel pour compléter un document
python src/rag_integration_ner.py --interactive
```

#### Exemples guidés

```bash
# Lancer les exemples interactifs
python examples/exemple_simple_ner_rag.py
```

📖 **Documentation complète** : Voir les guides dans `docs/` pour plus de détails

## 📚 Documentation

Le projet dispose d'une documentation complète et consolidée :

- **[01_DEMARRAGE_RAPIDE.md](docs/01_DEMARRAGE_RAPIDE.md)** - Démarrer en 30 secondes ⚡
- **[02_GUIDE_UTILISATEUR.md](docs/02_GUIDE_UTILISATEUR.md)** - Guide utilisateur complet 📖
- **[03_GUIDE_NER_RAG.md](docs/03_GUIDE_NER_RAG.md)** - Guide technique NER + RAG 🤖
- **[04_ARCHITECTURE_TECHNIQUE.md](docs/04_ARCHITECTURE_TECHNIQUE.md)** - Architecture et développement 🏗️
- **[05_HISTORIQUE_CHANGEMENTS.md](docs/05_HISTORIQUE_CHANGEMENTS.md)** - Historique du projet 📜

---

## 📝 Notes

- L'application nécessite une connexion internet pour accéder à l'API Azure OpenAI
- Les fichiers audio temporaires sont automatiquement nettoyés après traitement
- Le modèle Whisper est chargé une seule fois au démarrage pour optimiser les performances