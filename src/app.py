import streamlit as st
import whisper
import tempfile
import os
import warnings
import subprocess
import asyncio
import edge_tts
import re
from pathlib import Path
from utils.LLM import get_chat_response
from utils.fiche_defaut_manager import (
    FicheDefautChatManager, 
    create_fiche_system_message, 
    get_initial_fiche_message,
    detect_fiche_type_from_message
)
from utils.fiche_types import FicheType, get_fiche_structure

# Filtrer l'avertissement FP16 sur CPU
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

# Fonction helper pour détecter et activer le mode fiche automatiquement
def auto_detect_and_activate_fiche_mode(user_message: str) -> bool:
    """
    Détecte si l'utilisateur demande à créer une fiche et active automatiquement le mode.
    
    Args:
        user_message: Message de l'utilisateur
        
    Returns:
        True si une fiche a été activée, False sinon
    """
    # Ne rien faire si le mode fiche est déjà actif
    if st.session_state.fiche_mode or st.session_state.fiche_manager:
        return False
    
    # Mots-clés pour détecter l'intention de créer une fiche
    keywords_fiche = [
        "créer une fiche", "creer une fiche", "nouvelle fiche", "remplir une fiche",
        "fiche défaut", "fiche defaut", "fiche mes", "fiche controle mes", "contrôle mes", "controle mes",
        "fiche électricien", "fiche electricien", "fiche poseur",
        "je veux créer", "je veux creer", "commencer une fiche"
    ]
    
    message_lower = user_message.lower()
    
    # Vérifier si un mot-clé est présent
    if any(keyword in message_lower for keyword in keywords_fiche):
        # Détecter le type de fiche demandé
        detected_type = detect_fiche_type_from_message(user_message)
        
        if detected_type:
            # Activer le mode fiche automatiquement
            st.session_state.fiche_mode = True
            st.session_state.fiche_manager = FicheDefautChatManager(fiche_type=detected_type)
            
            # Message de confirmation
            fiche_info = get_fiche_structure(detected_type)
            
            if fiche_info:
                confirmation_msg = f"✅ **Mode Fiche activé automatiquement !**\n\n"
                confirmation_msg += f"📋 Type de fiche : **{fiche_info['nom']}**\n\n"
                confirmation_msg += get_initial_fiche_message(st.session_state.fiche_manager)
                
                st.session_state.messages.append({"role": "assistant", "content": confirmation_msg})
                return True
            else:
                # Type détecté mais structure non trouvée, ne pas activer
                return False
    
    return False

