import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from django.conf import settings
from datetime import datetime
import tempfile



def get_boto_client():
    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    config = Config(
        signature_version='s3v4',
        retries={
            'total_max_attempts': 3,  # Retry up to 3 times for faster error handling
            'mode': 'standard'  # Standard retry mode for quicker retries
        },
        read_timeout=200  # Set the read timeout to 120 seconds
    )
    s3 = session.client('s3', endpoint_url=settings.AWS_ENDPOINT, config=config)
    return s3


def upload_temp_file(request,file):
    s3 = get_boto_client()
    original_filename = file.name
    # Generate a timestamp and append it to the filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename, file_extension = os.path.splitext(original_filename)
    new_filename = f"{filename}_{timestamp}{file_extension}"
    # Save the file temporarily
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        for chunk in file.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name
    s3_path = f'datasets/{request.user.email.replace("@", "_").replace(".", "_")}/temp-folder/{new_filename}'
    try:
        s3.upload_file(temp_file_path, settings.AWS_BUCKET, s3_path)
    except Exception as e:
        raise e

    # Delete the temporary file
    os.remove(temp_file_path)
    return s3_path

def upload_file_to_s3(file_path, clean_filename, user_email="admin"):
    """
    Upload a file to S3/Minio.

    Args:
        file_path (str): Path to the local file
        clean_filename (str): Cleaned filename
        user_email (str): User email for organizing files

    Returns:
        str: S3 path where the file was uploaded
    """
    s3 = get_boto_client()
    s3_path = f'datasets/{user_email.replace("@", "_").replace(".", "_")}/{clean_filename}'
    try:
        s3.upload_file(file_path, settings.AWS_BUCKET, s3_path)
    except Exception as e:
        raise e
    return s3_path

def detect_and_convert_date_columns(df):
    """
    Detects and converts string columns that contain date values to datetime type.

    Args:
        df (pl.DataFrame): The DataFrame to process

    Returns:
        pl.DataFrame: DataFrame with date columns converted to datetime type
    """
    import polars as pl
    import re

    # Common date patterns to check
    date_patterns = [
        # ISO format: YYYY-MM-DD
        r'^\d{4}-\d{2}-\d{2}$',
        # US format: MM/DD/YYYY
        r'^\d{1,2}/\d{1,2}/\d{4}$',
        # European format: DD/MM/YYYY
        r'^\d{1,2}\.\d{1,2}\.\d{4}$',
        r'^\d{1,2}-\d{1,2}-\d{4}$',
        # With time component
        r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}',
        r'^\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}'
    ]

    # Function to check if a string matches any date pattern
    def is_date_string(s):
        if not isinstance(s, str):
            return False
        return any(re.match(pattern, s) for pattern in date_patterns)

    # Check each string column
    for col_name in df.columns:
        if df.schema[col_name] == pl.Utf8:  # Only check string columns
            # Get a sample of non-null values
            sample = df[col_name].drop_nulls().head(100).to_list()

            # Skip if no samples
            if not sample:
                continue

            # Check if most values match date patterns
            date_count = sum(1 for val in sample if is_date_string(val))
            if date_count > len(sample) * 0.8:  # If more than 80% match date patterns
                print(f"Converting column '{col_name}' to datetime type")
                try:
                    # Try to convert to datetime
                    df = df.with_columns(
                        pl.col(col_name).str.to_datetime(strict=False).alias(col_name)
                    )
                    print(f"Successfully converted '{col_name}' to datetime")
                except Exception as e:
                    print(f"Failed to convert '{col_name}' to datetime: {str(e)}")

    return df

