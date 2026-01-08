# Include .env file if it exists
-include .env
export

# Detect OS
ifeq ($(OS),Windows_NT)
    OS_TYPE := windows
else
    OS_TYPE := unix
endif

.PHONY: mp

promote:
	git checkout stage
	git pull origin stage
	git merge dev --no-edit
	git push origin stage
	git checkout master
	git pull origin master
	git merge stage --no-edit
	git push origin master
	git checkout dev

promote-stage:
	git checkout stage
	git pull origin stage
	git merge dev --no-edit
	git push origin stage
	git checkout dev

# Production commands
up:
	docker compose up -d
down:
	docker compose down
restart:
	docker compose down
	docker compose up --build -d

# Development commands
up-dev:
	docker compose -f dev.docker-compose.yml up --build -d
down-dev:
	docker compose -f dev.docker-compose.yml down
restart-dev:
	docker compose -f dev.docker-compose.yml down --remove-orphans
	docker compose -f dev.docker-compose.yml up --build -d --remove-orphans

# Staging commands
up-stage:
	docker compose -f stage.docker-compose.yml up -d
down-stage:
	docker compose -f stage.docker-compose.yml down
restart-stage:
	docker compose -f stage.docker-compose.yml down
	docker compose -f stage.docker-compose.yml up --build -d

# Wait for database to be ready before running migrations
wait_for_db:
ifeq ($(OS_TYPE),windows)
	powershell -File wait-for-db.ps1 -POSTGRES_USER $(POSTGRES_USER) -POSTGRES_DB $(POSTGRES_DB)
else
	bash wait-for-db.sh $(POSTGRES_USER) $(POSTGRES_DB)
endif

# Database migration commands
mms:
	docker compose exec backend alembic check || docker compose exec backend alembic revision --autogenerate
migrate: wait_for_db
	docker compose exec -it backend alembic upgrade head
head:
	docker compose exec backend alembic current


init: wait_for_db
	docker compose exec -i backend alembic upgrade head
	docker compose exec -i backend python init_db.py

init-prod: wait_for_db
	docker compose -p project-name-prod exec -i backend alembic upgrade head
	docker compose -p project-name-prod exec -i backend python init_db.py