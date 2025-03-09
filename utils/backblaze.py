from django.conf import settings
from b2sdk.v2 import InMemoryAccountInfo,B2Api

KEY_ID = settings.__getattr__("BACKBLAZE_KEY_ID")
KEY_APPLICATION_KEY = settings.__getattr__("BACKBLAZE_APP_KEY")
BUCKET_NAME=settings.__getattr__("BACKBLAZE_BUCKET")

#initialize B2 API
info = InMemoryAccountInfo()
b2_api = B2Api(info)
#authenticate
b2_api.authorize_account('production',KEY_ID,KEY_APPLICATION_KEY)

def upload_file_to_b2(file_path,filename):
    #get bucket info
    bucket = b2_api.get_bucket_by_name(BUCKET_NAME)
    #get upload token
    # upload_token = b2_api.authorize_upload(BUCKET_NAME)
    with open(file_path,'rb') as file:
        uploaded_file = bucket.upload_bytes(file.read(),filename)

    uploaded_file = f"https://s3.us-east-005.backblazeb2.com/file/{BUCKET_NAME}/{filename}"

    print("*********************")
    print(uploaded_file)
    return

