import logging
import os

from download_or_update_files import (
    ensure_directory_exists,
    download_most_recent_file,
    get_latest_full_timestamp,
    delete_outdated_incremental_files,
    download_incremental_files,
)

# Define constants for paths and file types
s3_daily_path = 's3://tf-premium-parquet/public-postgres/farcaster/v2/full/'
s3_incremental_path = 's3://tf-premium-parquet/public-postgres/farcaster/v2/incremental/'
local_full_path = os.path.abspath('./downloads/full')
local_incremental_path = os.path.abspath('./downloads/incremental')
file_types = ['casts', 'fids', 'fnames', 'links', 'reactions', 'signers', 'storage', 'user_data', 'verifications']


def delete_all_full_files(local_full_path, file_types):
    for file_type in file_types:
        for file in os.listdir(local_full_path):
            if file_type in file and file.endswith('.parquet'):
                os.remove(os.path.join(local_full_path, file))
                logging.info(f"Deleted full file: {file}")


def main():
    # Download incremental files newer than current full files
    ensure_directory_exists(local_incremental_path)
    for file_type in file_types:
        latest_timestamp = get_latest_full_timestamp(local_full_path, file_type)
        if latest_timestamp:
            delete_outdated_incremental_files(local_incremental_path, file_type, latest_timestamp)
            download_incremental_files(s3_incremental_path.split('/')[2], local_incremental_path, file_type,
                                       latest_timestamp)

    # Delete full files
    delete_all_full_files(local_full_path, file_types)

    # Download new full files
    ensure_directory_exists(local_full_path)
    for file_type in file_types:
        download_most_recent_file(s3_daily_path, local_full_path, file_type)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
    logging.info("Update finished ;)")
