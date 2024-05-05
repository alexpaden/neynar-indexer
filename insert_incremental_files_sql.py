import os
import pyarrow.parquet as pq
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from models import Base, Reactions, Fids, Storage, Casts, UserData, Fnames, Signers, Verifications, FileTracking, Links
import logging
from dotenv import load_dotenv
from filelock import FileLock, Timeout

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


skip_tables = {'links', 'reactions'}

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

def process_file(file_path):
    table_class_map = {
        'fids': Fids,
        'storage': Storage,
        'casts': Casts,
        'user_data': UserData,
        'fnames': Fnames,
        'signers': Signers,
        'verifications': Verifications
    }
    file_name = os.path.basename(file_path)
    lock_path = f'/tmp/{file_name}.lock'
    lock = FileLock(lock_path)

    try:
        with lock.acquire(timeout=0):  # Non-blocking attempt
            if file_already_processed(file_name):
                #logging.info(f"Skipping already processed file {file_name}")
                return

            table_name = file_name.split('-')[1].split('.')[0]
            orm_class = table_class_map.get(table_name)
            if not orm_class:
                #logging.info(f"No ORM class found for table '{table_name}' from file '{file_name}'")
                return

            primary_key = [key.name for key in orm_class.__table__.primary_key.columns][0]

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

                    insert_statement = insert(orm_class.__table__).on_conflict_do_update(
                        index_elements=[primary_key],
                        set_={key: value for key, value in row_data.items() if key != primary_key}
                    )
                    session.execute(insert_statement, filtered_data)
                    session.commit()
                    total_rows += len(filtered_data)

                logging.info(f"File {file_name} processed: {total_rows} rows inserted/updated")
                record_file_as_processed(file_name)
            session.close()
    except Timeout:
        logging.info(f"Skipping locked file {file_name}")

def main():
    path = './downloads/incremental'
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        process_file(file_path)

if __name__ == "__main__":
    main()
    logging.info("script finished")
