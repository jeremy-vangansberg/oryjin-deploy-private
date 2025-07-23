import os
import base64
import uuid
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Import optionnels selon le backend utilisé
try:
    from google.cloud import storage
except ImportError:
    storage = None
try:
    from azure.storage.blob import BlobServiceClient, ContentSettings, generate_blob_sas, BlobSasPermissions
except ImportError:
    BlobServiceClient = None
    ContentSettings = None
    generate_blob_sas = None
    BlobSasPermissions = None

# Charger les variables d'environnement (ex: OPENAI_API_KEY)
load_dotenv()

def decode_base64_image(image_base64):
    """Décode une image base64, gère le préfixe éventuel."""
    if "," in image_base64:
        _, encoded = image_base64.split(",", 1)
    else:
        encoded = image_base64
    return base64.b64decode(encoded)

class StorageUploader:
    """Interface d'upload d'image."""
    def upload(self, image_base64, destination_blob_name):
        raise NotImplementedError

class GCSUploader(StorageUploader):
    def __init__(self, bucket_name, credentials_path):
        if storage is None:
            raise ImportError("google-cloud-storage n'est pas installé.")
        self.bucket_name = bucket_name
        self.credentials_path = credentials_path
        self.client = storage.Client.from_service_account_json(credentials_path)
        self.bucket = self.client.bucket(bucket_name)

    def upload(self, image_base64, destination_blob_name):
        print(f"Upload de l'image vers le bucket GCS '{self.bucket_name}'...")
        try:
            image_data = decode_base64_image(image_base64)
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_string(image_data, content_type='image/png')
            public_url = f"https://storage.googleapis.com/{self.bucket.name}/{blob.name}"
            print("Upload réussi !")
            return public_url
        except Exception as e:
            print(f"Erreur lors de l'upload vers GCS : {e}")
            return None

class AzureBlobUploader(StorageUploader):
    def __init__(self, connection_string, container_name):
        if BlobServiceClient is None:
            raise ImportError("azure-storage-blob n'est pas installé.")
        self.connection_string = connection_string
        self.container_name = container_name
        self.service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.service_client.get_container_client(container_name)
        # Création du conteneur s'il n'existe pas
        try:
            self.container_client.create_container()
            print(f"Conteneur '{container_name}' créé sur Azure Blob.")
        except Exception as e:
            if 'ContainerAlreadyExists' in str(e):
                pass  # Le conteneur existe déjà, on ne fait rien
            else:
                print(f"Erreur lors de la création du conteneur Azure : {e}")
                raise

    def upload(self, image_base64, destination_blob_name):
        print(f"Upload de l'image vers le conteneur Azure Blob '{self.container_name}'...")
        try:
            image_data = decode_base64_image(image_base64)
            blob_client = self.container_client.get_blob_client(destination_blob_name)
            blob_client.upload_blob(
                image_data,
                overwrite=True,
                content_settings=ContentSettings(content_type='image/png')
            )
            # Générer un SAS token valable 1h (si disponible)
            if generate_blob_sas is not None and BlobSasPermissions is not None:
                sas_token = generate_blob_sas(
                    account_name=self.service_client.account_name,
                    container_name=self.container_name,
                    blob_name=destination_blob_name,
                    account_key=self.service_client.credential.account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(hours=1)
                )
                public_url = f"https://{self.service_client.account_name}.blob.core.windows.net/{self.container_name}/{destination_blob_name}?{sas_token}"
            else:
                # URL sans SAS token (accès public requis)
                public_url = f"https://{self.service_client.account_name}.blob.core.windows.net/{self.container_name}/{destination_blob_name}"
                print("Attention: SAS token non disponible, utilisation d'une URL publique")
            print("Upload réussi !")
            return public_url
        except Exception as e:
            print(f"Erreur lors de l'upload vers Azure Blob : {e}")
            return None

def generate_image(prompt):
    client = OpenAI()
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        quality="low",
        size="1024x1024"
    )
    return response.data[0].b64_json

def generate_and_upload_image(prompt, uploader, folder="personas"):
    """
    Orchestre la génération d'une image et son envoi sur un backend de stockage.
    :param prompt: Le texte pour générer l'image.
    :param uploader: Instance de StorageUploader (GCSUploader ou AzureBlobUploader).
    :param folder: Le dossier de destination (par défaut 'personas').
    :return: L'URL publique de l'image, ou None si une erreur survient.
    """
    print("--- Début du processus de génération et d'upload ---")
    image_base64 = generate_image(prompt)
    if not image_base64:
        print("--- Fin du processus : échec de la génération d'image ---")
        return None
    unique_filename = f"{folder}/{uuid.uuid4()}.png"
    public_url = uploader.upload(image_base64, unique_filename)
    if public_url:
        print(f"--- Fin du processus : succès. URL : {public_url} ---")
    else:
        print("--- Fin du processus : échec de l'upload ---")
    return public_url

