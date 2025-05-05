from django.conf import settings
from b2sdk.v2 import InMemoryAccountInfo, B2Api
import time
# import pandas as pd
import requests
from io import BytesIO
import polars as pl

KEY_ID = settings.__getattr__("BACKBLAZE_KEY_ID")
KEY_APPLICATION_KEY = settings.__getattr__("BACKBLAZE_APP_KEY")
BUCKET_NAME = settings.__getattr__("BACKBLAZE_BUCKET")

# Initialize B2 API
info = InMemoryAccountInfo()
b2_api = B2Api(info)

# Authenticate
b2_api.authorize_account('production', KEY_ID, KEY_APPLICATION_KEY)

# def upload_file_to_b2(file_path, filename, valid_duration=3600):
#     """
#     Uploads a file to Backblaze B2 and generates a pre-signed URL for access.

#     Args:
#         file_path (str): The local path to the file.
#         filename (str): The name to store the file as in B2.
#         valid_duration (int): Time in seconds for which the pre-signed URL is valid.

#     Returns:
#         str: Pre-signed URL for the uploaded file.
#     """
#     # Get bucket info
#     bucket = b2_api.get_bucket_by_name(BUCKET_NAME)
#     # Upload file
#     with open(file_path, 'rb') as file:
#         bucket.upload_bytes(file.read(), filename)

#     # Generate a pre-signed URL for the file
#     auth_token = bucket.get_download_authorization(filename, valid_duration)

#     pre_signed_url =f"https://f005.backblazeb2.com/file/{BUCKET_NAME}/{filename}?Authorization={auth_token}"


#     # # response = requests.head(pre_signed_url)
#     # response = requests.get(pre_signed_url, stream=True)
#     # if response.status_code == 200:
#     #     # Read file into pandas
#     #     df = pd.read_excel(BytesIO(response.content), engine="openpyxl")
#     #     print(df.head())  # Display first few rows
#     # else:
#     #     print("Failed to download file:", response.status_code, response.text)
#     return pre_signed_url


# def upload_file_to_b2(file_path, filename, valid_duration=3600):
#     """
#     Reads an Excel file, converts it to Parquet, and uploads it to Backblaze B2.

#     Args:
#         file_path (str): The local path to the Excel file.
#         filename (str): The name to store the file as in B2 (without extension).
#         valid_duration (int): Time in seconds for which the pre-signed URL is valid.

#     Returns:
#         str: Pre-signed URL for the uploaded Parquet file.
#     """
#     import polars as pl
#     # Read Excel file
#     df = pl.read_excel(file_path, engine="openpyxl")

#     # Convert DataFrame to Parquet and store in memory
#     parquet_buffer = BytesIO()
#     df.to_parquet(parquet_buffer, engine="pyarrow", index=False)

#     # Reset buffer position to the beginning
#     parquet_buffer.seek(0)

#     # Get bucket info
#     bucket = b2_api.get_bucket_by_name(BUCKET_NAME)

#     # Define new Parquet filename
#     parquet_filename = filename.replace(".xlsx", ".parquet")

#     # Upload Parquet file
#     bucket.upload_bytes(parquet_buffer.getvalue(), parquet_filename)

#     # Generate a pre-signed URL for the file
#     auth_token = bucket.get_download_authorization(parquet_filename, valid_duration)

#     pre_signed_url = f"https://f005.backblazeb2.com/file/{BUCKET_NAME}/{parquet_filename}?Authorization={auth_token}"

#     print("*********************")
#     print("Pre-Signed URL:", pre_signed_url)
#     response = requests.get(pre_signed_url, stream=True)
#     if response.status_code == 200:
#         # Load the Parquet file into a DataFrame
#         parquet_buffer = BytesIO(response.content)
#         # df = pd.read_parquet(parquet_buffer, engine="pyarrow")  # or engine="fastparquet"
#         df = pl.read_parquet(parquet_buffer)
#         print(df)

#     return pre_signed_url


def upload_file_to_b2(file_path, filename, valid_duration=3600, extract_metadata=False):
    """
    Reads a CSV or Excel file, converts it to Parquet, and uploads it to Backblaze B2.

    Args:
        file_path (str): The local path to the file (CSV or Excel).
        filename (str): The name to store the file as in B2.
        valid_duration (int): Time in seconds for which the pre-signed URL is valid.
        extract_metadata (bool): Whether to extract and return metadata about the file.

    Returns:
        dict: Dictionary containing the pre-signed URL and metadata if extract_metadata is True,
              otherwise just the pre-signed URL as a string.
    """
    from utils.aggregate import extract_dataset_metadata
    import os

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

    # Extract metadata if requested
    metadata = None
    if extract_metadata:
        metadata = extract_dataset_metadata(df)

    # Convert to Parquet with Snappy compression (optimized for speed & size)
    parquet_buffer = BytesIO()
    df.write_parquet(parquet_buffer, compression="snappy")
    parquet_buffer.seek(0)  # Reset buffer position

    # Get bucket info
    bucket = b2_api.get_bucket_by_name(BUCKET_NAME)

    # Define new Parquet filename (preserve original name but change extension)
    base_filename = os.path.splitext(filename)[0]
    parquet_filename = f"{base_filename}.parquet"

    # Upload Parquet file
    bucket.upload_bytes(parquet_buffer.getvalue(), parquet_filename)

    # Generate a pre-signed URL for the file
    auth_token = bucket.get_download_authorization(parquet_filename, valid_duration)
    pre_signed_url = f"https://f005.backblazeb2.com/file/{BUCKET_NAME}/{parquet_filename}?Authorization={auth_token}"

    print("*********************")
    print("Pre-Signed URL:", pre_signed_url)

    # Download and read Parquet using Polars
    response = requests.get(pre_signed_url, stream=True)
    if response.status_code == 200:
        download_buffer = BytesIO()
        for chunk in response.iter_content(chunk_size=8192):  # Efficient streaming
            download_buffer.write(chunk)
        download_buffer.seek(0)

        df = pl.read_parquet(download_buffer)
        print(df.head())
        print("*******")
        print(df.height)  # Display first few rows
    else:
        print("Failed to download file:", response.status_code, response.text)

    if extract_metadata:
        return {
            "url": pre_signed_url,
            "filename": parquet_filename,
            "metadata": metadata
        }
    else:
        return pre_signed_url

def get_file_from_backblaze(file_name):
    """
    Retrieves a file from Backblaze B2 and loads it into a Polars DataFrame.

    Args:
        file_name (str): The name of the file to retrieve.

    Returns:
        pl.LazyFrame: A Polars LazyFrame containing the file data.
    """
    import os

    bucket = b2_api.get_bucket_by_name(BUCKET_NAME)

    # Determine file extension (case-insensitive)
    file_extension = os.path.splitext(file_name.lower())[1]

    # Define Parquet filename based on original file extension
    base_filename = os.path.splitext(file_name)[0]
    parquet_filename = f"{base_filename}.parquet"

    try:
        # Download the file into memory
        downloaded_file = bucket.download_file_by_name(parquet_filename)
        file_content = BytesIO()
        downloaded_file.save(file_content)
        file_content.seek(0)

        # Read the Parquet file into a Polars LazyFrame for efficient processing
        df = pl.scan_parquet(file_content)
        return df
    except Exception as e:
        print(f"Error retrieving file from Backblaze: {str(e)}")
        raise ValueError(f"Failed to retrieve file {file_name} from Backblaze: {str(e)}")


def upload_file_to_s3(file_path,cleaned_name,useremail):

    return