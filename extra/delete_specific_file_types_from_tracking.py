import os
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from models import FileTracking
from dotenv import load_dotenv

# Setup logging and load environment variables
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# Database connection configuration
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
CONNECTION_STRING = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
ENGINE = create_engine(CONNECTION_STRING)
Session = sessionmaker(bind=ENGINE)


def delete_files_by_names(substrings):
    """
    Deletes rows from the FileTracking table where the file_name includes any of the specified substrings.

    Args:
    substrings (list of str): List of substrings to check in the file_name column.
    """
    session = Session()
    try:
        # Constructing the query with dynamic LIKE conditions
        query = session.query(FileTracking)
        like_conditions = [FileTracking.file_name.ilike(f'%{substring}%') for substring in substrings]
        query = query.filter(or_(*like_conditions))
        deleted_count = query.delete(synchronize_session=False)
        session.commit()
        logging.info(f"Deleted {deleted_count} rows from FileTracking.")
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to delete rows: {str(e)}")
    finally:
        session.close()


def main():
    # List of substrings to search for in the file names
    substrings_to_search = ["reactions", "links"]
    delete_files_by_names(substrings_to_search)


if __name__ == "__main__":
    main()