# Vérification de ffmpeg
def check_ffmpeg():
    """Vérifie si ffmpeg est installé"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, 
                      check=True,
                      timeout=5)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False

# Configuration de la page
st.set_page_config(
    page_title="Chatbot IA Conversationnel",
    page_icon="💬",
    layout="wide"
)

# CSS personnalisé pour des boutons circulaires modernes
st.markdown("""
<style>
    /* Style pour les boutons circulaires */
    div.stButton > button {
        border-radius: 50%;
        width: 50px;
        height: 50px;
        padding: 0;
        font-size: 20px;
        background-color: transparent;
        border: none;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Style pour le bouton d'envoi (primary) */
    div.stButton > button[kind="primary"] {
        background-color: #ffffff;
        color: #000000;
        border-radius: 50%;
    }
    
    div.stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.1);
        border: none;
    }
    
    div.stButton > button[kind="primary"]:hover {
        background-color: #e0e0e0;
    }
    
    /* Style pour le champ de saisie */
    div.stTextInput > div > div > input {
        border-radius: 25px;
        padding: 12px 20px;
        background-color: transparent;
        border: 1px solid #3d3d3d;
        color: var(--text-color);
    }
    
    /* Supprimer l'espace au-dessus du chat */
    .block-container {
        padding-top: 2rem;
    }
    
    /* Marge pour les logos */
    [data-testid="stImage"] {
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Vérifier ffmpeg au démarrage
if not check_ffmpeg():
    st.error("""
    ⚠️ **ffmpeg n'est pas installé sur votre système**
    
    **Pour installer ffmpeg, exécutez dans votre terminal :**
    
    ```bash
    sudo apt-get update
    sudo apt-get install -y ffmpeg
    ```
    
    **Ou sur d'autres systèmes :**
    - **macOS** : `brew install ffmpeg`
    - **Windows** : Téléchargez depuis [ffmpeg.org](https://ffmpeg.org/download.html)
    
    Après l'installation, redémarrez l'application Streamlit.
    """)
    st.stop()

# Initialisation du modèle Whisper (une seule fois)
@st.cache_resource
def load_whisper_model():
    """Charge le modèle Whisper (base model pour un bon équilibre vitesse/qualité)"""
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return whisper.load_model("tiny", device=device)

# Initialisation de l'historique de conversation
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_played_message_index" not in st.session_state:
    st.session_state.last_played_message_index = -1

# Mode fiche de défauts
if "fiche_mode" not in st.session_state:
    st.session_state.fiche_mode = False
if "fiche_manager" not in st.session_state:
    st.session_state.fiche_manager = None

# Initialisation des variables de session pour les modes
if "input_mode" not in st.session_state:
    st.session_state.input_mode = "text"  # "text", "file", "record"
if "show_file_uploader" not in st.session_state:
    st.session_state.show_file_uploader = False
if "show_audio_recorder" not in st.session_state:
    st.session_state.show_audio_recorder = False
if "text_input_key" not in st.session_state:
    st.session_state.text_input_key = 0
if "audio_upload_key" not in st.session_state:
    st.session_state.audio_upload_key = 0
if "audio_recording_key" not in st.session_state:
    st.session_state.audio_recording_key = 0
if "pending_message" not in st.session_state:
    st.session_state.pending_message = None
if "should_process_message" not in st.session_state:
    st.session_state.should_process_message = False
if "text_to_speech_enabled" not in st.session_state:
    st.session_state.text_to_speech_enabled = True  # Activé par défaut

# Fonction callback pour l'envoi par Entrée
def on_text_input_change():
    """Appelé quand l'utilisateur appuie sur Entrée dans le champ de saisie"""
    current_input = st.session_state.get(f"text_input_{st.session_state.text_input_key}", "")
    if current_input and current_input.strip():
        st.session_state.pending_message = current_input.strip()
        st.session_state.should_process_message = True

# Fonction pour transcrire un fichier audio
def transcribe_audio(audio_path):
    """Transcrit un fichier audio en texte"""
    model = load_whisper_model()
    result = model.transcribe(audio_path)
    return result["text"]

# Fonction pour retirer les emojis du texte
def remove_emojis(text):
    """Supprime les emojis du texte"""
    # Pattern pour détecter les emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002600-\U000026FF"  # Miscellaneous Symbols
        "\U00002700-\U000027BF"  # Dingbats
        "]+", 
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def clean_text_for_speech(text):
    """
    Nettoie le texte pour la synthèse vocale en supprimant :
    - Les caractères de formatage Markdown (*, _, **, __, etc.)
    - Les guillemets spéciaux (" " « »)
    - Les crochets et parenthèses de liens Markdown
    - Les caractères spéciaux qui ne doivent pas être lus
    """
    # Supprimer les emojis d'abord
    text = remove_emojis(text)
    
    # Supprimer les blocs de code markdown (```...```)
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Supprimer les codes inline (`...`)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Supprimer les liens Markdown [texte](url) en gardant juste le texte
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Supprimer les images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
    
    # Supprimer les caractères de formatage gras/italique
    # ** ou __ pour gras
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    
    # * ou _ pour italique
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Supprimer les astérisques isolés qui restent
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'_+', '', text)
    
    # Remplacer les guillemets spéciaux par des guillemets simples (puis les supprimer)
    text = text.replace('"', '').replace('"', '')
    text = text.replace('«', '').replace('»', '')
    text = text.replace('"', '')
    
    # Supprimer les # pour les titres
    text = re.sub(r'#{1,6}\s+', '', text)
    
    # Supprimer les > pour les citations
    text = re.sub(r'^\s*>\s+', '', text, flags=re.MULTILINE)
    
    # Supprimer les - ou * en début de ligne (listes)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    
    # Supprimer les numéros de liste (1., 2., etc.)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Nettoyer les espaces multiples
    text = re.sub(r'\s+', ' ', text)
    
    # Nettoyer les sauts de ligne multiples
    text = re.sub(r'\n\s*\n', '\n', text)
    
    return text.strip()

