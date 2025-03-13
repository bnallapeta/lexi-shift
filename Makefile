# Phony targets declaration
.PHONY: all build push deploy test run clean install install-test help \
        cluster-deploy cluster-test registry-start registry-stop dev-build \
        dev-push local-deploy setup-local run-local test-local \
        debug-deps debug-container clean-local create-secret show-config venv \
        cache-clean acr-login acr-build acr-push acr-clean acr-rebuild check-env \
        clean-artifacts container-info kserve-url test-kserve

# Core variables
ACR_NAME ?= bnracr
REGISTRY_TYPE ?= acr
REGISTRY_NAME ?= ${ACR_NAME}
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
REGISTRY_SECRET_NAME ?= acr-secret

# Container runtime configuration
CONTAINER_RUNTIME ?= $(shell which podman 2>/dev/null || which docker 2>/dev/null)
CONTAINER_TYPE := $(shell basename $(CONTAINER_RUNTIME))

# Build configuration
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

# Container information
container-info:
	@echo "Container Runtime Information:"
	@echo "  Runtime: $(CONTAINER_RUNTIME)"
	@$(CONTAINER_RUNTIME) version
	@echo "\nPlatforms:"
	@if echo $(CONTAINER_RUNTIME) | grep -q "docker"; then \
		$(CONTAINER_RUNTIME) buildx ls; \
	else \
		echo "  Podman platforms: $(shell $(CONTAINER_RUNTIME) info --format '{{.Host.Arch}}')"; \
	fi

# ACR commands
acr-login:
	@echo "Logging in to ACR..."
	az acr login --name $(REGISTRY_NAME)

acr-build: check-env acr-clean acr-build-only acr-push

acr-build-only: 
	@echo "Starting multi-architecture build..."
	@echo "Using container runtime: $(CONTAINER_RUNTIME)"
	@if echo $(CONTAINER_RUNTIME) | grep -q "docker"; then \
		echo "Using Docker for multi-architecture build..."; \
		$(CONTAINER_RUNTIME) buildx create --name multiarch --use || true; \
		$(CONTAINER_RUNTIME) buildx build \
			--platform $(PLATFORMS) \
			--build-arg BUILDPLATFORM=linux/amd64 \
			--build-arg TARGETPLATFORM=linux/amd64 \
			--tag $(REGISTRY_IMAGE) \
			--load .; \
		$(CONTAINER_RUNTIME) buildx rm multiarch; \
	else \
		echo "Using Podman for multi-architecture build..."; \
		echo "Cleaning up any existing images..."; \
		$(CONTAINER_RUNTIME) rmi $(REGISTRY_IMAGE)-amd64 2>/dev/null || true; \
		$(CONTAINER_RUNTIME) rmi $(REGISTRY_IMAGE)-arm64 2>/dev/null || true; \
		echo "Building AMD64 image..."; \
		BUILDPLATFORM=linux/amd64 $(CONTAINER_RUNTIME) build \
			--platform=linux/amd64 \
			--build-arg BUILDPLATFORM=linux/amd64 \
			--build-arg TARGETPLATFORM=linux/amd64 \
			--tag $(REGISTRY_IMAGE)-amd64 \
			--layers \
			--force-rm=false . || exit 1; \
		echo "Building ARM64 image..."; \
		BUILDPLATFORM=linux/arm64 $(CONTAINER_RUNTIME) build \
			--platform=linux/arm64 \
			--build-arg BUILDPLATFORM=linux/arm64 \
			--build-arg TARGETPLATFORM=linux/arm64 \
			--tag $(REGISTRY_IMAGE)-arm64 \
			--layers \
			--force-rm=false . || exit 1; \
	fi

