#!/bin/bash
# Test KServe InferenceService for Translation

set -e

# Get the InferenceService URL
SERVICE_URL=$(kubectl get inferenceservice translation-service -o jsonpath='{.status.url}' 2>/dev/null)

if [ -z "$SERVICE_URL" ]; then
    echo "Error: Could not retrieve InferenceService URL. Is the service deployed?"
    exit 1
fi

echo "Testing translation service at: $SERVICE_URL"

# Remove protocol prefix if present
SERVICE_URL=${SERVICE_URL#http://}
SERVICE_URL=${SERVICE_URL#https://}

# Make a test translation request
echo "Sending test translation request..."
curl -X POST "http://$SERVICE_URL/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "options": {
      "source_lang": "en",
      "target_lang": "fr"
    }
  }'

echo
echo "Test completed. Verify that the response contains a translated text." 