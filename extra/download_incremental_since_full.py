import os
import logging
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(dotenv_path)

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_env_variable(var_name):
    """ Retrieve environment variable or raise an error if not found. """
    value = os.getenv(var_name)
    if value is None:
        error_msg = f"Environment variable {var_name} is not set. Please check your .env file."
        logging.error(error_msg)
        raise ValueError(error_msg)
    return value

# Set AWS configuration from environment variables
os.environ['AWS_ACCESS_KEY_ID'] = get_env_variable('AWS_ACCESS_KEY_ID')
os.environ['AWS_SECRET_ACCESS_KEY'] = get_env_variable('AWS_SECRET_ACCESS_KEY')
os.environ['AWS_DEFAULT_REGION'] = get_env_variable('AWS_DEFAULT_REGION')

# AWS S3 and local paths for both full and incremental files
s3_full_path = 's3://tf-premium-parquet/public-postgres/farcaster/v2/full/'
local_full_path = os.path.abspath('../downloads/full')
s3_incremental_path = 's3://tf-premium-parquet/public-postgres/farcaster/v2/incremental/'
local_incremental_path = os.path.abspath('../downloads/incremental')
file_types = ['casts', 'fids', 'fnames', 'links', 'reactions', 'signers', 'storage', 'user_data', 'verifications']

def ensure_directory_exists(path):
    """ Ensure that the directory exists, and create it if it does not. """
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"Created directory: {path}")

def get_latest_full_timestamp(local_path, file_type):
    """ Get the timestamp of the latest downloaded full file for a given file type. """
    files = [f for f in os.listdir(local_path) if file_type in f and f.endswith('.parquet')]
    if not files:
        return None
    latest_file = max(files, key=lambda x: int(x.split('-')[-1].split('.')[0]))
    return int(latest_file.split('-')[-1].split('.')[0])

def download_incremental_files(bucket_name, local_incremental_path, file_type, latest_timestamp):
    """ Download all incremental files starting from the latest full file timestamp, handling pagination. """
    s3 = boto3.client('s3')
    prefix = '/'.join(s3_incremental_path.split('/')[3:])
    continuation_token = None

    while True:
        # Prepare request parameters dynamically to handle the continuation token correctly
        request_params = {
            'Bucket': bucket_name,
            'Prefix': prefix
        }
        if continuation_token:
            request_params['ContinuationToken'] = continuation_token

        response = s3.list_objects_v2(**request_params)

        if 'Contents' in response:
            for file in response['Contents']:
                file_key = file['Key']
                if file_type in file_key and file_key.endswith('.parquet'):
                    file_timestamp = int(file_key.rsplit('.', 1)[0].rsplit('-', 1)[-1])
                    if file_timestamp >= latest_timestamp:
                        local_file_path = os.path.join(local_incremental_path, os.path.basename(file_key))
                        if not os.path.exists(local_file_path):
                            s3.download_file(bucket_name, file_key, local_file_path)
                            logging.info(f"Downloaded incremental file: {file_key}")

        # Update the continuation token if present
        continuation_token = response.get('NextContinuationToken', None)
        if not continuation_token:
            break


def manage_downloads():
    """ Manage the download process for incremental files based on the timestamp of full files. """
    ensure_directory_exists(local_full_path)
    ensure_directory_exists(local_incremental_path)

    for file_type in file_types:
        latest_timestamp = get_latest_full_timestamp(local_full_path, file_type)
        if latest_timestamp:
            logging.info(f"Processing incremental files for {file_type} starting from timestamp {latest_timestamp}")
            download_incremental_files(s3_incremental_path.split('/')[2], local_incremental_path, file_type, latest_timestamp)
        else:
            logging.info(f"No existing full file found for {file_type}, skipping incremental download.")

manage_downloads()
print("Download process completed.")
