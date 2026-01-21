import os
import boto3

data_lake_r2 = None

def get_data_lake_r2():
    global data_lake_r2
    if data_lake_r2 is None and os.getenv("CF_R2_DATA_LAKE_URL"):
        data_lake_r2 = boto3.client(
            service_name="s3",
            endpoint_url=os.getenv("CF_R2_DATA_LAKE_URL"),
            aws_access_key_id=os.getenv("CF_R2_DATA_LAKE_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("CF_R2_DATA_LAKE_SECRET_ACCESS_KEY"),
            region_name="auto",
        )
    return data_lake_r2