acr-push:
	@if echo $(CONTAINER_RUNTIME) | grep -q "docker"; then \
		$(CONTAINER_RUNTIME) push $(REGISTRY_IMAGE); \
	else \
		echo "Pushing AMD64 image..."; \
		$(CONTAINER_RUNTIME) push $(REGISTRY_IMAGE)-amd64 || exit 1; \
		echo "Pushing ARM64 image..."; \
		$(CONTAINER_RUNTIME) push $(REGISTRY_IMAGE)-arm64 || exit 1; \
		echo "Cleaning up any existing manifests..."; \
		$(CONTAINER_RUNTIME) manifest rm $(REGISTRY_IMAGE) 2>/dev/null || true; \
		echo "Creating new manifest..."; \
		$(CONTAINER_RUNTIME) manifest create $(REGISTRY_IMAGE) || exit 1; \
		echo "Adding AMD64 image to manifest..."; \
		$(CONTAINER_RUNTIME) manifest add $(REGISTRY_IMAGE) $(REGISTRY_IMAGE)-amd64 || exit 1; \
		echo "Adding ARM64 image to manifest..."; \
		$(CONTAINER_RUNTIME) manifest add $(REGISTRY_IMAGE) $(REGISTRY_IMAGE)-arm64 || exit 1; \
		echo "Pushing manifest..."; \
		$(CONTAINER_RUNTIME) manifest push --all $(REGISTRY_IMAGE) || exit 1; \
	fi

acr-clean:
	@echo "Cleaning up registry images and manifests..."
	-$(CONTAINER_RUNTIME) manifest rm $(REGISTRY_IMAGE) 2>/dev/null || true
	-$(CONTAINER_RUNTIME) rmi $(REGISTRY_IMAGE)-amd64 2>/dev/null || true
	-$(CONTAINER_RUNTIME) rmi $(REGISTRY_IMAGE)-arm64 2>/dev/null || true
	-$(CONTAINER_RUNTIME) rmi $(REGISTRY_IMAGE) 2>/dev/null || true

# KServe commands
kserve-url:
	@echo "KServe InferenceService URL:"
	@kubectl get inferenceservice translation-service -o jsonpath='{.status.url}'

test-kserve:
	@echo "Testing KServe InferenceService..."
	./scripts/test_kserve.sh

# Environment checks
check-env:
	@if [ -z "$(REGISTRY_TYPE)" ]; then \
		echo "Error: REGISTRY_TYPE is not set"; \
		echo "Please set your registry type:"; \
		echo "  export REGISTRY_TYPE=acr|ghcr|dockerhub"; \
		exit 1; \
	fi
ifeq ($(REGISTRY_TYPE),acr)
	@if [ -z "$(REGISTRY_NAME)" ]; then \
		echo "Error: REGISTRY_NAME is not set"; \
		echo "Please set your Azure Container Registry name:"; \
		echo "  export ACR_NAME=your-acr-name"; \
		exit 1; \
	fi
endif

# Help
help:
	@echo "Available commands:"
	@echo "  Local Development:"
	@echo "    make setup-local   - Set up local development environment"
	@echo "    make run-local     - Run service locally"
	@echo "    make test          - Run tests"
	@echo ""
	@echo "  Container Operations:"
	@echo "    make container-info - Display container runtime information"
	@echo "    make build         - Build container image"
	@echo "    make push          - Push image to registry"
	@echo "    make deploy        - Deploy to Kubernetes"
	@echo "    make test-kserve   - Test KServe InferenceService"
	@echo ""
	@echo "  ACR Specific:"
	@echo "    make acr-login     - Login to Azure Container Registry"
	@echo "    make acr-build     - Build and push multi-arch image to ACR"
	@echo "    make acr-clean     - Clean up ACR images"
	@echo "    make create-secret - Create Kubernetes secret for ACR"
	@echo ""
	@echo "  KServe:"
	@echo "    make kserve-url    - Get KServe InferenceService URL"
	@echo "    make test-kserve   - Test KServe InferenceService"
	@echo ""
	@echo "  Cleanup:"
	@echo "    make clean         - Clean up all resources"
	@echo ""
	@echo "  Miscellaneous:"
	@echo "    make help          - Show this help message" 