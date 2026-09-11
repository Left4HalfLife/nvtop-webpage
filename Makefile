# Makefile for nvtop-webpage

.PHONY: help install run setup up down logs build check clean

help: ## Show this help message
	@echo "Available commands:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make setup      - Generate secrets and build the image"
	@echo "  make up         - Start the Compose service"
	@echo "  make down       - Stop the Compose service"
	@echo "  make logs       - Follow application logs"
	@echo "  make run        - Run locally (requires AUTH_PASSWORD and SECRET_KEY)"
	@echo "  make check      - Validate source and configuration"
	@echo "  make clean      - Remove temporary files"

install:
	python3 -m pip install -r requirements.txt

run:
	./run.sh

setup:
	./setup.sh

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f nvtop-webapp

build:
	docker compose build

check:
	python3 -m py_compile app.py
	python3 -m json.tool instance/config.json >/dev/null
	bash -n setup.sh run.sh opt/nvtop/actions/*.sh
	docker compose config --quiet

clean:
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
