import os
import base64
import uuid
from google.cloud import storage
from openai import OpenAI
from dotenv import load_dotenv

# Charger les variables d'environnement (ex: OPENAI_API_KEY)
load_dotenv()

def generate_image(prompt):
        client = OpenAI()
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            quality="high",
            size="1024x1024"
        )
        return response.data[0].b64_json

def upload_to_gcs_from_base64(bucket_name, image_base64, destination_blob_name,credentials_path):
    """Uploade une image depuis une chaîne base64 vers GCS sans sauvegarde locale."""
    print(f"Upload de l'image vers le bucket GCS '{bucket_name}'...")
    try:
        # 1. Initialiser le client GCS
        storage_client = storage.Client.from_service_account_json(credentials_path)
        bucket = storage_client.bucket(bucket_name)

        # 2. Décoder la chaîne base64
        if "," in image_base64:
            _, encoded = image_base64.split(",", 1)
        else:
            encoded = image_base64
        image_data = base64.b64decode(encoded)

        # 3. Uploader les données en mémoire
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(image_data, content_type='image/png')
        
        public_url = f"https://storage.googleapis.com/{bucket.name}/{blob.name}"

        print("Upload réussi !")
        return public_url
    except Exception as e:
        print(f"Erreur lors de l'upload vers GCS : {e}")
        return None

def generate_and_upload_image(prompt, bucket_name, credentials_path, folder="personas"):
    """
    Orchestre la génération d'une image et son envoi sur GCS.
    1. Génère une image à partir d'un prompt.
    2. Uploade l'image sur Google Cloud Storage.
    3. Retourne l'URL publique de l'image.
    
    :param prompt: Le texte pour générer l'image.
    :param bucket_name: Le nom du bucket GCS.
    :param credentials_path: Le chemin vers le fichier de clé de service JSON.
    :param folder: Le dossier de destination dans le bucket (par défaut 'personas').
    :return: L'URL publique de l'image, ou None si une erreur survient.
    """
    print("--- Début du processus de génération et d'upload ---")
    
    # 1. Générer l'image
    image_base64 = generate_image(prompt)
    if not image_base64:
        print("--- Fin du processus : échec de la génération d'image ---")
        return None

    # 2. Définir un nom de fichier unique
    unique_filename = f"{folder}/{uuid.uuid4()}.png"

    # 3. Uploader l'image
    public_url = upload_to_gcs_from_base64(
        bucket_name=bucket_name,
        image_base64=image_base64,
        destination_blob_name=unique_filename,
        credentials_path=credentials_path
    )
    
    if public_url:
        print(f"--- Fin du processus : succès. URL : {public_url} ---")
    else:
        print("--- Fin du processus : échec de l'upload ---")

    return public_url

# --- Script de Test ---

if __name__ == "__main__":
    # --- Configuration ---
    GCS_BUCKET_NAME = "images-oryjin"
    CREDENTIALS_PATH = "config_gcloud.json" # Assurez-vous que le fichier est au bon endroit
    TEST_PROMPT = "Un logo abstrait pour une startup tech, style néon sur fond sombre."
    
    # --- Vérification des credentials ---
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"ERREUR : Le fichier de clé '{CREDENTIALS_PATH}' est introuvable.")
        print("Veuillez le placer à côté de ce script ou mettre à jour le chemin.")
    else:
        # --- Exécution avec la nouvelle fonction --- 
        final_url = generate_and_upload_image(
            prompt=TEST_PROMPT,
            bucket_name=GCS_BUCKET_NAME,
            credentials_path=CREDENTIALS_PATH,
            folder="tests" # On met les images de test dans un dossier 'tests'
        )
        
        if final_url:
            print(f"\nTest réussi ! L'image est disponible à l'URL suivante : {final_url}")
        else:
            print("\nLe test a échoué. Veuillez vérifier les logs ci-dessus.")
