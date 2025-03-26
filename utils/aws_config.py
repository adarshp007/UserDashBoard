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
        s3.upload_file(temp_file_path, settings.AWS_STORAGE_BUCKET_NAME, s3_path)
    except Exception as e:
        raise e
    
    # Delete the temporary file
    os.remove(temp_file_path)
    return s3_path

def upload_file_to_s3(file_path,clean_filename,user_email):

    s3 = get_boto_client()
    s3_path = f'datasets/{user_email.replace("@", "_").replace(".", "_")}/{clean_filename}'
    try:
        s3.upload_file(file_path, settings.AWS_BUCKET, s3_path)
    except Exception as e:
        raise e
    return s3_path