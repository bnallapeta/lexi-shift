# lexi-shift: Translation Service

A high-performance text translation service using NLLB-200 models, designed to be part of a speech-to-speech translation pipeline.

## Overview

The Translation Service is a microservice that provides text translation capabilities between 100+ languages using Meta's NLLB-200 models. It is designed to be:

- **Fast**: Optimized for near real-time translation
- **Scalable**: Runs efficiently in Kubernetes
- **Flexible**: Supports various model sizes and compute options
- **Robust**: Includes comprehensive error handling and monitoring

This service is part of a larger speech-to-speech translation pipeline that includes:

1. **Speech-to-Text (ASR)** - Kube-Whisperer (already implemented)
2. **Text Translation** - This service
3. **Text-to-Speech (TTS)** - Future implementation

## Features

- Translation between 100+ languages
- Support for various model sizes (small, medium, large, xl)
- CPU and GPU acceleration
- Quantization options for improved performance
- REST API with JSON request/response
- Health, readiness, and liveness endpoints
- Structured logging
- Containerized deployment
- Kubernetes manifests

## Implementation Status

We have successfully implemented:

- Core translation functionality using NLLB-200 models
- REST API with endpoints for single and batch translation
- Configuration endpoint to retrieve model settings and supported languages
- Health and readiness checks
- Structured logging with request tracking
- Proper error handling and validation
- Language code mapping between ISO codes (e.g., "en", "fr") and NLLB-200 codes (e.g., "eng_Latn", "fra_Latn")
- Support for different model sizes and compute types
- Language detection for automatic source language identification
- Asynchronous translation endpoints with task tracking
- Translation caching for improved performance
- Prometheus metrics for monitoring
- Kubernetes deployment with resource limits and autoscaling

## Quick Start

### Prerequisites

- Python 3.9+ (tested with 3.9 and 3.11)
- Docker (optional, for containerized deployment)
- Kubernetes (optional, for cluster deployment)

### Local Development

1. **Set up the development environment**

   ```bash
   # Using the setup script
   ./scripts/setup_dev.sh
   
   # Or using make
   make setup-local
   ```

2. **Run the service in development mode**

   ```bash
   # Using the development script
   ./scripts/run_dev.sh
   
   # Or using make (default port: 8000)
   make run-local
   
   # Run on a custom port
   make PORT=8080 run-local
   ```

3. **Test the API**

   ```bash
   # For default port 8000
   curl -X POST http://localhost:8000/translate \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Hello, how are you?",
       "options": {
         "source_lang": "en",
         "target_lang": "fr",
         "beam_size": 5
       }
     }'
   
   # If using a custom port
   curl -X POST http://localhost:8080/translate \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Hello, how are you?",
       "options": {
         "source_lang": "en",
         "target_lang": "fr",
         "beam_size": 5
       }
     }'
   ```

4. **Access API Documentation**

   While the service is running, you can access:
   - Swagger UI: http://localhost:8000/docs (replace 8000 with your custom port if needed)
   - ReDoc: http://localhost:8000/redoc (replace 8000 with your custom port if needed)

### Docker Deployment

1. **Build the Docker image**

   ```bash
   docker build -t translation-service:latest .
   ```

2. **Run the container**

   ```bash
   docker run -p 8000:8000 translation-service:latest
   ```

3. **Test the container**

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

### Container Runtime Options

The project supports both Docker and Podman as container runtimes. The Makefile automatically detects which runtime is available on your system.

1. **Check container runtime information**

   ```bash
   make container-info
   ```

2. **Force a specific container runtime**

   ```bash
   # Force Docker
   make FORCE_DOCKER=1 build

   # Force Podman
   make FORCE_PODMAN=1 build
   ```

3. **Build and run with the detected runtime**

   ```bash
   # Build the image
   make build

   # Run the container
   make run-container

   # Test the container endpoint
   make test-container-endpoint
   ```

4. **Multi-architecture builds**

   The project supports multi-architecture builds using buildx when available:

   ```bash
   # Build for multiple architectures (requires buildx)
   make acr-build
   ```

   If buildx is not available, the build will fall back to a single architecture build.

### Azure Container Registry (ACR) Deployment

1. **Set up Azure CLI and login to Azure**

   ```bash
   az login
   ```