# Fonction pour synthétiser le texte en audio
async def text_to_speech_async(text, output_path):
    """Convertit le texte en audio avec Edge TTS"""
    # Utiliser une voix française naturelle
    voice = "fr-FR-DeniseNeural"  # Voix féminine française
    # voice = "fr-FR-HenriNeural"  # Alternative : voix masculine française
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def text_to_speech(text):
    """Wrapper synchrone pour la synthèse vocale"""
    try:
        # Nettoyer le texte des emojis et caractères de formatage
        clean_text = clean_text_for_speech(text)
        
        if not clean_text:
            return None
        
        # Créer un fichier temporaire pour l'audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            output_path = tmp_file.name
        
        # Exécuter la synthèse vocale
        asyncio.run(text_to_speech_async(clean_text, output_path))
        
        return output_path
    except Exception as e:
        st.error(f"Erreur lors de la synthèse vocale: {str(e)}")
        return None

# En-tête avec titre et logos
col_title, col_spacer, col_logo1, col_logo2 = st.columns([3, 0.5, 0.5, 0.5])

with col_title:
    st.title("💬 Chatbot IA Conversationnel")
    st.markdown("Chattez avec l'IA en utilisant du texte, un fichier audio ou en enregistrant votre voix. L'IA identifiera le type de fiche ou vous pouvez la choisir manuellement et la remplira automatiquement. Donnez autant d'informations que possible pour que l'IA puisse remplir la fiche correctement ou laissez vous guider.")
    st.markdown("Pour commencer, veuillez envoyer un message de type 'Je veux créer une fiche de défaut' ou 'Je veux remplir une fiche controle poseur pour le projet XXX'.")
with col_logo1:
    try:
        st.image("img/Emmeraude.png", width=80)
    except:
        pass

with col_logo2:
    try:
        st.image("img/niji.png", width=80)
    except:
        pass

# Affichage de l'historique de conversation
chat_container = st.container()
with chat_container:
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Lire automatiquement la dernière réponse de l'assistant (si la synthèse vocale est activée)
            if (message["role"] == "assistant" and 
                idx == len(st.session_state.messages) - 1 and 
                idx > st.session_state.last_played_message_index and
                st.session_state.text_to_speech_enabled):
                
                with st.spinner("🔊 Génération de l'audio..."):
                    audio_path = text_to_speech(message["content"])
                    if audio_path:
                        # Lire l'audio automatiquement
                        with open(audio_path, "rb") as audio_file:
                            audio_bytes = audio_file.read()
                            st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                        
                        # Nettoyer le fichier temporaire
                        try:
                            os.unlink(audio_path)
                        except:
                            pass
                        
                        # Marquer ce message comme lu
                        st.session_state.last_played_message_index = idx

# Section pour les modes d'entrée
st.divider()

# Zone de saisie avec boutons
col1, col2, col3, col4 = st.columns([0.8, 3, 0.8, 0.8])

with col1:
    # Bouton pour attacher un fichier audio (trombone/+)
    if st.button("➕", help="Joindre un fichier audio", use_container_width=True):
        st.session_state.show_file_uploader = not st.session_state.show_file_uploader
        st.session_state.show_audio_recorder = False
        st.rerun()

with col2:
    # Zone de saisie texte
    user_text = st.text_input(
        "Message",
        placeholder="Poser une question",
        label_visibility="collapsed",
        key=f"text_input_{st.session_state.text_input_key}",
        on_change=on_text_input_change
    )

with col3:
    # Bouton micro pour enregistrer
    if st.button("🎤", help="Enregistrer un message audio", use_container_width=True):
        st.session_state.show_audio_recorder = not st.session_state.show_audio_recorder
        st.session_state.show_file_uploader = False
        st.rerun()

with col4:
    # Bouton envoyer
    send_text = st.button("▶", type="primary", help="Envoyer le message", use_container_width=True)

# Affichage conditionnel des zones de fichier et d'enregistrement
uploaded_file = None
audio_recording = None
send_audio_file = False
send_recording = False

