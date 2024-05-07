import os
import sys

import pyarrow.parquet as pq
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from models import Base, Fids, Storage, Links, Casts, UserData, Reactions, Fnames, Signers, Verifications, FileTracking
import logging
from dotenv import load_dotenv
from filelock import FileLock, Timeout
from datetime import datetime

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

#skip_tables = {'links'}
skip_tables = {}

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
    # Query to check if at least one row exists
    query = text(f"SELECT EXISTS (SELECT 1 FROM {table_name} LIMIT 1)")
    with ENGINE.connect() as conn:
        result = conn.execute(query)
        # Return True if no rows exist
        return not result.scalar()


def process_file(file_path, incremental=False):
    file_name = os.path.basename(file_path)
    table_name = file_name.split('-')[1].split('.')[0]
    if table_name in skip_tables:
        #logging.info(f"Skipping file {file_name} associated with table {table_name}")
        return

    lock_path = f'/tmp/{file_name}.lock'
    lock = FileLock(lock_path)

    try:
        with lock.acquire(timeout=0):  # Non-blocking attempt
            if incremental and file_already_processed(file_name):
                #logging.info(f"Skipping already processed file {file_name}")
                return

            orm_class = {
                'fids': Fids,
                'storage': Storage,
                'links': Links,
                'casts': Casts,
                'user_data': UserData,
                'reactions': Reactions,
                'fnames': Fnames,
                'signers': Signers,
                'verifications': Verifications
            }.get(table_name)

            if not orm_class or (not incremental and not table_is_empty(table_name)):
                logging.info(f"No action taken for table '{table_name}' from file '{file_name}'")
                return

            with pq.ParquetFile(file_path) as pf:
                iterator = pf.iter_batches(batch_size=4000000)  # Adjust batch size based on your memory constraints
                session = Session()
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

                    session.execute(insert_statement, filtered_data)
                    session.commit()
                    total_rows += len(filtered_data)

                logging.info(f"File {file_name} processed: {total_rows} rows inserted/updated")
                if incremental:
                    record_file_as_processed(file_name)
            session.close()
    except Timeout:
        pass
        #logging.info(f"Skipping locked file {file_name}")


def main():
    run_sql_script('./sql/setup.sql')

    full_path = './downloads/full'
    newest_full_timestamp = datetime.min
    for file in os.listdir(full_path):
        file_path = os.path.join(full_path, file)
        try:
            unix_timestamp = extract_timestamp(file)
            timestamp = convert_unix_to_datetime(unix_timestamp)
            if timestamp > newest_full_timestamp:
                newest_full_timestamp = timestamp
            process_file(file_path, incremental=False)
        except ValueError as e:
            logging.error(e)
            continue

    incremental_path = './downloads/incremental'
    for file in os.listdir(incremental_path):
        file_path = os.path.join(incremental_path, file)
        try:
            unix_timestamp = extract_timestamp(file)
            timestamp = convert_unix_to_datetime(unix_timestamp)
            if timestamp >= newest_full_timestamp:
                process_file(file_path, incremental=True)
        except ValueError as e:
            logging.error(e)
            continue

if __name__ == "__main__":
    main()
    logging.info("Script finished")

