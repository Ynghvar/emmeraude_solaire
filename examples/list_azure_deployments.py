"""
Script pour lister les déploiements disponibles sur Azure OpenAI
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

if not AZURE_API_KEY or not AZURE_ENDPOINT:
    print("❌ Variables d'environnement manquantes")
    print("   AZURE_OPENAI_API_KEY et AZURE_OPENAI_ENDPOINT doivent être définies")
    exit(1)

# Nettoyer l'endpoint
AZURE_ENDPOINT = AZURE_ENDPOINT.rstrip('/')

print(f"🔍 Récupération des déploiements disponibles...")
print(f"   Endpoint: {AZURE_ENDPOINT}\n")

# Essayer différentes API versions
api_versions = ["2024-10-01-preview", "2024-08-01-preview", "2024-06-01", "2024-02-15-preview", "2023-12-01-preview"]

for api_version in api_versions:
    # URL pour lister les déploiements
    url = f"{AZURE_ENDPOINT}/openai/deployments?api-version={api_version}"
    
    headers = {
        "api-key": AZURE_API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ API version {api_version} - Succès\n")
            data = response.json()
            
            if "data" in data and len(data["data"]) > 0:
                print(f"📋 Déploiements disponibles ({len(data['data'])}):\n")
                for deployment in data["data"]:
                    print(f"  • Nom: {deployment.get('id', 'N/A')}")
                    print(f"    Modèle: {deployment.get('model', 'N/A')}")
                    print(f"    Status: {deployment.get('status', 'N/A')}")
                    if 'capabilities' in deployment:
                        print(f"    Capacités: {deployment.get('capabilities', {})}")
                    print()
                break
            else:
                print("⚠️  Aucun déploiement trouvé")
                print(f"   Réponse brute: {data}\n")
                break
                
        elif response.status_code == 404:
            print(f"⚠️  API version {api_version} - Pas disponible (404)")
            continue
        else:
            print(f"❌ API version {api_version} - Erreur {response.status_code}")
            print(f"   {response.text}\n")
            
    except Exception as e:
        print(f"❌ Erreur avec API version {api_version}: {str(e)}\n")
        continue

print("\n💡 Pour utiliser un déploiement spécifique, ajoutez dans votre .env:")
print("   AZURE_MISTRAL_DEPLOYMENT=nom_du_deploiement")