if st.session_state.show_file_uploader:
    st.markdown("---")
    col_upload1, col_upload2, col_upload3 = st.columns([3, 0.8, 0.8])
    with col_upload1:
        uploaded_file = st.file_uploader(
            "Choisissez un fichier audio",
            type=['wav', 'mp3', 'm4a'],
            help="Formats supportés: .wav, .mp3, .m4a",
            key=f"audio_upload_{st.session_state.audio_upload_key}",
            label_visibility="collapsed"
        )
    with col_upload2:
        send_audio_file = st.button("▶", type="primary", help="Envoyer le fichier audio", use_container_width=True, disabled=(uploaded_file is None), key="send_audio_file")
    with col_upload3:
        if st.button("🗑️", help="Supprimer le fichier audio", use_container_width=True, disabled=(uploaded_file is None), key="delete_audio_file"):
            st.session_state.audio_upload_key += 1
            st.rerun()

if st.session_state.show_audio_recorder:
    st.markdown("---")
    col_record1, col_record2, col_record3 = st.columns([3, 0.8, 0.8])
    with col_record1:
        audio_recording = st.audio_input("Enregistrez votre message audio", key=f"audio_recording_{st.session_state.audio_recording_key}", label_visibility="collapsed")
    with col_record2:
        send_recording = st.button("▶", type="primary", help="Envoyer l'enregistrement", use_container_width=True, disabled=(audio_recording is None), key="send_recording")
    with col_record3:
        if st.button("🗑️", help="Supprimer l'enregistrement", use_container_width=True, disabled=(audio_recording is None), key="delete_recording"):
            st.session_state.audio_recording_key += 1
            st.rerun()

# Traitement des envois
# Vérifier si un message doit être traité (bouton cliqué OU Entrée pressée)
message_to_process = None
if send_text and user_text.strip():
    message_to_process = user_text.strip()
elif st.session_state.should_process_message and st.session_state.pending_message:
    message_to_process = st.session_state.pending_message
    st.session_state.should_process_message = False
    st.session_state.pending_message = None

if message_to_process:
    # Vérifier si le mode fiche est activé sans manager initialisé
    if st.session_state.fiche_mode and st.session_state.fiche_manager is None:
        # Auto-créer un manager en mode sélection
        keywords = ["fiche", "chantier", "défaut", "anomalie", "contrôle", "maintenance", "mes"]
        if any(keyword in message_to_process.lower() for keyword in keywords):
            # Essayer de détecter le type de fiche
            detected_type = detect_fiche_type_from_message(message_to_process)
            
            if detected_type:
                # Type détecté : créer directement la bonne fiche
                st.session_state.fiche_manager = FicheDefautChatManager(fiche_type=detected_type)
            else:
                # Type non détecté : créer en mode sélection
                st.session_state.fiche_manager = FicheDefautChatManager()
            
            initial_msg = get_initial_fiche_message(st.session_state.fiche_manager)
            st.session_state.messages = [{"role": "assistant", "content": initial_msg}]
            st.rerun()
    
    # Si le manager est en mode sélection, vérifier si l'utilisateur choisit un type
    if (st.session_state.fiche_mode and 
        st.session_state.fiche_manager and 
        st.session_state.fiche_manager.mode == "selection"):
        
        detected_type = detect_fiche_type_from_message(message_to_process)
        if detected_type:
            # Type détecté : initialiser la fiche
            st.session_state.fiche_manager.set_fiche_type(detected_type)
            initial_msg = get_initial_fiche_message(st.session_state.fiche_manager)
            st.session_state.messages = [{"role": "assistant", "content": initial_msg}]
            st.rerun()
    
    # Mode texte
    user_message = message_to_process
    
    # Ajouter le message de l'utilisateur à l'historique
    st.session_state.messages.append({"role": "user", "content": user_message})
    
    # Détection automatique d'intention de créer une fiche
    if auto_detect_and_activate_fiche_mode(user_message):
        st.rerun()
    
    # Mettre à jour la fiche si le mode est activé
    if st.session_state.fiche_mode and st.session_state.fiche_manager:
        # Récupérer la dernière question du chatbot pour le contexte
        last_question = ""
        if st.session_state.messages:
            for msg in reversed(st.session_state.messages):
                if msg["role"] == "assistant":
                    last_question = msg["content"]
                    break
        
        champs_mis_a_jour = st.session_state.fiche_manager.update_from_conversation(
            user_message, 
            last_question=last_question
        )
        if champs_mis_a_jour:
            print(f"✅ Champs mis à jour: {', '.join(champs_mis_a_jour)}")
    
    # Générer la réponse du chatbot
    with st.spinner("🤔 Réflexion en cours..."):
        try:
            # Préparer les messages pour l'API
            api_messages = [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in st.session_state.messages
            ]
            
            # Ajouter le contexte de la fiche si le mode est activé
            if st.session_state.fiche_mode and st.session_state.fiche_manager:
                system_msg = create_fiche_system_message(st.session_state.fiche_manager)
                api_messages = [system_msg] + api_messages
            
            # Obtenir la réponse
            response = get_chat_response(api_messages)
            
            # Ajouter la réponse à l'historique
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            error_msg = f"❌ Erreur: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Vider le champ de saisie en changeant la clé
    st.session_state.text_input_key += 1
    
    # Recharger la page pour afficher les nouveaux messages
    st.rerun()

