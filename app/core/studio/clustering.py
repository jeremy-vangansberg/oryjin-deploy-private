from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd

def perform_kmeans(data: pd.DataFrame) -> str:
    """
    Effectue un clustering K-Means sur les données fournies.
    - Crée une copie des données pour le prétraitement afin de ne pas modifier l'original.
    - Gère les valeurs manquantes.
    - Standardise les données numériques pertinentes.
    - Applique l'algorithme K-Means.
    - Ajoute les étiquettes de cluster au DataFrame original.
    - Calcule les statistiques moyennes pour chaque cluster sur TOUTES les colonnes.
    - Retourne un aperçu textuel de ces statistiques pour analyse par le LLM.
    """
    # Créer une copie pour le prétraitement afin de ne pas modifier le DataFrame original
    data_for_clustering = data.copy()

    data_for_clustering.drop(['ID_H3','RF', 'ZONES_HAB_CAT', 'RESTAURANTS_CAT', 'COMMERCES_CAT','EDUCATION_CAT' ], axis=1, inplace=True)

    # Gérer les valeurs manquantes (-1)
    data_for_clustering.replace({-1: np.nan}, inplace=True)
    data_for_clustering.fillna(data_for_clustering.mean(), inplace=True)


    # Standardiser les données
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data_for_clustering)

    # Effectuer le clustering
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    kmeans.fit(scaled_data)

    # Ajouter les étiquettes de cluster au DataFrame original
    data_for_clustering['cluster'] = kmeans.labels_
    
    # Calculer les statistiques sur le DataFrame original pour conserver toutes les colonnes
    statistics_clusters = data_for_clustering.groupby('cluster').mean()
    
    # Retourner l'aperçu des statistiques en JSON pour une extraction fiable par le LLM
    statistics_clusters_preview = statistics_clusters.to_json(orient='index', indent=2)
    return statistics_clusters_preview