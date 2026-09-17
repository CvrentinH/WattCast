Créer le reseau interne du projet
docker network create wattcast

lancement docker compose core
make core

lancement docker compose batch
make batch 

lancement docker compose stream
make stream 

utiliser 
stat -c '%g' /var/run/docker.sock 
pour connaitre le gid et le remplir dans le .env

MINIO
http://localhost:9001/

PGADMIN
http://localhost:5050/

AIRFLOW
http://localhost:8080/

FLINK
http://localhost:8081

SPARK
http://localhost:4040