elif send_audio_file and uploaded_file is not None:
    # Mode fichier audio uploadé
    with st.spinner("🎤 Transcription de l'audio en cours..."):
        try:
            # Sauvegarder temporairement le fichier
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                # Transcrire l'audio
                transcription = transcribe_audio(tmp_path)
                
                # Ajouter le message de l'utilisateur avec transcription
                st.session_state.messages.append({
                    "role": "user", 
                    "content": transcription,
                    "transcription": transcription
                })
                
                # Détection automatique d'intention de créer une fiche
                if auto_detect_and_activate_fiche_mode(transcription):
                    st.rerun()
                
                # Mettre à jour la fiche si le mode est activé
                if st.session_state.fiche_mode and st.session_state.fiche_manager:
                    # Récupérer la dernière question du chatbot pour le contexte
                    last_question = ""
                    if st.session_state.messages:
                        for msg in reversed(st.session_state.messages):
                            if msg["role"] == "assistant":
                                last_question = msg["content"]
                                break
                    
                    champs_mis_a_jour = st.session_state.fiche_manager.update_from_conversation(
                        transcription,
                        last_question=last_question
                    )
                    if champs_mis_a_jour:
                        print(f"✅ Champs mis à jour: {', '.join(champs_mis_a_jour)}")
                
                # Générer la réponse du chatbot
                with st.spinner("🤔 Réflexion en cours..."):
                    try:
                        # Préparer les messages pour l'API
                        api_messages = [
                            {"role": msg["role"], "content": msg["content"]} 
                            for msg in st.session_state.messages
                        ]
                        
                        # Ajouter le contexte de la fiche si le mode est activé
                        if st.session_state.fiche_mode and st.session_state.fiche_manager:
                            system_msg = create_fiche_system_message(st.session_state.fiche_manager)
                            api_messages = [system_msg] + api_messages
                        
                        # Obtenir la réponse
                        response = get_chat_response(api_messages)
                        
                        # Ajouter la réponse à l'historique
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                    except Exception as e:
                        error_msg = f"❌ Erreur: {str(e)}"
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
            finally:
                # Nettoyer le fichier temporaire
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
            # Vider la zone de fichier en changeant la clé
            st.session_state.audio_upload_key += 1
            
            # Recharger la page
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la transcription: {str(e)}")

