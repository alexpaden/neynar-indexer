from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Fids, Storage, Links, Casts, UserData, Reactions, Fnames, Signers, Verifications
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
CONNECTION_STRING = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
ENGINE = create_engine(CONNECTION_STRING)
Session = sessionmaker(bind=ENGINE)

def get_row_count(table_class):
    """ Get the row count for a given SQLAlchemy table class """
    session = Session()
    row_count = session.query(table_class).count()
    session.close()
    return row_count

def main():
    # List of all table classes
    table_classes = [Fids, Storage, Links, Casts, UserData, Reactions, Fnames, Signers, Verifications]

    # Iterate over each table class and print row counts
    for table_class in table_classes:
        row_count = get_row_count(table_class)
        logging.info(f"{table_class.__tablename__}: {row_count} rows")

if __name__ == "__main__":
    main()
