# Makefile for nvtop-webpage

.PHONY: help install dev run docker docker-build docker-run test clean lint check

help: ## Show this help message
	@echo "Available commands:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make dev        - Run Flask app with auto-reload (development)"
	@echo "  make run        - Run Flask app (production)"
	@echo "  make docker     - Build Docker image"
	@echo "  make docker-run - Run container locally"
	@echo "  make clean      - Remove temporary files"

install: ## Install Python dependencies
	pip install -r requirements.txt

dev: install ## Run Flask app with auto-reload (development)
	FLASK_DEBUG=true python app.py

run: install ## Run Flask app (production)
	FLASK_ENV=production python app.py

docker-build: ## Build Docker image
	docker build -t nvtop-webapp .

docker-run: ## Run container locally (useful for testing)
	docker run -d \
		--name nvtop-webapp \
		-p 5000:5000 \
		-e AUTH_USER="nvtop-admin" \
		-e AUTH_PASSWORD="your-secret-password-here" \
		nvtop-webapp

docker-stop: ## Stop running container
	docker stop nvtop-webapp || true

docker-clean: docker-stop ## Clean up old containers and images
	docker rm nvtop-webapp 2>/dev/null || true
	docker rmi nvtop-webapp 2>/dev/null || true
	docker system prune -f

check: lint test ## Run lint and tests

lint: ## Check code style (if flake8/pylint is installed)
	flake8 app.py config.py || echo "Lint issues found (optional)"

test: install ## Run any tests (add tests later)
	echo "Tests would run here. Add pytest/unit tests as needed."

clean: ## Remove temporary files
	rm -rf __pycache__/*.pyc
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

check-sys: ## Check system requirements
	@echo "Checking Python version..."
	python3 --version
	@echo "Python is installed. Next: Run 'make install'"
