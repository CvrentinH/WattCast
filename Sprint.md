# 🏃‍♂️ Sprint Backlog : Architecture Smart Grid

> **Objectif du Sprint :** Mettre en place les fondations de l'architecture hybride Lambda-Kappa pour le projet Smart Grid.

## 1. 📥 Ingestion et Routage des Flux
- [ ] **RabbitMQ** : Configurer les files d'attente pour la collecte des messages MQTT/AMQP.
- [ ] **RabbitMQ** : Implémenter le pré-routage pour la gestion des pics de connexion intermittents.
- [ ] **Kafka Connect** : Mettre en place le connecteur pour transférer les messages vers Kafka.
- [ ] **Apache Kafka** : Créer les topics clés (`telemetry.raw.smartmeters`, `grid.alerts`, `market.prices.realtime`).
- [ ] **Apache Kafka** : Configurer le partitionnement sur `grid_node_id` et un facteur de réplication de 3.

## 2. ⚙️ Traitement et Consommation
- [ ] **Apache Flink** : Développer le job de Stream Processing avec fenêtrage (Tumbling et Sliding Windows).
- [ ] **Apache Flink** : Implémenter le calcul d'agrégats à la volée (ex: consommation par noeud toutes les 5 min).
- [ ] **Apache Flink** : Configurer la remontée d'alertes de surcharge vers Redis.
- [ ] **Apache Spark** : Développer les jobs Batch (Spark SQL / Dataframe) pour le nettoyage de la couche Bronze.
- [ ] **Apache Spark** : Implémenter l'imputation (interpolation linéaire/moyenne) pour traiter les valeurs manquantes.

## 3. 🗄️ Stockage Multi-Modèles (Data Lakehouse)
- [ ] **MinIO (Couche Bronze)** : Configurer le bucket S3 pour le stockage brut JSON/Avro (partitionnement `year/month/day`).
- [ ] **MinIO (Couche Silver)** : Mettre en place le stockage Parquet/Delta Lake (données enrichies météo/géo et dédoublonnées).
- [ ] **Redis (Feature Store)** : Configurer le cache temps réel pour stocker l'état du réseau (latence < 5ms).
- [ ] **PostgreSQL (Serving Store)** : Créer les tables pour la couche Gold (administration, topologie, historique).
- [ ] **MongoDB (Document Store)** : Configurer la base pour les logs semi-structurés et rapports d'intervention.

## 4. 🔀 Orchestration
- [ ] **Apache Airflow** : Créer le DAG quotidien pour le téléchargement des données Open-Meteo.
- [ ] **Apache Airflow** : Créer le DAG de lancement des jobs Spark de consolidation/nettoyage.
- [ ] **Apache Airflow** : Mettre en place les "Data Quality Gates" avant le passage de Silver à Gold.

## 5. 🧠 MLOps et Cycle de Vie des Modèles
- [ ] **Entraînement** : Développer le pipeline d'entraînement du modèle (XGBoost/LSTM) pour prédire la charge à J+1.
- [ ] **Inférence** : Conteneuriser (FastAPI) et déployer le microservice d'inférence.
- [ ] **Retraining** : Configurer Airflow pour surveiller la performance (MAPE > 5%) et déclencher le ré-entraînement.

## 6. 🏗️ DevOps et Infrastructure
- [ ] **Terraform** : Écrire le code pour provisionner les clusters Kubernetes, les rôles IAM et MinIO.
- [ ] **Docker** : Créer les `Dockerfile` pour chaque brique (Spark, Flink, Airflow, API ML).
- [ ] **Réseau & Sécurité** : Configurer les réseaux virtuels isolés et les variables d'environnement.

## 7. 📊 Observabilité et Restitution
- [ ] **Prometheus & Grafana** : Mettre en place le monitoring technique (files Kafka, checkpoints Flink, K8s).
- [ ] **Power BI** : Connecter Power BI à la couche Gold PostgreSQL.
- [ ] **Power BI** : Créer le tableau de bord métier incluant la médiation des données (facteurs clés de décision).

## 8. 🛡️ Patterns de Design à valider
- [ ] **Event Sourcing** : Tester le rejeu du flux d'événements depuis la couche Bronze.
- [ ] **CQRS** : Vérifier l'isolation entre écritures (Kafka/MinIO) et lectures (PostgreSQL/Power BI).
- [ ] **Circuit Breaker** : Implémenter et tester la règle métier dégradée en cas de panne du modèle ML.
