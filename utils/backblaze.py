from django.conf import settings
from b2sdk.v2 import InMemoryAccountInfo, B2Api
import time
import pandas as pd
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


def upload_file_to_b2(file_path, filename, valid_duration=3600):
    """
    Reads an Excel file, converts it to Parquet, and uploads it to Backblaze B2.
    
    Args:
        file_path (str): The local path to the Excel file.
        filename (str): The name to store the file as in B2 (without extension).
        valid_duration (int): Time in seconds for which the pre-signed URL is valid.

    Returns:
        str: Pre-signed URL for the uploaded Parquet file.
    """

    # Read Excel file using Polars (faster than Pandas)
    df = pl.read_excel(file_path, engine="openpyxl")

    # Convert to Parquet with Snappy compression (optimized for speed & size)
    parquet_buffer = BytesIO()
    df.write_parquet(parquet_buffer, compression="snappy")
    parquet_buffer.seek(0)  # Reset buffer position

    # Get bucket info
    bucket = b2_api.get_bucket_by_name(BUCKET_NAME)

    # Define new Parquet filename
    parquet_filename = filename.replace(".xlsx", ".parquet")

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

    return pre_signed_url

def get_file_from_backblaze(file_name):
    bucket = b2_api.get_bucket_by_name(BUCKET_NAME)
    # Define new Parquet filename
    parquet_filename = file_name.replace(".xlsx", ".parquet")
    # Generate a pre-signed URL for the file
    # pre_signed_url = f"https://f005.backblazeb2.com/file/{BUCKET_NAME}/{parquet_filename}?Authorization={auth_token}"
    # Download the file into memory
    # file_key=f"file/{BUCKET_NAME}/{parquet_filename}" 
    downloaded_file = bucket.download_file_by_name(parquet_filename)
    file_content = BytesIO()
    downloaded_file.save(file_content)
    file_content.seek(0)
    # Read the Parquet file directly into a Polars DataFrame
    # df = pl.read_parquet(file_content) #dataframe
    df = pl.scan_parquet(file_content)
    return df


def upload_file_to_s3(file_path,cleaned_name,useremail):
    
    return 