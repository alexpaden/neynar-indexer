import logging
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import gc
import psutil

import pyarrow.parquet as pq
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from models import Fids, Storage, Links, Casts, UserData, Reactions, Fnames, Signers, Verifications, WarpcastPowerUsers, ProfileWithAddresses

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

# Create an engine with an optimized connection pool
ENGINE = create_engine(
    CONNECTION_STRING,
    poolclass=QueuePool,
    pool_size=400,  # Increased from 50 to better utilize resources
    max_overflow=100,  # Increased from 10 to allow more connections during peak times
    pool_pre_ping=True,
    pool_recycle=1800  # Recycle connections after an hour
)
Session = sessionmaker(bind=ENGINE)

skip_tables = {}

# Increased batch size to better utilize resources
BATCH_SIZE = 200000  # Adjusted from 100k to 500k

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

def process_batch(orm_class, batch_data, retries=3):
    start_time = time.time()
    attempt = 0
    while attempt < retries:
        try:
            with Session() as session:
                insert_statement = insert(orm_class.__table__).on_conflict_do_nothing()
                session.execute(insert_statement, batch_data)
                session.commit()
            end_time = time.time()
            if attempt > 0:
                logger.info(f"Successful retry on attempt {attempt + 1}")
            return len(batch_data), end_time - start_time
        except (OperationalError, SQLAlchemyError) as e:
            attempt += 1
            logger.warning(f"Error on attempt {attempt}/{retries}: {e}")
            if attempt < retries:
                time.sleep(2 ** attempt)  # Exponential backoff
        finally:
            session.close()
    logger.error(f"Failed to process batch of {len(batch_data)} rows after {retries} attempts")
    return 0, 0

def process_chunk(orm_class, chunk, batch_size):
    total_rows = 0
    total_time = 0
    batch_data = []

    for row in chunk.to_pylist():
        row_data = {key: value for key, value in row.items() if key in orm_class.__table__.columns.keys()}
        batch_data.append(row_data)

        if len(batch_data) >= batch_size:
            rows, batch_time = process_batch(orm_class, batch_data)
            total_rows += rows
            total_time += batch_time
            batch_data = []

    if batch_data:
        rows, batch_time = process_batch(orm_class, batch_data)
        total_rows += rows
        total_time += batch_time

    return total_rows, total_time

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
        'warpcast_power_users': WarpcastPowerUsers,
        'profile_with_addresses': ProfileWithAddresses
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

    # Determine the number of CPU cores and available memory
    num_cores = psutil.cpu_count(logical=False)
    available_memory = psutil.virtual_memory().available

    # Calculate chunk size based on available memory (aim for ~10% of available memory per chunk)
    chunk_size = max(10000, int(available_memory * 0.1 / (num_cores * 8)))  # Assuming 8 bytes per value on average

    with pq.ParquetFile(file_path) as pf:
        num_row_groups = pf.num_row_groups
        with ProcessPoolExecutor(max_workers=num_cores) as executor:
            futures = []
            for row_group in range(num_row_groups):
                table = pf.read_row_group(row_group)
                for chunk_start in range(0, len(table), chunk_size):
                    chunk = table.slice(chunk_start, chunk_size)
                    futures.append(executor.submit(process_chunk, orm_class, chunk, BATCH_SIZE))

            for future in as_completed(futures):
                rows, chunk_time = future.result()
                total_rows += rows
                total_time += chunk_time
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
