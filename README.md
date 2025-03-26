# lexi-shift: Translation Service

A high-performance text translation service using Meta's NLLB-200 models for 100+ languages, designed as part of a speech-to-speech translation pipeline.

## Overview

This microservice provides text translation capabilities with a focus on:
- **Performance**: Optimized for near real-time translation
- **Flexibility**: Supports multiple model sizes and compute options
- **Scalability**: Containerized for Kubernetes deployment
- **Robustness**: Comprehensive error handling and monitoring

## Key Features

- Translation between 100+ languages
- Model size options: small, medium, large, xl
- CPU/GPU acceleration with quantization options
- Language detection for automatic source identification
- Synchronous and asynchronous translation endpoints
- Translation caching
- Prometheus metrics
- Kubernetes/KServe integration

## Quick Start

### Prerequisites
- Python 3.11
- Docker/Podman (for containerization)
- Kubernetes (for cluster deployment)

### Local Development

```bash
# Setup environment
./scripts/setup_dev.sh
# or
make setup-local

# Run service (default: port 8000)
./scripts/run_dev.sh
# or
make run-local
```

### Container Deployment

```bash
# Using Docker
docker build -t translation-service:latest .
docker run -p 8000:8000 translation-service:latest

# Using Podman
podman build -t translation-service:latest .
podman run -p 8000:8000 translation-service:latest

# Using Makefile (auto-detects Docker or Podman)
make build
make run-container
```

The project automatically detects whether Docker or Podman is available on your system and uses the appropriate runtime.

### Testing the API

```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "options": {
      "source_lang": "en",
      "target_lang": "fr"
    }
  }'
```

## API Endpoints

### Translation
- `POST /translate` - Translate single text
- `POST /batch_translate` - Batch translation
- `POST /detect_language` - Detect language
- `POST /async/translate` - Asynchronous translation
- `GET /async/status/{task_id}` - Check async task status

### System
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `GET /live` - Liveness check
- `GET /config` - Service configuration
- `GET /cache/stats` - Cache statistics
- `POST /cache/clear` - Clear cache
- `GET /metrics` - Prometheus metrics (port 8001)

## Configuration

Configure via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_SIZE` | Model size (small, medium, large, xl) | small |
| `MODEL_DEVICE` | Device (cpu, cuda, mps) | cpu |
| `MODEL_COMPUTE_TYPE` | Compute type (float32, float16, int8) | float32 |
| `SERVER_PORT` | Server port | 8000 |
| `METRICS_PORT` | Metrics port | 8001 |
| `CACHE_MAX_SIZE` | Cache size | 1000 |
| `CACHE_TTL` | Cache TTL (seconds) | 3600 |

## Deployment Options

### Azure Container Registry (ACR)
```bash
export REGISTRY_TYPE=acr
export REGISTRY_NAME=your-acr-name
make acr-login
make acr-build
```

### KServe Deployment

To deploy the service to KServe:

1. Create a Kubernetes secret for pulling from your container registry:

```bash
kubectl create secret docker-registry acr-secret \
  --docker-server=your-registry.azurecr.io \
  --docker-username=00000000-0000-0000-0000-000000000000 \
  --docker-password=$(az acr login --name your-registry --expose-token --query accessToken -o tsv) \
  --namespace=default
```

2. Apply the KServe InferenceService manifest:

```bash
kubectl apply -f k8s/translation-inferenceservice.yaml
```

3. Check the service status:

```bash
kubectl get inferenceservice
```

4. Get the service URL:

```bash
kubectl get inferenceservice translation-service -o jsonpath='{.status.url}'
```

### Testing KServe Deployment

For local testing with KServe, you can use nip.io to access the service:

```bash

# Test the service using nip.io
curl -X POST "http://lexi-shift.default.${EXTERNAL_IP}.nip.io/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "options": {
      "source_lang": "en",
      "target_lang": "fr"
    }
  }'
```

> Note: In production environments, replace the nip.io URL with your actual domain.

## Makefile Commands

Run `make help` to see all available commands, including:
- `make setup-local` - Setup development environment
- `make run-local` - Run service locally
- `make test` - Run tests
- `make build` - Build container image
- `make acr-build` - Build and push to ACR

## Project Structure

```
lexi-shift/
├── k8s/                 # Kubernetes manifests
├── scripts/             # Utility scripts
├── src/                 # Source code
│   ├── api/             # API endpoints
│   ├── models/          # Translation models
│   └── utils/           # Utility functions
└── tests/               # Test suite
```

## Git Hooks

The project includes git hooks for code quality that automatically format and lint your code on commit:

- Pre-commit hook runs black, isort, and flake8 on Python files
- Hooks are automatically installed when you run `./scripts/setup_dev.sh`
- Alternatively, install manually with `./scripts/install_hooks.sh`

## Known Limitations

- Memory intensive, especially for larger models
- First-time requests slower (model loading)
- int8 quantization compatibility varies by platform

## License

This project is licensed under the MIT License - see the LICENSE file for details.