2. **Set environment variables**

   ```bash
   export REGISTRY_TYPE=acr
   export REGISTRY_NAME=your-acr-name  # Replace with your ACR name
   ```

3. **Login to ACR**

   ```bash
   make acr-login
   ```

4. **Build and push image to ACR**

   ```bash
   make acr-build
   ```

   Or build and push separately:

   ```bash
   make build
   make acr-push
   ```

5. **Run the container locally**

   ```bash
   make run-container
   ```

6. **Test the container endpoint**

   ```bash
   make test-translation
   ```

### KServe Deployment

This project supports deploying the translation service as a KServe InferenceService. Follow these steps to deploy to KServe:

1. **Prerequisites**
   - Kubernetes cluster with KServe installed
   - kubectl configured to access your cluster

2. **Create Kubernetes secret for ACR**

   ```bash
   make create-secret
   ```

3. **Deploy KServe InferenceService**

   ```bash
   make kserve-deploy
   ```

4. **Get the InferenceService URL**

   ```bash
   make kserve-url
   ```

5. **Test the KServe InferenceService**

   ```bash
   make test-kserve
   ```

### Troubleshooting ACR and KServe

#### ACR Issues

- **Authentication errors**: Make sure you're logged in to Azure (`az login`) and ACR (`make acr-login`).
- **Push errors**: Check that your ACR name is correct and that you have permissions to push to the repository.
- **Build errors**: If you encounter build errors, try cleaning the build cache with `make acr-clean` and then rebuilding.

#### KServe Issues

- **Deployment errors**: Check the status of the InferenceService with `kubectl get inferenceservices` and `kubectl describe inferenceservice translation-service`.
- **Pod issues**: Check the pod logs with `kubectl logs -l serving.kserve.io/inferenceservice=translation-service`.
- **Connection issues**: Make sure the InferenceService is ready and the URL is accessible.
- **Image pull errors**: Verify that the Kubernetes secret for ACR is correctly configured with `kubectl describe secret registry-secret`.

## API Reference

### Health Endpoints

- `GET /health` - Basic health check
- `GET /ready` - Readiness check (verifies model is loaded)

### Translation Endpoints

- `POST /translate` - Translate a single text
- `POST /batch_translate` - Translate multiple texts in a batch
- `POST /detect_language` - Detect the language of a text
- `POST /async/translate` - Submit an asynchronous translation request
- `POST /async/batch_translate` - Submit an asynchronous batch translation request
- `GET /async/status/{task_id}` - Get the status of an asynchronous translation task

### Configuration and Monitoring Endpoints

- `GET /config` - Get current service configuration and supported languages
- `GET /cache/stats` - Get translation cache statistics
- `POST /cache/clear` - Clear the translation cache
- `GET /metrics` - Prometheus metrics (on port 8001)

### Example Requests

#### Translate Text

```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "options": {
      "source_lang": "en",
      "target_lang": "fr",
      "beam_size": 5,
      "max_length": 200
    }
  }'
```

Response:

```json
{
  "translated_text": "Bonjour, comment allez-vous?",
  "source_lang": "en",
  "target_lang": "fr",
  "processing_time": 0.922
}
```

#### Auto-Detect Language and Translate

```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hola, ¿cómo estás?",
    "options": {
      "target_lang": "en",
      "beam_size": 5
    }
  }'
```

Response:

```json
{
  "translated_text": "Hello, how are you?",
  "source_lang": "es",
  "target_lang": "en",
  "processing_time": 0.845
}
```

#### Detect Language

```bash
curl -X POST http://localhost:8000/detect_language \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bonjour, comment allez-vous?",
    "top_k": 3
  }'
```

Response:

```json
{
  "detections": [
    {"language": "fr", "confidence": 0.89},
    {"language": "ca", "confidence": 0.05},
    {"language": "it", "confidence": 0.03}
  ],
  "processing_time": 0.021
}
```

#### Asynchronous Translation

```bash
curl -X POST http://localhost:8000/async/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "options": {
      "source_lang": "en",
      "target_lang": "fr",
      "beam_size": 5
    },
    "callback_url": "https://example.com/webhook"
  }'
```

