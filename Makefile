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

# ── Database inspection commands ──

# Show all plans in the database
db-plans:
	docker compose exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "SELECT plan_id, plan_type, carrier, plan_name, year, quarter, ee_only, created_at FROM plans ORDER BY carrier, plan_name;"

# Count plans per carrier/quarter
db-summary:
	docker compose exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "SELECT carrier, quarter, year, COUNT(*) as plan_count FROM plans GROUP BY carrier, quarter, year ORDER BY carrier, quarter;"

# Show medical details for a specific plan (usage: make db-plan-details ID=<plan_id>)
db-plan-details:
	docker compose exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "SELECT p.carrier, p.plan_name, m.* FROM plans p JOIN medical_plan_details m USING (plan_id) WHERE p.plan_id = '$(ID)';"

# List all tables and row counts
db-tables:
	docker compose exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "SELECT 'plans' as table_name, COUNT(*) FROM plans UNION ALL SELECT 'medical_plan_details', COUNT(*) FROM medical_plan_details;"

# Open interactive psql shell
db-shell:
	docker compose exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

# ── Database reset commands ──

# Clear all plan data (keeps tables intact)
db-clear:
	docker compose exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "TRUNCATE plans CASCADE;"
	@echo "All plan data cleared."

# Full reset: drop tables and re-run migrations
db-reset: wait_for_db
	docker compose exec backend alembic downgrade base
	docker compose exec backend alembic upgrade head
	@echo "Database reset complete — tables recreated."

# Nuclear option: destroy the entire postgres volume and start fresh
db-nuke:
	@echo "WARNING: This will destroy ALL data in the database."
	docker compose down -v
	docker compose up -d db
	@echo "Waiting for DB to start..."
	sleep 3
	docker compose up -d backend
	@echo "Run 'make migrate' to recreate tables."