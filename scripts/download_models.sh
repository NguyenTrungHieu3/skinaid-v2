#!/bin/bash
set -e

echo "=== Downloading models from S3 ==="

MODEL_DIR=${MODEL_DIR:-/app/models}
S3_BUCKET=${S3_BUCKET:-skinaid-models}

if [ ! -f "$MODEL_DIR/.downloaded" ]; then
    echo "Downloading models..."
    aws s3 sync s3://${S3_BUCKET}/models/ ${MODEL_DIR}/
    touch "$MODEL_DIR/.downloaded"
    echo "Models downloaded successfully!"
else
    echo "Models already downloaded, skipping..."
fi