elif send_recording and audio_recording is not None:
    # Mode enregistrement audio
    with st.spinner("🎤 Transcription de l'enregistrement en cours..."):
        try:
            # Sauvegarder temporairement le fichier audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_recording.read())
                tmp_path = tmp_file.name
            
            try:
                # Transcrire l'audio
                transcription = transcribe_audio(tmp_path)
                
                # Ajouter le message de l'utilisateur avec transcription
                st.session_state.messages.append({
                    "role": "user", 
                    "content": transcription,
                    "transcription": transcription
                })
                
                # Détection automatique d'intention de créer une fiche
                if auto_detect_and_activate_fiche_mode(transcription):
                    st.rerun()
                
                # Mettre à jour la fiche si le mode est activé
                if st.session_state.fiche_mode and st.session_state.fiche_manager:
                    # Récupérer la dernière question du chatbot pour le contexte
                    last_question = ""
                    if st.session_state.messages:
                        for msg in reversed(st.session_state.messages):
                            if msg["role"] == "assistant":
                                last_question = msg["content"]
                                break
                    
                    champs_mis_a_jour = st.session_state.fiche_manager.update_from_conversation(
                        transcription,
                        last_question=last_question
                    )
                    if champs_mis_a_jour:
                        print(f"✅ Champs mis à jour: {', '.join(champs_mis_a_jour)}")
                
                # Générer la réponse du chatbot
                with st.spinner("🤔 Réflexion en cours..."):
                    try:
                        # Préparer les messages pour l'API
                        api_messages = [
                            {"role": msg["role"], "content": msg["content"]} 
                            for msg in st.session_state.messages
                        ]
                        
                        # Ajouter le contexte de la fiche si le mode est activé
                        if st.session_state.fiche_mode and st.session_state.fiche_manager:
                            system_msg = create_fiche_system_message(st.session_state.fiche_manager)
                            api_messages = [system_msg] + api_messages
                        
                        # Obtenir la réponse
                        response = get_chat_response(api_messages)
                        
                        # Ajouter la réponse à l'historique
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                    except Exception as e:
                        error_msg = f"❌ Erreur: {str(e)}"
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
            finally:
                # Nettoyer le fichier temporaire
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
            # Vider la zone d'enregistrement en changeant la clé
            st.session_state.audio_recording_key += 1
            
            # Recharger la page
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la transcription: {str(e)}")