Response:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2023-04-01T12:34:56.789Z"
}
```

#### Check Asynchronous Translation Status

```bash
curl -X GET http://localhost:8000/async/status/550e8400-e29b-41d4-a716-446655440000
```

Response:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2023-04-01T12:34:56.789Z",
  "completed_at": "2023-04-01T12:35:01.234Z",
  "result": {
    "translated_text": "Bonjour, comment allez-vous?",
    "source_lang": "en",
    "target_lang": "fr",
    "processing_time": 0.922
  }
}
```

## Quick Start for KServe

### Deploy to KServe
```bash
# Set environment variables
export KUBECONFIG=/path/to/your/kubeconfig
export REGISTRY_TYPE=acr
export REGISTRY_NAME=your-acr-name

# Login to ACR
make acr-login

# Build and push image
make acr-build

# Create Kubernetes secret for ACR
make create-secret

# Deploy to KServe
make kserve-deploy

# Get service URL
make kserve-url
```

### Test the KServe Deployment
```bash
# Test translation
curl -X POST "http://translation-service.default.your-domain.com/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "options": {
      "source_lang": "en",
      "target_lang": "fr"
    }
  }'
```

### Container Runtime Options

The project supports both Docker and Podman as container runtimes. The Makefile automatically detects which runtime is available on your system.

1. **Check container runtime information**

   ```bash
   make container-info
   ```

2. **Force a specific container runtime**

   ```bash
   # Force Docker
   make FORCE_DOCKER=1 build

   # Force Podman
   make FORCE_PODMAN=1 build
   ```

3. **Build and run with the detected runtime**

   ```bash
   # Build the image
   make build

   # Run the container
   make run-container

   # Test the container endpoint
   make test-container-endpoint
   ```

4. **Multi-architecture builds**

   The project supports multi-architecture builds using buildx when available:

   ```bash
   # Build for multiple architectures (requires buildx)
   make acr-build
   ```

   If buildx is not available, the build will fall back to a single architecture build.

## Configuration

The service can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_SIZE` | Model size (small, medium, large, xl) | small |
| `MODEL_DEVICE` | Device to use (cpu, cuda, mps) | cpu |
| `MODEL_COMPUTE_TYPE` | Compute type (float32, float16, int8) | float32 |
| `MODEL_DOWNLOAD_ROOT` | Root directory for model downloads | /tmp/nllb_models |
| `SERVER_HOST` | Host to bind the server to | 0.0.0.0 |
| `SERVER_PORT` | Port to bind the server to | 8000 |
| `SERVER_LOG_LEVEL` | Log level | info |
| `METRICS_PORT` | Port for Prometheus metrics | 8001 |
| `CACHE_MAX_SIZE` | Maximum number of items in the translation cache | 1000 |
| `CACHE_TTL` | Time to live for cached translations (in seconds) | 3600 |

### Compute Type Options

- **float32**: Full precision, highest accuracy but slower and uses more memory
- **float16**: Half precision, good balance of accuracy and performance
- **int8**: 8-bit quantization, fastest but may reduce accuracy slightly

> **Note**: Using `int8` requires the `bitsandbytes` package to be installed. If not available, the service will automatically fall back to `float32`.

### Additional Dependencies

For optimal performance with certain configurations, you may need to install additional packages:

```bash
# For int8 quantization support
pip install bitsandbytes

# For improved loading performance
pip install accelerate
```

## How to Configure the Service

You can configure the translation service in several ways:

### 1. Environment Variables

When running locally or in a container, set environment variables:

```bash
# Local development
export MODEL_SIZE=medium
export MODEL_DEVICE=cpu
export MODEL_COMPUTE_TYPE=float16
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# Docker
docker run -p 8000:8000 \
  -e MODEL_SIZE=medium \
  -e MODEL_DEVICE=cpu \
  -e MODEL_COMPUTE_TYPE=float16 \
  translation-service:latest
```

### 2. Kubernetes ConfigMap/Environment Variables

In your Kubernetes deployment or KServe InferenceService, add environment variables:

```yaml
# In k8s/translation-inferenceservice.yaml
containers:
  - name: translation-service
    image: bnracr.azurecr.io/translation-service:latest
    env:
    - name: MODEL_SIZE
      value: "small"
    - name: MODEL_DEVICE
      value: "cpu"
    - name: MODEL_COMPUTE_TYPE
      value: "float32"
