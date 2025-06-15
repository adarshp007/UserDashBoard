#!/usr/bin/env python
"""
Script to upload a sample file to Minio.
This is useful for testing the application.
"""
import os
import sys
from io import BytesIO

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from botocore.client import Config

# Get settings from environment variables
AWS_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY", "minioadmin")
AWS_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
AWS_BUCKET = os.getenv("S3_BUCKET", "userdashboard")
AWS_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")


def create_sample_data():
    """Create a sample DataFrame for testing."""
    # Create a sample DataFrame
    data = {
        "Region": ["Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Fujairah"],
        "Gender": ["Male", "Female", "Male", "Female", "Male"],
        "Employment_Rate": [75.2, 68.5, 72.1, 65.8, 70.3],
        "Population": [1500000, 2500000, 800000, 400000, 300000],
        "Year": [2020, 2020, 2020, 2020, 2020],
        "Quarter": [1, 1, 1, 1, 1],
    }
    return pd.DataFrame(data)


def upload_sample_file():
    """Upload a sample file to Minio."""
    # Create sample data
    df = create_sample_data()

    # Convert to Parquet
    table = pa.Table.from_pandas(df)
    parquet_buffer = BytesIO()
    pq.write_table(table, parquet_buffer, compression="snappy")
    parquet_buffer.seek(0)

    # Create S3 client
    session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    config = Config(signature_version="s3v4", retries={"total_max_attempts": 3, "mode": "standard"}, read_timeout=200)
    s3 = session.client("s3", endpoint_url=AWS_ENDPOINT, config=config)

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
            return False

    # Define file name and path
    file_name = "employment_data_sample.parquet"
    s3_path = f"datasets/{file_name}"

    # Upload file
    try:
        s3.upload_fileobj(parquet_buffer, AWS_BUCKET, s3_path)
        print(f"Uploaded sample file to {s3_path}")
        return True
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return False


if __name__ == "__main__":
    success = upload_sample_file()
    sys.exit(0 if success else 1)
