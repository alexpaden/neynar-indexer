import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import gc
import psutil
from memory_profiler import profile
import threading

import pyarrow.parquet as pq
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, event
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

# Create an engine with a large connection pool
keepalive_kwargs = {
    "keepalives": 1,
    "keepalives_idle": 30,
    "keepalives_interval": 5,
    "keepalives_count": 5,
}

ENGINE = create_engine(
    CONNECTION_STRING,
    poolclass=QueuePool,
    pool_size=150,
    max_overflow=50,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 30, **keepalive_kwargs}
)
Session = sessionmaker(bind=ENGINE)

skip_tables = {}

# Define a batch size
BATCH_SIZE = 10000  # Adjusted batch size

def connection_record_info(conn, record):
    logger.debug(f"Connection record: {record}")

event.listen(ENGINE, 'checkout', connection_record_info)

def memory_monitor():
    while True:
        process = psutil.Process()
        logger.info(f"Memory usage: {process.memory_info().rss / (1024 * 1024):.2f} MB")
        time.sleep(60)  # Log every minute

threading.Thread(target=memory_monitor, daemon=True).start()

def log_memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    logger.info(f"Memory usage: {memory_info.rss / (1024 * 1024):.2f} MB")

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

@profile
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
            session.close()  # Ensure the session is closed
    logger.error(f"Failed to process batch of {len(batch_data)} rows after {retries} attempts")
    return 0, 0  # Return 0 rows processed and 0 time if all attempts fail

@profile
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

    with pq.ParquetFile(file_path) as pf:
        table_columns = {column.name for column in orm_class.__table__.columns}

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            batch_data = []
            for row_group in pf.iter_batches(batch_size=BATCH_SIZE):
                data = row_group.to_pydict()
                for i in range(len(row_group)):
                    row_data = {key: value[i] for key, value in data.items() if key in table_columns}
                    batch_data.append(row_data)

                    if len(batch_data) >= BATCH_SIZE:
                        logger.debug(f"Created batch of size {len(batch_data)}")
                        futures.append(executor.submit(process_batch, orm_class, batch_data))
                        logger.debug(f"Submitted batch for processing")
                        batch_data = []
                        gc.collect()

            if batch_data:
                futures.append(executor.submit(process_batch, orm_class, batch_data))
                gc.collect()

            for i, future in enumerate(as_completed(futures)):
                try:
                    rows, batch_time = future.result()
                    total_rows += rows
                    total_time += batch_time
                    if (i + 1) % 10 == 0 or i == len(futures) - 1:
                        logger.info(f"Processed {total_rows} rows in {total_time:.2f} seconds. "
                                    f"Average rate: {total_rows / total_time:.2f} rows/second")
                        log_memory_usage()
                except Exception as e:
                    logger.error(f"Error processing batch: {e}")

    del pf
    gc.collect(generation=2)  # Force full collection

    end_time = time.time()
    total_file_time = end_time - start_time
    logger.info(f"File {file_name} processed: {total_rows} rows in {total_file_time:.2f} seconds. "
                f"Overall rate: {total_rows / total_file_time:.2f} rows/second")
    log_memory_usage()

@profile
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
        log_memory_usage()
        gc.collect(generation=2)  # Force full collection after each file

if __name__ == "__main__":
    main_start_time = time.time()
    main()
    main_end_time = time.time()
    logger.info(f"Script finished. Total execution time: {main_end_time - main_start_time:.2f} seconds")
    log_memory_usage()