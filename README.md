# Translation Service

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
   
   # Or using make
   make dev
   ```

3. **Test the API**

   ```bash
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
   ```

### Docker Deployment

1. **Build the Docker image**

   ```bash
   docker build -t translation-service:latest .
   ```

2. **Run the Docker container**

   ```bash
   docker run -p 8000:8000 translation-service:latest
   ```

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