def upload_dataset_to_s3(file_path, filename, extract_metadata=False):
    """
    Reads a CSV or Excel file, converts it to Parquet, and uploads it to S3/Minio.

    Args:
        file_path (str): The local path to the file (CSV or Excel).
        filename (str): The name to store the file as in S3.
        extract_metadata (bool): Whether to extract and return metadata about the file.

    Returns:
        dict: Dictionary containing the S3 URL and metadata if extract_metadata is True,
              otherwise just the S3 URL as a string.
    """
    from utils.aggregate import extract_dataset_metadata
    import os
    import polars as pl
    from io import BytesIO

    # Determine file type based on extension (case-insensitive)
    file_extension = os.path.splitext(filename.lower())[1]

    # Read file based on its extension
    if file_extension in ['.xlsx', '.xls']:
        # Read Excel file using Polars
        try:
            df = pl.read_excel(file_path, engine="openpyxl")
        except Exception as e:
            print(f"Error reading Excel file: {str(e)}")
            raise
    elif file_extension == '.csv':
        # Read CSV file using Polars
        try:
            # Try to infer delimiter and other parameters
            df = pl.read_csv(file_path, infer_schema_length=10000)
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            # Fallback to common delimiters if inference fails
            try:
                df = pl.read_csv(file_path, separator=',')
            except:
                try:
                    df = pl.read_csv(file_path, separator=';')
                except:
                    try:
                        df = pl.read_csv(file_path, separator='\t')
                    except Exception as e2:
                        print(f"Failed to read CSV with common delimiters: {str(e2)}")
                        raise
    else:
        raise ValueError(f"Unsupported file type: {file_extension}. Only .csv, .xlsx, and .xls are supported.")

    # Detect and convert date columns
    print("Detecting and converting date columns...")
    df = detect_and_convert_date_columns(df)

    # Extract metadata if requested
    metadata = None
    if extract_metadata:
        metadata = extract_dataset_metadata(df)

    # Convert to Parquet with Snappy compression (optimized for speed & size)
    parquet_buffer = BytesIO()
    df.write_parquet(parquet_buffer, compression="snappy")
    parquet_buffer.seek(0)  # Reset buffer position

    # Get S3 client
    s3 = get_boto_client()

    # Define new Parquet filename (preserve original name but change extension)
    base_filename = os.path.splitext(filename)[0]
    parquet_filename = f"{base_filename}.parquet"

    # Define S3 path
    s3_path = f'datasets/{parquet_filename}'

    # Upload Parquet file to S3
    try:
        s3.upload_fileobj(parquet_buffer, settings.AWS_BUCKET, s3_path)

        # Generate a URL for the file
        url = f"{settings.AWS_ENDPOINT}/{settings.AWS_BUCKET}/{s3_path}"

        print("*********************")
        print("S3 URL:", url)

        if extract_metadata:
            return {
                "url": url,
                "filename": parquet_filename,
                "s3_path": s3_path,
                "metadata": metadata
            }
        else:
            return url

    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        raise

def get_file_from_s3(file_name):
    """
    Retrieves a file from S3/Minio and loads it into a Polars DataFrame.

    Args:
        file_name (str): The name of the file to retrieve.

    Returns:
        pl.LazyFrame: A Polars LazyFrame containing the file data.
    """
    import os
    import polars as pl
    from io import BytesIO

    # Get S3 client
    s3 = get_boto_client()

    # Determine file extension (case-insensitive)
    file_extension = os.path.splitext(file_name.lower())[1]

    # Define Parquet filename based on original file extension
    if file_extension != '.parquet':
        base_filename = os.path.splitext(file_name)[0]
        parquet_filename = f"{base_filename}.parquet"
    else:
        parquet_filename = file_name

    # Define S3 path
    s3_path = f'datasets/{parquet_filename}'

    try:
        # Download the file into memory
        file_content = BytesIO()
        s3.download_fileobj(settings.AWS_BUCKET, s3_path, file_content)
        file_content.seek(0)

        # Read the Parquet file into a Polars DataFrame first to check schema
        print(f"Reading file {parquet_filename} from S3")
        df = pl.read_parquet(file_content)

        # Print schema for debugging
        print(f"File schema: {df.schema}")

        # Check for string columns that might be dates
        string_cols = [col for col, dtype in df.schema.items() if dtype == pl.Utf8]
        if string_cols:
            print(f"Found string columns that might be dates: {string_cols}")
            # Convert to DataFrame, process date columns, then back to LazyFrame
            df = detect_and_convert_date_columns(df)
            print(f"Schema after date detection: {df.schema}")
            return df.lazy()
        else:
            # If no string columns to check, just return the LazyFrame
            file_content.seek(0)  # Reset buffer position
            return pl.scan_parquet(file_content)
    except Exception as e:
        print(f"Error retrieving file from S3: {str(e)}")
        raise ValueError(f"Failed to retrieve file {file_name} from S3: {str(e)}")