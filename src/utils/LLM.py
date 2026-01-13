from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Vérification des variables d'environnement
api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

if not api_key:
    raise ValueError("AZURE_OPENAI_API_KEY n'est pas définie dans les variables d'environnement")
if not azure_endpoint:
    raise ValueError("AZURE_OPENAI_ENDPOINT n'est pas définie dans les variables d'environnement")

client = AzureOpenAI(
    api_key=api_key,
    api_version="2024-02-15-preview",
    azure_endpoint=azure_endpoint
)

def get_response(prompt):
    """Fonction de compatibilité pour un prompt simple"""
    return get_chat_response([{"role": "user", "content": prompt}])

def get_chat_response(messages):
    """
    Génère une réponse du chatbot basée sur l'historique de conversation
    
    Args:
        messages: Liste de dictionnaires avec 'role' ('user' ou 'assistant') et 'content'
    
    Returns:
        str: La réponse du chatbot
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = f"Erreur lors de l'appel à l'API Azure OpenAI: {str(e)}"
        if "401" in str(e) or "Unauthorized" in str(e):
            error_msg += "\nVérifiez que votre clé API (AZURE_OPENAI_API_KEY) est valide et que votre endpoint (AZURE_OPENAI_ENDPOINT) est correct."
        raise Exception(error_msg) from e


#if __name__ == "__main__":
#    try:
#        print(get_response("Hello, how are you?"))
#    except Exception as e:
#        print(f"Erreur: {e}")