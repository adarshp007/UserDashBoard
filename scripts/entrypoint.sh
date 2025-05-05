#!/bin/bash

# Create Minio bucket
python /app/scripts/create_minio_bucket.py

# Run the command passed to the script
exec "$@"
