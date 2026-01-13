# 🚀 Démarrage Rapide - Application Diag IA

## ⚡ Lancer l'application en 30 secondes

```bash
# 1. Aller dans le dossier du projet
cd /home/glegeai/diag-emeraude-solaire

# 2. Activer l'environnement virtuel
source venv/bin/activate  # ou source .venv/bin/activate

# 3. Lancer l'application !
streamlit run src/app.py
```

L'application s'ouvrira automatiquement dans votre navigateur sur `http://localhost:8501`

---

## 🎯 Utiliser le Mode Fiches

### Étape 1 : Activer le mode

Dans la **sidebar** (barre latérale à gauche) :

```
┌─────────────────────────────┐
│ 📋 Mode Fiches              │
│                             │
│ [x] Activer le mode Fiches  │ ← Cochez cette case
│                             │
└─────────────────────────────┘
```

### Étape 2 : Choisir le type de fiche

Vous verrez **4 boutons** pour choisir le type de fiche :

```
┌─────────────────────────────┐
│ [Fiche de Défauts]          │ ← Anomalies et problèmes
│ [Fiche de Mise en Service]  │ ← Documentation MES complète
│ [Fiche de Contrôle]         │ ← Contrôles périodiques
│ [Fiche de Maintenance]      │ ← Interventions maintenance
└─────────────────────────────┘
```

**Cliquez** sur le type voulu !

### Étape 3 : Remplir naturellement

Parlez naturellement avec le chatbot !

```
🤖 : Quel est le nom du chantier ?

👤 : Le chantier s'appelle "GAEC DE VAULEON", 
     l'AO est AO-2022-0456 et le technicien 
     c'est F.A. Loctiere

🤖 : Excellent ! J'ai bien noté :
     - Chantier : GAEC DE VAULEON ✅
     - AO : AO-2022-0456 ✅
     - Technicien : F.A. Loctiere ✅
     
     Et la date d'intervention ?
```

### Étape 4 : Suivre la progression

Dans la sidebar, une barre montre votre avancement :

```
[████████░░] 75%
Complétion: 75%
```

### Étape 5 : Exporter

Quand vous atteignez 100% :

```
[💾 Exporter la fiche] ← Cliquez !
```

→ Téléchargez votre fichier JSON structuré

---

## 💡 Astuces

### ✅ Donnez plusieurs infos à la fois

Le chatbot extrait automatiquement toutes les informations :

> "Le chantier est GAEC DE VAULEON, l'AO est AO-2022-0456, le technicien est F.A. Loctiere et la date c'est le 03/06/2021"

### ✅ Utilisez "RAS" pour "Rien à Signaler"

> "Pour la partie DC, c'est RAS"

### ✅ Mode vocal 🎤

Cliquez sur le micro et dictez vos réponses ! Le chatbot transcrit ET extrait automatiquement.

---

## 🎨 Détection automatique du type

Vous pouvez aussi simplement **dire le type** :

```
👤 : Je veux remplir une fiche de maintenance

[Le système détecte et initialise automatiquement]

🤖 : Fiche de Maintenance activée ! 
     Quel est le site concerné ?
```

**Mots-clés reconnus :**
- "défaut" / "anomalie" → Fiche de Défauts
- "mes" / "mise en service" → Fiche de MES  
- "contrôle" / "vérification" → Fiche de Contrôle
- "maintenance" / "intervention" → Fiche de Maintenance

---

## 🧪 Test rapide (1 minute)

```bash
streamlit run src/app.py
```

Puis :
1. Sidebar → Activer mode
2. Cliquer "Nouvelle fiche"
3. Taper : "Le chantier s'appelle Test et l'AO est AO-001"
4. Observer la progression ! ⬆️

---

## ❌ Résolution de problèmes

### Le mode ne démarre pas ?

1. **Rafraîchir la page** (F5)
2. **Activer le mode** dans la sidebar ☑️
3. **Cliquer sur un bouton de type** (ne pas juste écrire)
4. **Attendre** que le chatbot démarre
5. **Répondre** aux questions

### Vérifier que tout est OK

```bash
cd /home/glegeai/diag-emeraude-solaire
source venv/bin/activate
python src/validate_ner_setup.py
```

Résultat attendu : **✅ SYSTÈME OPÉRATIONNEL**

---

## 📊 Ce qui est rempli automatiquement

### Fiche de Défauts
- Informations de mise en service (6 champs)
- Tableau des défauts par section (DC, AC, Communication, etc.)

### Fiche de MES
- Informations générales du site
- Vérifications et tests de conformité
- Remarques et observations

### Fiche de Contrôle
- Identification du site
- Points de contrôle détaillés
- État des équipements

### Fiche de Maintenance
- Informations d'intervention
- Opérations réalisées
- Pièces changées

---

## 🎯 Workflow typique

1. **Lancer** → `streamlit run src/app.py`
2. **Activer** → Toggle dans sidebar
3. **Choisir** → Type de fiche
4. **Parler** → Conversation naturelle
5. **Suivre** → Barre de progression
6. **Vérifier** → Détails complets
7. **Exporter** → Télécharger JSON
8. **Utiliser** → Importer dans votre système

⏱️ **Temps total : 3-5 minutes** au lieu de 15-20 !

---

## 📚 Documentation complète

- **Guide utilisateur** : `docs/02_GUIDE_UTILISATEUR.md`
- **Guide NER+RAG** : `docs/03_GUIDE_NER_RAG.md`
- **Architecture technique** : `docs/04_ARCHITECTURE_TECHNIQUE.md`

---

## 🎊 C'est tout !

**Simple, rapide, efficace.**

Lancez l'app et testez dès maintenant ! 🚀
