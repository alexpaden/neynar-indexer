import logging
import os

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
file_types = ['casts', 'fids', 'fnames', 'links', 'reactions', 'signers', 'storage', 'user_data', 'verifications', 'warpcast_power_users', 'profile_with_addresses']

try:
    session = boto3.Session(profile_name='neynar_parquet_exports')
    s3 = session.client('s3')
except ProfileNotFound as e:
    logging.error("AWS profile 'neynar_parquet_exports' not found. Please ensure it is configured correctly.")
    raise e


def file_already_downloaded(local_path, file_type):
    for file in os.listdir(local_path):
        if file_type in file and file.endswith('.parquet'):
            return True
    return False


def download_most_recent_file(s3_path, local_path, file_type):
    if file_already_downloaded(local_path, file_type):
        return

    try:
        bucket_name = s3_path.split('/')[2]
        prefix = '/'.join(s3_path.split('/')[3:])
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        files = [file for file in response['Contents'] if file_type in file['Key'] and file['Key'].endswith('.parquet')]
        files.sort(key=lambda x: int(x['Key'].rsplit('.', 1)[0].rsplit('-', 1)[-1]), reverse=True)

        if files:
            most_recent_file = files[0]['Key']
            file_size = files[0]['Size']
            logging.info(f"Most recent file: {most_recent_file}, Size: {file_size} bytes")
            local_file_path = os.path.join(local_path, os.path.basename(most_recent_file))
            if not os.path.exists(local_file_path):
                s3.download_file(bucket_name, most_recent_file, local_file_path)
        else:
            logging.info(f"No files found for {file_type} in {s3_path}")
    except NoCredentialsError as e:
        logging.error(
            f"Failed to download the most recent file for {file_type} from {s3_path} to {local_path}: {str(e)}")


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
                        files_deleted_count += 1
                except ValueError as e:
                    logging.error(f"Error processing file {file}: {e}")
            else:
                logging.error(f"Filename format is unexpected: {file}")


def download_incremental_files(bucket_name, local_incremental_path, file_type, latest_timestamp):
    prefix = '/'.join(s3_incremental_path.split('/')[3:])
    continuation_token = None
    while True:
        request_params = {'Bucket': bucket_name, 'Prefix': prefix}
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
        continuation_token = response.get('NextContinuationToken', None)
        if not continuation_token:
            break


def get_available_file_types(s3_path):
    bucket_name = s3_path.split('/')[2]
    prefix = '/'.join(s3_path.split('/')[3:])
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    file_types = {}
    latest_timestamp = 0

    if 'Contents' in response:
        files = response['Contents']
        files.sort(key=lambda x: x['LastModified'], reverse=True)
        recent_files = files[:14]  # Get the most recent 20 files

        for file in recent_files:
            file_name = file['Key'].split('/')[-1]
            logging.info(f"File found: {file_name}")
            if file_name.endswith('.parquet'):
                file_parts = file_name.split('-')
                if len(file_parts) > 1:
                    file_type = file_parts[0]
                    try:
                        timestamp = int(file_parts[-1].split('.')[0])
                    except ValueError:
                        logging.error(f"Error parsing timestamp from file name: {file_name}")
                        continue

                    if timestamp > latest_timestamp:
                        latest_timestamp = timestamp
                        file_types = {file_type: timestamp}
                    elif timestamp == latest_timestamp:
                        file_types[file_type] = timestamp

    # Log the available file types and their timestamps
    logging.info(f"Available file types in {s3_path} (timestamp {latest_timestamp}):")
    for file_type, timestamp in file_types.items():
        logging.info(f"  - {file_type}: {timestamp}")

    return file_types, latest_timestamp


def main():

    ensure_directory_exists(local_full_path)

    # Log available file types for full dataset
    full_types, full_timestamp = get_available_file_types(s3_daily_path)
    logging.info(f"Available file types in full dataset (timestamp {full_timestamp}):")
    for file_type in sorted(full_types.keys()):
        logging.info(f"  - {file_type}")


    for file_type in file_types:
        download_most_recent_file(s3_daily_path, local_full_path, file_type)
    ensure_directory_exists(local_incremental_path)
    for file_type in file_types:
        latest_timestamp = get_latest_full_timestamp(local_full_path, file_type)
        if latest_timestamp:
            delete_outdated_incremental_files(local_incremental_path, file_type, latest_timestamp)
            download_incremental_files(s3_incremental_path.split('/')[2], local_incremental_path, file_type,
                                       latest_timestamp)


if __name__ == "__main__":
    main()
    logging.info("finished ;)")