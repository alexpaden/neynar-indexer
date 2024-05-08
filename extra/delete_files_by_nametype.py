import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

LOCAL_INCREMENTAL_PATH = os.getenv('LOCAL_INCREMENTAL_PATH', './downloads/incremental')

def delete_files_by_names(local_path, substrings):
    files_deleted_count = 0
    try:
        files = os.listdir(local_path)
        for file in files:
            if any(substring in file for substring in substrings):
                file_path = os.path.join(local_path, file)
                os.remove(file_path)
                logging.info(f"Deleted file: {file}")
                files_deleted_count += 1

        logging.info(f"Total of {files_deleted_count} files deleted.")
    except Exception as e:
        logging.error(f"Failed to delete files: {str(e)}")

def main():
    # List of substrings to search for in the file names
    substrings_to_search = ["links", "fids", "casts", "fnames", "signers", "storage", "user_data", "verifications"]
    delete_files_by_names(LOCAL_INCREMENTAL_PATH, substrings_to_search)

if __name__ == "__main__":
    main()
