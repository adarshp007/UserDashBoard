#!/usr/bin/env python
"""
Script to create the Minio bucket if it doesn't exist.
This should be run when the container starts.
"""
import os
import boto3
from botocore.client import Config
import time

# Wait for Minio to be ready
time.sleep(5)

# Get settings from environment variables
AWS_ACCESS_KEY_ID = os.getenv('S3_ACCESS_KEY', 'minioadmin')
AWS_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_KEY', 'minioadmin')
AWS_BUCKET = os.getenv('S3_BUCKET', 'userdashboard')
AWS_ENDPOINT = os.getenv('S3_ENDPOINT', 'http://minio:9000')

# Create S3 client
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)
config = Config(
    signature_version='s3v4',
    retries={
        'total_max_attempts': 3,
        'mode': 'standard'
    },
    read_timeout=200
)
s3 = session.client('s3', endpoint_url=AWS_ENDPOINT, config=config)

# Create bucket if it doesn't exist
try:
    s3.head_bucket(Bucket=AWS_BUCKET)
    print(f"Bucket {AWS_BUCKET} already exists")
except Exception:
    try:
        s3.create_bucket(Bucket=AWS_BUCKET)
        print(f"Created bucket {AWS_BUCKET}")
    except Exception as e:
        print(f"Error creating bucket: {str(e)}")
