"""
Script pour tester différents modèles sur Azure
"""
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

if not AZURE_API_KEY or not AZURE_ENDPOINT:
    print("❌ Variables d'environnement manquantes")
    exit(1)

print(f"🧪 Test des modèles disponibles sur Azure")
print(f"   Endpoint: {AZURE_ENDPOINT}\n")

# Initialiser le client Azure OpenAI
client = AzureOpenAI(
    api_key=AZURE_API_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=AZURE_ENDPOINT
)

# Liste de modèles à tester
models_to_test = [
    "gpt-4o",
    "mistral-document-ai-2505",
]

for model in models_to_test:
    print(f"🔍 Test du modèle: {model}")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": "Bonjour, réponds par OK"
                }
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"  ✅ Le modèle '{model}' fonctionne!")
        print(f"  📝 Réponse: {result}\n")
            
    except Exception as e:
        error_str = str(e)
        if "DeploymentNotFound" in error_str or "404" in error_str:
            print(f"  ❌ Le modèle '{model}' n'est pas déployé sur votre ressource Azure\n")
        elif "401" in error_str or "Unauthorized" in error_str:
            print(f"  ⚠️  Erreur d'authentification pour '{model}'\n")
        elif "InvalidRequestError" in error_str:
            print(f"  ⚠️  Requête invalide pour '{model}': {error_str[:150]}\n")
        else:
            print(f"  ❌ Erreur pour '{model}': {error_str[:200]}\n")

print("\n" + "="*60)
print("💡 Suggestions:")
print("   1. Utilisez les modèles qui fonctionnent (✅) pour vos tâches")
print("   2. Les modèles avec ❌ doivent être déployés dans Azure AI Studio")
print("   3. Vérifiez que le nom du déploiement correspond exactement")
