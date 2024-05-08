import os
import logging
import boto3
from botocore.exceptions import NoCredentialsError, ProfileNotFound
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

s3_daily_path = 's3://tf-premium-parquet/public-postgres/farcaster/v2/full/'
local_full_path = os.path.abspath('./downloads/full')
s3_incremental_path = 's3://tf-premium-parquet/public-postgres/farcaster/v2/incremental/'
local_incremental_path = os.path.abspath('./downloads/incremental')
file_types = ['casts', 'fids', 'fnames', 'links', 'reactions', 'signers', 'storage', 'user_data', 'verifications']

try:
    session = boto3.Session(profile_name='neynar_parquet_exports')
    s3 = session.client('s3')
except ProfileNotFound as e:
    logging.error(f"AWS profile 'neynar_parquet_exports' not found. Please ensure it is configured correctly.")
    raise e

def file_already_downloaded(local_path, file_type):
    for file in os.listdir(local_path):
        if file_type in file and file.endswith('.parquet'):
            return True
    return False

def download_most_recent_file(s3_path, local_path, file_type):
    if file_already_downloaded(local_path, file_type):
        #logging.info(f"{file_type} file already downloaded, skipping new download.")
        return

    try:
        bucket_name = s3_path.split('/')[2]
        prefix = '/'.join(s3_path.split('/')[3:])
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        files = [file for file in response['Contents'] if file_type in file['Key'] and file['Key'].endswith('.parquet')]
        files.sort(key=lambda x: int(x['Key'].rsplit('.', 1)[0].rsplit('-', 1)[-1]), reverse=True)

        if files:
            most_recent_file = files[0]['Key']
            local_file_path = os.path.join(local_path, os.path.basename(most_recent_file))
            if not os.path.exists(local_file_path):
                s3.download_file(bucket_name, most_recent_file, local_file_path)
                #logging.info(f"Downloaded most recent file: {most_recent_file}")
            else:
                pass
                #logging.info(f"{most_recent_file} already downloaded.")
        else:
            logging.info(f"No files found for {file_type} in {s3_path}")
    except NoCredentialsError as e:
        logging.error(f"Failed to download the most recent file for {file_type} from {s3_path} to {local_path}: {str(e)}")

def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"Created directory: {path}")

def get_latest_full_timestamp(local_path, file_type):
    files = [f for f in os.listdir(local_path) if file_type in f and f.endswith('.parquet')]
    if not files:
        return None
    latest_file = max(files, key=lambda x: int(x.split('-')[-1].split('.')[0]))
    return int(latest_file.split('-')[-1].split('.')[0])


def delete_outdated_incremental_files(local_incremental_path, file_type, latest_full_timestamp):
    files_deleted_count = 0
    for file in os.listdir(local_incremental_path):
        if file_type in file and file.endswith('.parquet'):
            file_name_parts = file.split('-')
            if len(file_name_parts) == 4:
                try:
                    file_start_timestamp = int(file_name_parts[2])
                    file_end_timestamp = int(file_name_parts[3].split('.')[0])

                    if file_end_timestamp < latest_full_timestamp:
                        os.remove(os.path.join(local_incremental_path, file))
                        #logging.info(f"Deleted outdated incremental file: {file}")
                        files_deleted_count += 1
                except ValueError as e:
                    logging.error(f"Error processing file {file}: {e}")
            else:
                logging.error(f"Filename format is unexpected: {file}")

    if files_deleted_count > 0:
        #logging.info(f"Total of {files_deleted_count} outdated incremental files deleted for {file_type}.")
        pass


def download_incremental_files(bucket_name, local_incremental_path, file_type, latest_timestamp):
    prefix = '/'.join(s3_incremental_path.split('/')[3:])
    continuation_token = None

    while True:
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
                            #logging.info(f"Downloaded incremental file: {file_key}")

        continuation_token = response.get('NextContinuationToken', None)
        if not continuation_token:
            break

def manage_downloads():
    ensure_directory_exists(local_full_path)
    for file_type in file_types:
        download_most_recent_file(s3_daily_path, local_full_path, file_type)

    ensure_directory_exists(local_incremental_path)
    for file_type in file_types:
        latest_timestamp = get_latest_full_timestamp(local_full_path, file_type)
        if latest_timestamp:
            delete_outdated_incremental_files(local_incremental_path, file_type, latest_timestamp)
            #logging.info(f"Processing incremental files for {file_type} starting from timestamp {latest_timestamp}")
            download_incremental_files(s3_incremental_path.split('/')[2], local_incremental_path, file_type, latest_timestamp)


manage_downloads()
