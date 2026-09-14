lancement docker compose core
docker compose --env-file .env -f infrastructure/docker-compose.core.yml up -d

lancement docker compose batch
docker compose --env-file .env -f infrastructure/docker-compose.batch.yml up -d

lancement docker compose stream
docker compose --env-file .env -f infrastructure/docker-compose.stream.yml up -d

utiliser la commande 
docker exec -it airflow-wattcast airflow users reset-password -u admin -p admin
pour modifier les acces admin de airflow (cause : init du standalone)
