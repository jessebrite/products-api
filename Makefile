# Makefile for FastAPI project with Docker, testing, and migrations

# Set project name
PROJECT_NAME = products-api

# The Python environment or docker commands
PYTHON = python
DOCKER_COMPOSE = docker-compose -f docker-compose.yml

TARGETS = run clean install unit integration covunit covint cov test lint format migrate docker-up \
	build docker-stop docker-down docker-test coverage

.PHONY: $(TARGETS)

## Run FastAPI in development mode (with hot-reload)
run:
	cd src && uvicorn main:app --reload

## Clean up coverage and cache files
clean:
	rm -rf .coverage* coverage_html dist build .mypy_cache .ruff_cache __pycache__ **/__pycache__

## Install project dependencies
install:
	uv sync --all-extras --dev

## Run unit tests only
unit:
	uv run pytest tests/unit --tb=long maxfail=1 -vv

integration:
	uv run pytest tests/integration --tb=long maxfail=1 -vv

## Run unit tests with coverage
covunit:
	uv run coverage run --data-file=.coverage.unit \
		-m pytest tests/unit/ --tb=long --durations=8 -v
	uv run coverage report --data-file=.coverage.unit -m

## Run integration tests with coverage
covint:
	uv run coverage run --data-file=.coverage.integration \
        -m pytest tests/integration/ --tb=long --durations=8 -v
	uv run coverage report --data-file=.coverage.integration -m

## Run the current code coverage
cov:
	uv run coverage report -m

## Combine coverage reports and generate HTML report
coverage: covunit covint
	echo "removing old .coverage to avoid any gotcha"
	rm -f .coverage
	uv run coverage combine .coverage.*
	uv run coverage report -m
	uv run coverage html
	uv run coverage xml -o coverage-combined.xml

## Run all tests (unit + integration)
test:
	uv run pytest --tb=long --maxfail=1 -vv --disable-warnings

## Lint the code using ruff
lint:
	uv run ruff check .

## Format the code using ruff
format:
	uv run ruff format . && uv run ruff check --fix .

## Run database migrations using alembic
migrate:
	uv run alembic upgrade head

## Build the Docker image and start containers
docker-up:
	$(DOCKER_COMPOSE) up --build

## Build the Docker image without starting containers (useful for CI/CD)
build:
	$(DOCKER_COMPOSE) build

## Stop the running Docker containers (doesn't remove them)
docker-stop:
	$(DOCKER_COMPOSE) stop

## Clean up the containers and volumes
docker-down:
	$(DOCKER_COMPOSE) down -v

## Run tests inside Docker (useful in CI or isolated environment)
docker-test:
	$(DOCKER_COMPOSE) run --rm app pytest -vv --disable-warnings

## Lint, format, and test all in one go (CI ready)
ci:
	make format
	make coverage