# Sidebar avec informations et actions
with st.sidebar:
    st.header("ℹ️ À propos")
    st.markdown("""
    **Chatbot IA Conversationnel pour la création de fiches**
    
    Chattez avec une IA en utilisant :
    - ✍️ **Texte** : Tapez directement votre message
    - 📁 **Fichier Audio** : Uploadez un fichier audio (.wav, .mp3, .m4a)
    - 🎤 **Enregistrement** : Enregistrez votre voix directement
    
    L'IA comprend le contexte de la conversation et répond de manière cohérente.
    L'IA identifiera le type de fiche et la remplira automatiquement. Donnez autant d'informations que possible pour que l'IA puisse remplir la fiche correctement ou laissez vous guider.
    Type de fiche disponible :
    - Fiche de Défauts
    - Fiche de Contrôle MES
    - Fiche de Contrôle Poseur
    - Fiche de Contrôle Electricien
    """)
    
    st.divider()
    
    st.header("🔧 Modèles utilisés")
    st.info("""
    - **Whisper** : Transcription audio
    - **GPT-4o** : Génération de réponses
    """)
    
    st.divider()
    
    # Paramètres de synthèse vocale
    st.header("🔊 Synthèse vocale")
    text_to_speech_enabled = st.toggle(
        "Activer la synthèse vocale",
        value=st.session_state.text_to_speech_enabled,
        key="text_to_speech_toggle",
        help="Lire automatiquement les réponses de l'assistant à voix haute"
    )
    if text_to_speech_enabled != st.session_state.text_to_speech_enabled:
        st.session_state.text_to_speech_enabled = text_to_speech_enabled
    
    st.divider()
    
    # Mode Fiche de Défauts
    st.header("📋 Créer une fiche")
    
    # Toggle pour activer/désactiver le mode
    fiche_mode_active = st.toggle(
        "Activer le mode Fiche",
        value=st.session_state.fiche_mode,
        key="fiche_toggle"
    )
    
    # Si le toggle change d'état
    if fiche_mode_active != st.session_state.fiche_mode:
        st.session_state.fiche_mode = fiche_mode_active
        
        if fiche_mode_active:
            # Activer le mode : choisir entre nouvelle fiche ou charger OCR
            st.session_state.messages = []  # Vider l'historique
        else:
            # Désactiver le mode
            st.session_state.fiche_manager = None
            st.session_state.messages = []
        
        st.rerun()
    
    # Interface du mode fiche
    if st.session_state.fiche_mode:
        st.markdown("**Mode actif** ✅")
        
        # Options de démarrage
        if st.session_state.fiche_manager is None:
            st.info("💡 Choisis le type de fiche ou charge un document OCR")
            st.markdown("---")
            
            from utils.fiche_types import get_available_fiches
            fiches_list = get_available_fiches()
            
            # Icônes pour chaque type
            icones = {
                'defauts': '🔧',
                'controle_mes': '📋',
                'electriciens': '⚡',
                'poseurs': '🏗️'
            }
            
            # Créer les options pour le selectbox
            options_display = []
            options_mapping = {}
            
            for fiche in fiches_list:
                icone = icones.get(fiche['id'], '📄')
                display_text = f"{icone} {fiche['nom']}"
                options_display.append(display_text)
                options_mapping[display_text] = fiche['id']
            
            st.markdown("**📝 Sélectionne un type de fiche:**")
            
            selected_option = st.selectbox(
                "Type de fiche",
                options=options_display,
                index=None,
                placeholder="Choisir un type...",
                label_visibility="collapsed"
            )
            
            if selected_option:
                # Afficher la description de la fiche sélectionnée
                fiche_id = options_mapping[selected_option]
                selected_fiche = next(f for f in fiches_list if f['id'] == fiche_id)
                st.caption(selected_fiche['description'])
                
                # Bouton de création avec texte plus court
                if st.button("✅ Créer", use_container_width=True, type="primary"):
                    fiche_type = FicheType(fiche_id)
                    st.session_state.fiche_manager = FicheDefautChatManager(fiche_type=fiche_type)
                    initial_msg = get_initial_fiche_message(st.session_state.fiche_manager)
                    st.session_state.messages = [{"role": "assistant", "content": initial_msg}]
                    st.rerun()
            
        
        else:
            # Afficher l'état de la fiche
            st.markdown("---")
            
            # Afficher le type de fiche si sélectionné
            if st.session_state.fiche_manager.mode != "selection":
                from utils.fiche_types import get_fiche_structure
                fiche_info = get_fiche_structure(st.session_state.fiche_manager.fiche_type)
                
                if fiche_info:
                    st.info(f"📝 **{fiche_info['nom']}**")
                    
                    completude = st.session_state.fiche_manager.get_completion_percentage()
                    st.progress(completude / 100, text=f"Complétion: {completude:.0f}%")
                else:
                    st.error("⚠️ Type de fiche non reconnu")
                
                # Bouton pour afficher le détail
                with st.expander("📊 Détails de la fiche"):
                    st.markdown(st.session_state.fiche_manager.get_completion_summary())
            else:
                st.warning("⏳ En attente de sélection du type de fiche...")
            
            # Boutons pour exporter
            if completude >= 100:
                st.success("✅ Fiche complète à 100% !")
                
                # Export TXT
                txt_export = st.session_state.fiche_manager.export_txt()
                st.download_button(
                    label="📥 Télécharger la fiche (.txt)",
                    data=txt_export,
                    file_name=f"fiche_defaut_{st.session_state.fiche_manager.entities.get('mise_en_service', {}).get('nom_chantier', 'export').replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    type="primary"
                )
                
                # Export JSON (optionnel, pour développeurs)
                with st.expander("💾 Export avancé (JSON)"):
                    json_export = st.session_state.fiche_manager.export_json()
                    st.download_button(
                        label="📥 Télécharger JSON",
                        data=json_export,
                        file_name="fiche_defaut_complete.json",
                        mime="application/json",
                        use_container_width=True
                    )
            
            # Bouton pour recommencer
            col1, col2 = st.columns([1, 6], vertical_alignment="center")
            with col1:
                if st.button("🔄", key="btn_recommencer"):
                    st.session_state.fiche_manager = None
                    st.session_state.messages = []
                    st.rerun()
            with col2:
                st.markdown("Recommencer")

    st.divider()
    
    # Bouton pour effacer l'historique
    st.markdown("""
    <style>
    div[data-testid="stButton"] > button {
        border-radius: 50% !important;
        width: 44px;
        height: 44px;
        padding: 0 !important;
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 6], vertical_alignment="center")

    with col1:
        if st.button("🗑️", key="clear_history"):
            st.session_state.messages = []
            st.rerun()

    with col2:
        st.markdown("Effacer l’historique")
    
    # Afficher le nombre de messages
    if st.session_state.messages:
        st.info(f"💬 {len(st.session_state.messages)} messages dans l'historique")
