import logging
import os
import sys
import threading
from collections import defaultdict
from datetime import datetime

import pyarrow.parquet as pq
from dotenv import load_dotenv
from filelock import FileLock, Timeout
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

from models import Fids, Storage, Links, Casts, UserData, Reactions, Fnames, Signers, Verifications, FileTracking, WarpcastPowerUsers, ProfileWithAddresses

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

required_env_vars = ['DB_NAME', 'DB_USER', 'DB_PASS', 'DB_HOST', 'DB_PORT']
env_vars = {var: os.getenv(var) for var in required_env_vars}

if None in env_vars.values():
    missing_vars = [var for var, value in env_vars.items() if value is None]
    logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

CONNECTION_STRING = f"postgresql://{env_vars['DB_USER']}:{env_vars['DB_PASS']}@{env_vars['DB_HOST']}:{env_vars['DB_PORT']}/{env_vars['DB_NAME']}"

ENGINE = create_engine(CONNECTION_STRING)
Session = sessionmaker(bind=ENGINE)

skip_tables = {'links'}
#skip_tables = {}


def run_sql_script(filename):
    with open(filename, 'r') as file:
        sql_script = file.read()
    statements = [s.strip() for s in sql_script.split(';') if s.strip()]
    conn = ENGINE.raw_connection()
    cursor = conn.cursor()
    try:
        for statement in statements:
            if statement:
                cursor.execute(statement)
        conn.commit()
        logging.info("SQL script executed successfully.")
    except Exception as e:
        conn.rollback()
        logging.error(f"Failed to execute SQL script: {e}")
    finally:
        cursor.close()
        conn.close()


def file_already_processed(file_name):
    session = Session()
    exists = session.query(FileTracking).filter(FileTracking.file_name == file_name).one_or_none() is not None
    session.close()
    return exists


def record_file_as_processed(file_name):
    session = Session()
    tracking_entry = FileTracking(file_name=file_name)
    session.add(tracking_entry)
    session.commit()
    session.close()


def extract_timestamp(filename):
    parts = filename.split('-')
    try:
        if len(parts) > 3 and parts[-2].isdigit() and parts[-1].split('.')[0].isdigit():
            start_timestamp = int(parts[-2])
            end_timestamp = int(parts[-1].split('.')[0])
            return max(start_timestamp, end_timestamp)
        elif parts[-1].split('.')[0].isdigit():
            return int(parts[-1].split('.')[0])
        else:
            raise ValueError("No valid timestamp found in filename.")
    except ValueError as e:
        raise ValueError(f"Error extracting timestamp from {filename}: {e}")


def convert_unix_to_datetime(unix_time):
    return datetime.utcfromtimestamp(unix_time)


def table_is_empty(table_name):
    query = text(f"SELECT EXISTS (SELECT 1 FROM {table_name} LIMIT 1)")
    with ENGINE.connect() as conn:
        result = conn.execute(query)
        return not result.scalar()


def process_category_files(files, path, incremental):
    """Process files for a specific category in chronological order."""
    for file in files:
        file_path = os.path.join(path, file)
        try:
            process_file(file_path, incremental)
        except Exception as e:
            logging.error(f"Error processing file {file}: {e}")


def process_file(file_path, incremental=False):
    file_name = os.path.basename(file_path)
    table_name = file_name.split('-')[1].split('.')[0]

    orm_class_dict = {
        'fids': Fids,
        'storage': Storage,
        'links': Links,
        'casts': Casts,
        'user_data': UserData,
        'reactions': Reactions,
        'fnames': Fnames,
        'signers': Signers,
        'verifications': Verifications,
        'warpcast_power_users': WarpcastPowerUsers,
        'profile_with_addresses': ProfileWithAddresses
    }

    if table_name in skip_tables:
        logging.info(f"Skipping file {file_name} associated with table {table_name}")
        return

    lock_path = f'/tmp/{file_name}.lock'
    lock = FileLock(lock_path)

    try:
        with lock.acquire(timeout=0), Session() as session:
            if incremental and file_already_processed(file_name):
                logging.info(f"Skipping already processed file {file_name}")
                return

            orm_class = orm_class_dict.get(table_name)
            if not orm_class or (not incremental and not table_is_empty(table_name)):
                logging.info(f"No action taken for table '{table_name}' from file '{file_name}'")
                return

            logging.info(f"Processing file {file_name} for table {table_name}")

            with pq.ParquetFile(file_path) as pf:
                iterator = pf.iter_batches(batch_size=2000000)
                total_rows = 0
                for batch in iterator:
                    data = batch.to_pydict()
                    table_columns = {column.name for column in orm_class.__table__.columns}
                    filtered_data = []
                    for i in range(len(batch)):
                        row_data = {key: value[i] for key, value in data.items() if key in table_columns}
                        filtered_data.append(row_data)

                        if incremental:
                            primary_key = [key.name for key in orm_class.__table__.primary_key.columns][0]
                            insert_statement = insert(orm_class.__table__).on_conflict_do_update(
                                index_elements=[primary_key],
                                set_={key: value for key, value in row_data.items() if key != primary_key}
                            )
                        else:
                            insert_statement = insert(orm_class.__table__).on_conflict_do_nothing()

                        session.execute(insert_statement, [row_data])
                        total_rows += 1

                    logging.info(f"Processed {total_rows} rows so far for file {file_name}")

                session.commit()
                logging.info(f"File {file_name} processed: {total_rows} rows inserted/updated")

                if incremental:
                    record_file_as_processed(file_name)
    except Timeout:
        logging.info(f"Skipping locked file {file_name}")


def main():
    run_sql_script('./sql/setup.sql')

    full_path = './downloads/full'
    incremental_path = './downloads/incremental'

    # Process full files first, sequentially, sorted by timestamp
    full_files = sorted(os.listdir(full_path), key=lambda f: extract_timestamp(f))
    for file in full_files:
        file_path = os.path.join(full_path, file)
        try:
            process_file(file_path, incremental=False)
        except Exception as e:
            logging.error(e)

    # Categorize incremental files by type and sort them by timestamp within each category
    categorized_files = defaultdict(list)
    for file in os.listdir(incremental_path):
        try:
            category = file.split('-')[1]  # Assuming category is defined in the filename
            categorized_files[category].append(file)
        except IndexError:
            logging.error(f"Filename format error: {file}")
            continue

    for category in categorized_files:
        categorized_files[category] = sorted(categorized_files[category], key=lambda f: extract_timestamp(f))

    threads = []
    for category, files in categorized_files.items():
        thread = threading.Thread(target=process_category_files, args=(files, incremental_path, True))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
    logging.info("Script finished")
