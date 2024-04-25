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

# AWS S3 and local paths
s3_daily_path = 's3://tf-premium-parquet/public-postgres/farcaster/v2/full/'
local_full_path = os.path.abspath('../downloads/full')
file_types = ['casts', 'fids', 'fnames', 'links', 'reactions', 'signers', 'storage', 'user_data', 'verifications']

def file_already_downloaded(local_path, file_type):
    """ Check if any file of the specified type already exists in the local directory. """
    for file in os.listdir(local_path):
        if file_type in file and file.endswith('.parquet'):
            return True
    return False

def download_most_recent_file(s3_path, local_path, file_type):
    """ Download the most recent Parquet file from S3 based on a specific file type if not already downloaded. """
    if file_already_downloaded(local_path, file_type):
        logging.info(f"{file_type} file already downloaded, skipping new download.")
        return

    try:
        s3 = boto3.client('s3')
        bucket_name = s3_path.split('/')[2]  # extract the bucket name from the s3 path
        prefix = '/'.join(s3_path.split('/')[3:])  # extract the prefix from the s3 path
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        files = [file for file in response['Contents'] if file_type in file['Key'] and file['Key'].endswith('.parquet')]
        files.sort(key=lambda x: int(x['Key'].rsplit('.', 1)[0].rsplit('-', 1)[-1]), reverse=True)  # Correctly extract timestamp before .parquet

        if files:
            most_recent_file = files[0]['Key']
            local_file_path = os.path.join(local_path, os.path.basename(most_recent_file))
            if not os.path.exists(local_file_path):
                s3.download_file(bucket_name, most_recent_file, local_file_path)
                logging.info(f"Downloaded most recent file: {most_recent_file}")
            else:
                logging.info(f"{most_recent_file} already downloaded.")
        else:
            logging.info(f"No files found for {file_type} in {s3_path}")
    except NoCredentialsError as e:
        logging.error(f"Failed to download the most recent file for {file_type} from {s3_path} to {local_path}: {str(e)}")

def ensure_directory_exists(path):
    """ Ensure that the directory exists, and create it if it does not. """
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"Created directory: {path}")

def manage_downloads():
    """ Manage the download process for each file type. """
    ensure_directory_exists(local_full_path)
    for file_type in file_types:
        download_most_recent_file(s3_daily_path, local_full_path, file_type)

manage_downloads()
print("Download process completed.")
