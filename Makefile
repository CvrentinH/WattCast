.PHONY: help core batch stream down

help:
	@echo "     make core : lance le compose core (postgres, pgadmin, minio)"
	@echo "     make batch : lance le compose batch (airflow, spark)"
	@echo "     make stream : lance le compose stream (kafka, flink, redis)"
	@echo "     make down : ferme tous les compose"

core:
	docker compose -p myapp-core --env-file .env -f infrastructure/docker-compose.core.yml up -d --remove-orphans

batch:
	docker compose -p myapp-batch --env-file .env -f infrastructure/docker-compose.batch.yml up -d --remove-orphans
	@until docker exec airflow-wattcast airflow db check 2>/dev/null; do sleep 2; done
	@sleep 5
	docker exec -it airflow-wattcast airflow users reset-password -u admin -p admin

stream:
	docker compose -p myapp-stream --env-file .env -f infrastructure/docker-compose.stream.yml up -d --remove-orphans

down:
	docker compose -p myapp-core --env-file .env -f infrastructure/docker-compose.core.yml down
	docker compose -p myapp-batch --env-file .env -f infrastructure/docker-compose.batch.yml down
	docker compose -p myapp-stream --env-file .env -f infrastructure/docker-compose.stream.yml down
