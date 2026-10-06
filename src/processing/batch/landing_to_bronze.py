"""
from processing.batch.file_utils import unzip, xls_to_csv

faire ici la recuperation de landing zip & csv
    - unzipper & convetir
    - mettre dans la table append-only les métadonnées de la table bronze des fichiers donnés


    UTILISER ces lignes pour unzip & convert
    response.raise_for_status()
    xls_stream = unzip(response.content)
    self.s3_body = xls_to_csv(xls_stream)
"""
