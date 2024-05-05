import os
import pyarrow.parquet as pq
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from models import Base, Fids, Storage, Links, Casts, UserData, Reactions, Fnames, Signers, Verifications, FileTracking
import logging
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
CONNECTION_STRING = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
ENGINE = create_engine(CONNECTION_STRING)
Session = sessionmaker(bind=ENGINE)

skip_tables = {'links', 'reactions'}  # Set of table names to skip

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

def table_is_empty(table_name):
    # Query to check if at least one row exists
    query = text(f"SELECT EXISTS (SELECT 1 FROM {table_name} LIMIT 1)")
    with ENGINE.connect() as conn:
        result = conn.execute(query)
        # Return True if no rows exist
        return not result.scalar()

def process_file(file_path):
    table_class_map = {
        'fids': Fids,
        'storage': Storage,
       # 'links': Links,
        'casts': Casts,
        'user_data': UserData,
       # 'reactions': Reactions,
        'fnames': Fnames,
        'signers': Signers,
        'verifications': Verifications
    }
    table_name = file_path.split('-')[1].split('.')[0]  # Added split('.') to handle file extension if present
    orm_class = table_class_map.get(table_name)
    if not orm_class or not table_is_empty(table_name):  # Check if table is empty
        logging.info(f"No action taken for table '{table_name}' from file '{file_path}'")
        return

    with pq.ParquetFile(file_path) as pf:
        iterator = pf.iter_batches(batch_size=4000000)  # Adjust batch size based on your memory constraints
        session = Session()
        try:
            for batch in iterator:
                data = batch.to_pydict()
                table_columns = {column.name for column in orm_class.__table__.columns}
                filtered_data = [{key: value[i] for key, value in data.items() if key in table_columns} for i in
                                 range(len(batch))]

                insert_statement = insert(orm_class.__table__).on_conflict_do_nothing()
                session.execute(insert_statement, filtered_data)
                session.commit()
                logging.info(f"Inserted data into {orm_class.__tablename__}: {len(filtered_data)} rows")
        except Exception as e:
            session.rollback()
            logging.error(f"Error processing {file_path}: {str(e)}")
        finally:
            session.close()

def main():
    run_sql_script('../sql/setup.sql')
    path = '../downloads/full'

    for file in os.listdir(path):
        table_name = file.split('-')[1]
        if table_name in skip_tables:
            logging.info(f"Skipping file {file} associated with table {table_name}")
            continue
        file_path = os.path.join(path, file)
        process_file(file_path)

if __name__ == "__main__":
    main()
    #logging.info("script finished")
