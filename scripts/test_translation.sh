#!/bin/bash
# Script to test the translation service

set -e

# Default values
HOST="localhost"
PORT="8000"
ENDPOINT="/translate"
TEXT="Hello, how are you?"
SOURCE_LANG="en"
TARGET_LANG="fr"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --host)
      HOST="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --endpoint)
      ENDPOINT="$2"
      shift 2
      ;;
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
URL="http://${HOST}:${PORT}${ENDPOINT}"

# Construct JSON payload
PAYLOAD=$(cat <<EOF
{
  "text": "${TEXT}",
  "options": {
    "source_lang": "${SOURCE_LANG}",
    "target_lang": "${TARGET_LANG}",
    "beam_size": 5,
    "max_length": 200
  }
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