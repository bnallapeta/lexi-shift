# Phony targets declaration
.PHONY: all build push deploy test run clean install install-test help \
        cluster-deploy cluster-test registry-start registry-stop dev-build \
        dev-push local-deploy cloud-deploy setup-local run-local test-local \
        debug-deps debug-container clean-local create-secret show-config venv \
        cache-clean acr-login acr-build acr-push acr-clean acr-rebuild check-env \
        clean-artifacts

# Core variables
REGISTRY_TYPE ?= ghcr
REGISTRY_NAME ?= ${GITHUB_USERNAME}
REGISTRY_URL ?= $(if $(filter acr,$(REGISTRY_TYPE)),$(REGISTRY_NAME).azurecr.io,\
                $(if $(filter ghcr,$(REGISTRY_TYPE)),ghcr.io/${GITHUB_USERNAME},\
                $(if $(filter dockerhub,$(REGISTRY_TYPE)),docker.io/${DOCKER_USERNAME},\
                $(REGISTRY_NAME))))

# Image configuration
IMAGE_NAME ?= translation-service
TAG ?= latest
REGISTRY_IMAGE = $(REGISTRY_URL)/$(IMAGE_NAME):$(TAG)
LOCAL_REGISTRY ?= localhost:5000
LOCAL_IMAGE_NAME = $(LOCAL_REGISTRY)/$(IMAGE_NAME):$(TAG)
REGISTRY_SECRET_NAME ?= registry-secret

# Build configuration
CONTAINER_RUNTIME ?= $(shell which podman 2>/dev/null || which docker 2>/dev/null)
PLATFORMS ?= linux/amd64,linux/arm64
CACHE_DIR ?= $(HOME)/.cache/translation-build
BUILD_JOBS ?= 2

# Development configuration
PYTHON ?= python3
VENV ?= venv
PIP ?= $(VENV)/bin/pip
KUBECONFIG ?= ${KUBECONFIG}

# Create cache directories
$(shell mkdir -p $(CACHE_DIR)/amd64 $(CACHE_DIR)/arm64)

# Default target
all: build

# Virtual environment setup
venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# Local development setup
setup-local:
	@echo "Setting up local development environment..."
	mkdir -p /tmp/nllb_models
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

# Build and push commands
build:
	$(CONTAINER_RUNTIME) build -t $(IMAGE_NAME):$(TAG) .
	$(CONTAINER_RUNTIME) tag $(IMAGE_NAME):$(TAG) $(REGISTRY_IMAGE)

push: check-env
	$(CONTAINER_RUNTIME) push $(REGISTRY_IMAGE)

# Deployment commands
deploy: check-env
	sed -e "s|\$${REGISTRY_IMAGE}|$(REGISTRY_IMAGE)|g" \
	    -e "s|\$${REGISTRY_SECRET_NAME}|$(REGISTRY_SECRET_NAME)|g" \
	    k8s/translation-service.yaml | kubectl apply -f -

# Testing commands
run:
	$(PYTHON) src/main.py

run-local: setup-local
	@echo "Starting Translation service locally..."
	. $(VENV)/bin/activate && $(PYTHON) -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

test:
	. $(VENV)/bin/activate && pytest tests/

# Cleanup commands
clean: clean-artifacts clean-local
	@echo "Clean complete!"

clean-local:
	rm -rf $(VENV)
	rm -rf /tmp/nllb_models
	rm -rf __pycache__
	rm -rf *.pyc
	rm -rf .pytest_cache

# Environment check
check-env:
	@if [ -z "$(GITHUB_USERNAME)" ] && [ "$(REGISTRY_TYPE)" = "ghcr" ]; then \
		echo "Error: GITHUB_USERNAME is not set"; \
		exit 1; \
	fi
	@if [ -z "$(DOCKER_USERNAME)" ] && [ "$(REGISTRY_TYPE)" = "dockerhub" ]; then \
		echo "Error: DOCKER_USERNAME is not set"; \
		exit 1; \
	fi

# Help
help:
	@echo "Available commands:"
	@echo "  Local Development:"
	@echo "    make setup-local   - Set up local development environment"
	@echo "    make run-local     - Run service locally"
	@echo "    make test          - Run tests"
	@echo ""
	@echo "  Build and Deploy:"
	@echo "    make build         - Build container image"
	@echo "    make push          - Push image to registry"
	@echo "    make deploy        - Deploy to Kubernetes"
	@echo ""
	@echo "  Cleanup:"
	@echo "    make clean         - Clean up all resources"
	@echo ""
	@echo "  Miscellaneous:"
	@echo "    make help          - Show this help message" 