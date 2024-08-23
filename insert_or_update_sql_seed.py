import logging
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import time

import pyarrow.parquet as pq
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from models import Fids, Storage, Links, Casts, UserData, Reactions, Fnames, Signers, Verifications, WarpcastPowerUsers

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

required_env_vars = ['DB_NAME', 'DB_USER', 'DB_PASS', 'DB_HOST', 'DB_PORT']
env_vars = {var: os.getenv(var) for var in required_env_vars}

if None in env_vars.values():
    missing_vars = [var for var, value in env_vars.items() if value is None]
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

CONNECTION_STRING = f"postgresql://{env_vars['DB_USER']}:{env_vars['DB_PASS']}@{env_vars['DB_HOST']}:{env_vars['DB_PORT']}/{env_vars['DB_NAME']}"

# Create an engine with a large connection pool
ENGINE = create_engine(
    CONNECTION_STRING,
    poolclass=QueuePool,
    pool_size=200,  # Adjust based on your needs, but keep it below the 250 limit
    max_overflow=50,
    pool_pre_ping=True
)
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
        logger.info("SQL script executed successfully.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to execute SQL script: {e}")
    finally:
        cursor.close()
        conn.close()


def table_is_empty(table_name):
    query = text(f"SELECT EXISTS (SELECT 1 FROM {table_name} LIMIT 1)")
    with ENGINE.connect() as conn:
        result = conn.execute(query)
        return not result.scalar()


# Define a batch size
BATCH_SIZE = 1000000  # Adjust this value based on your needs and system capabilities


def process_batch(orm_class, batch_data):
    start_time = time.time()
    with Session() as session:
        insert_statement = insert(orm_class.__table__).on_conflict_do_nothing()
        session.execute(insert_statement, batch_data)
        session.commit()
    end_time = time.time()
    return len(batch_data), end_time - start_time


def process_file(file_path):
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
        'warpcast_power_users': WarpcastPowerUsers
    }

    if table_name in skip_tables:
        logger.info(f"Skipping file {file_name} associated with table {table_name}")
        return

    orm_class = orm_class_dict.get(table_name)
    if not orm_class or not table_is_empty(table_name):
        logger.info(f"No action taken for table '{table_name}' from file '{file_name}'")
        return

    logger.info(f"Starting to process file {file_name} for table {table_name}")

    total_rows = 0
    total_time = 0
    start_time = time.time()

    with pq.ParquetFile(file_path) as pf:
        table_columns = {column.name for column in orm_class.__table__.columns}

        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count() * 16) as executor:
            futures = []
            batch_data = []
            for row_group in pf.iter_batches():
                data = row_group.to_pydict()
                for i in range(len(row_group)):
                    row_data = {key: value[i] for key, value in data.items() if key in table_columns}
                    batch_data.append(row_data)

                    if len(batch_data) >= BATCH_SIZE:
                        futures.append(executor.submit(process_batch, orm_class, batch_data))
                        batch_data = []

            # Process any remaining data
            if batch_data:
                futures.append(executor.submit(process_batch, orm_class, batch_data))

            for i, future in enumerate(as_completed(futures)):
                rows, batch_time = future.result()
                total_rows += rows
                total_time += batch_time
                if (i + 1) % 10 == 0 or i == len(futures) - 1:  # Log every 10 batches or at the end
                    logger.info(f"Processed {total_rows} rows in {total_time:.2f} seconds. "
                                f"Average rate: {total_rows / total_time:.2f} rows/second")

    end_time = time.time()
    total_file_time = end_time - start_time
    logger.info(f"File {file_name} processed: {total_rows} rows in {total_file_time:.2f} seconds. "
                f"Overall rate: {total_rows / total_file_time:.2f} rows/second")


def main():
    run_sql_script('./sql/setup.sql')

    full_path = './downloads/full'

    full_files = [f for f in os.listdir(full_path) if f.endswith('.parquet')]

    total_files = len(full_files)
    for i, file in enumerate(full_files, 1):
        file_path = os.path.join(full_path, file)
        logger.info(f"Processing file {i} of {total_files}: {file}")
        start_time = time.time()
        try:
            process_file(file_path)
        except Exception as e:
            logger.error(f"Error processing file {file}: {e}")
        end_time = time.time()
        logger.info(f"Total processing time for {file}: {end_time - start_time:.2f} seconds")
        logger.info(f"Completed {i}/{total_files} files")


if __name__ == "__main__":
    main_start_time = time.time()
    main()
    main_end_time = time.time()
    logger.info(f"Script finished. Total execution time: {main_end_time - main_start_time:.2f} seconds")
