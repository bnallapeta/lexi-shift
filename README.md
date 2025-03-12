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

## Quick Start

### Prerequisites

- Python 3.9+ (tested with 3.9 and 3.11)
- Docker (optional, for containerized deployment)
- Kubernetes (optional, for cluster deployment)

### Local Development

1. **Set up the development environment**

   ```bash
   # Create and activate a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Run the service locally**

   ```bash
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
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

### Configuration Endpoint

- `GET /config` - Get current service configuration and supported languages

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

#### Batch Translate

```bash
curl -X POST http://localhost:8000/batch_translate \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Hello, how are you?", "What is your name?"],
    "options": {
      "source_lang": "en",
      "target_lang": "fr",
      "beam_size": 5
    }
  }'
```

Response:

```json
{
  "translations": [
    "Bonjour, comment allez-vous?",
    "Comment vous appelez-vous?"
  ],
  "source_lang": "en",
  "target_lang": "fr",
  "processing_time": 1.535
}
```

#### Get Configuration

```bash
curl -X GET http://localhost:8000/config
```

Response:

```json
{
  "model_size": "small",
  "device": "cpu",
  "compute_type": "float32",
  "supported_languages": ["en", "fr", "de", "es", "it", "pt", "ru", "zh", "ja", "ko", "ar", "hi", ...]
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
translation-service/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── logging_setup.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints.py
│   │   └── models.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── translation.py
│   └── utils/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_config.py
│   ├── test_endpoints.py
│   ├── test_logging.py
│   ├── test_main.py
│   └── test_translation.py
├── k8s/
│   └── translation-service.yaml
├── Dockerfile
├── Makefile
├── requirements.txt
├── README.md
└── .gitignore
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