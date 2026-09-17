.PHONY: help core batch stream down

help:
	@echo "     make core : lance le compose core (postgres, pgadmin, minio)"
	@echo "     make batch : lance le compose batch (airflow, spark)"
	@echo "     make stream : lance le compose stream (kafka, flink, redis)"
	@echo "     make down : ferme tous les compose"

core:
	docker compose -p wattcast-core --env-file .env -f infrastructure/docker-compose.core.yml up -d --remove-orphans

batch:
	docker compose -p wattcast-batch --env-file .env -f infrastructure/docker-compose.batch.yml build spark
	docker compose -p wattcast-batch --env-file .env -f infrastructure/docker-compose.batch.yml up -d --remove-orphans
	docker exec airflow-wattcast bash -c "until airflow db check 2>/dev/null; do sleep 2; done; airflow users reset-password -u admin -p admin"

stream:
	docker compose -p wattcast-stream --env-file .env -f infrastructure/docker-compose.stream.yml up -d --remove-orphans

down:
	docker compose -p wattcast-core --env-file .env -f infrastructure/docker-compose.core.yml down
	docker compose -p wattcast-batch --env-file .env -f infrastructure/docker-compose.batch.yml down
	docker compose -p wattcast-stream --env-file .env -f infrastructure/docker-compose.stream.yml down
