#!/bin/bash
# Script to test the KServe InferenceService

set -e

# Get the InferenceService URL
SERVICE_URL=$(kubectl get inferenceservice translation-service -o jsonpath='{.status.url}')

if [ -z "$SERVICE_URL" ]; then
  echo "Error: Could not get InferenceService URL. Make sure the service is deployed and ready."
  exit 1
fi

# Remove the protocol prefix if present
SERVICE_URL=${SERVICE_URL#http://}
SERVICE_URL=${SERVICE_URL#https://}

# Default values
TEXT="Hello, how are you?"
SOURCE_LANG="en"
TARGET_LANG="fr"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --text)
      TEXT="$2"
      shift 2
      ;;
    --source)
      SOURCE_LANG="$2"
      shift 2
      ;;
    --target)
      TARGET_LANG="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Construct URL
URL="http://${SERVICE_URL}/v1/models/translation-service:predict"

# Construct JSON payload
PAYLOAD=$(cat <<EOF
{
  "instances": [
    {
      "text": "${TEXT}",
      "options": {
        "source_lang": "${SOURCE_LANG}",
        "target_lang": "${TARGET_LANG}",
        "beam_size": 5,
        "max_length": 200
      }
    }
  ]
}
EOF
)

# Print request details
echo "Sending request to: ${URL}"
echo "Payload:"
echo "${PAYLOAD}" | jq . 2>/dev/null || echo "${PAYLOAD}"

# Send request
echo -e "\nResponse:"
curl -s -X POST "${URL}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}" | jq . 2>/dev/null || echo "Failed to parse response as JSON"

echo -e "\nRequest completed." 