```

### 3. Makefile Variables

When using the provided Makefile targets, you can override variables:

```bash
# Deploy with specific model size
make kserve-deploy MODEL_SIZE=medium MODEL_DEVICE=cpu

# Build with specific configuration
make build MODEL_SIZE=large MODEL_COMPUTE_TYPE=float16
```

### 4. Configuration Endpoint

You can check the current configuration via the `/config` endpoint:

```bash
curl -X GET http://translation-service.default.your-domain.com/config
```

This will return the current configuration including model size, device, compute type, and supported languages.

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest
```

## Project Structure

```
lexi-shift/
├── .build/              # Build artifacts and temporary files
├── .github/             # GitHub workflows
├── docs/                # Documentation files
├── k8s/                 # Kubernetes manifests
├── scripts/             # Utility scripts
│   ├── clean.sh         # Clean up the project
│   ├── install_hooks.sh # Install git hooks
│   ├── run_dev.sh       # Run the service in development mode
│   ├── run_tests.sh     # Run tests with coverage
│   └── setup_dev.sh     # Set up the development environment
├── src/                 # Source code
│   ├── api/             # API endpoints
│   ├── models/          # Translation models
│   └── utils/           # Utility functions
└── tests/               # Test suite
```

### Utility Scripts

The `scripts` directory contains utility scripts for development and testing:

- `setup_dev.sh`: Sets up the development environment
- `run_dev.sh`: Runs the service in development mode with hot reloading
- `run_tests.sh`: Runs tests with coverage reporting
- `clean.sh`: Cleans up the project
- `install_hooks.sh`: Installs git hooks for code quality

To use these scripts:

```bash
# Set up development environment
./scripts/setup_dev.sh

# Run service in development mode
./scripts/run_dev.sh

# Run tests with coverage
./scripts/run_tests.sh

# Clean up the project
./scripts/clean.sh

# Install git hooks
./scripts/install_hooks.sh
```

### Git Hooks

The project includes git hooks to ensure code quality:

- **pre-commit**: Automatically formats and lints staged Python files using black, isort, and flake8

Git hooks are installed automatically when you run `./scripts/setup_dev.sh` or can be installed manually with `./scripts/install_hooks.sh`.

### Makefile Targets

The project includes a Makefile with various targets for common tasks:

```bash
# Set up development environment
make setup-local

# Run service in development mode
make dev

# Run tests with coverage
make test

# Format code with black and isort
make format

# Lint code with flake8
make lint

# Install git hooks
make hooks

# Clean up the project
make clean

# Build Docker image
make build

# Run container locally
make run-container

# Test container endpoint
make test-container-endpoint

# ACR specific commands
make acr-login     # Login to Azure Container Registry
make acr-build     # Build and push multi-arch image to ACR
make acr-push      # Push image to ACR
make acr-clean     # Clean ACR images
make acr-rebuild   # Clean and rebuild ACR images
make create-secret # Create Kubernetes secret for ACR

# KServe commands
make kserve-deploy # Deploy KServe InferenceService
make kserve-url    # Get KServe InferenceService URL
make test-kserve   # Test KServe InferenceService

# Show all available targets
make help
```

## Known Issues and Limitations

- The service currently requires a significant amount of memory to load the NLLB-200 model, especially for larger model sizes.
- First-time translation requests may be slower as the model needs to be loaded into memory.
- The int8 quantization may not work on all platforms due to compatibility issues with the bitsandbytes library.

## Future Improvements

- Add support for custom terminology and domain-specific translations
- Implement caching for frequent translations to improve performance
- Add support for more advanced translation options (formatting preservation, etc.)
- Implement WebSocket support for streaming translations
- Add support for more advanced monitoring and observability features

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Meta NLLB-200](https://github.com/facebookresearch/fairseq/tree/nllb) - The underlying translation model
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/index) - Used for model loading and inference
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework for building the API

## Monitoring

The service exposes Prometheus metrics on port 8001. The following metrics are available:

- **Request metrics**: Count and latency of HTTP requests
- **Translation metrics**: Count, latency, and text length of translations
- **Model metrics**: Load time and memory usage of the translation model
- **System metrics**: CPU and memory usage of the service
- **Task metrics**: Count, latency, and queue size of asynchronous tasks

You can use Grafana to visualize these metrics and set up alerts.