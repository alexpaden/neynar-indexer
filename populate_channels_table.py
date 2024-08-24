import os
import requests
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, Channel

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database connection configuration
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
CONNECTION_STRING = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
ENGINE = create_engine(CONNECTION_STRING)
Session = sessionmaker(bind=ENGINE)

# API configuration
API_KEY = os.getenv('NEYNAR_API_KEY')
API_URL = 'https://api.neynar.com/v2/farcaster/channel/list'
LIMIT = 200

def fetch_channels(cursor=None):
    headers = {
        'accept': 'application/json',
        'api_key': API_KEY
    }
    params = {
        'limit': LIMIT
    }
    if cursor:
        params['cursor'] = cursor

    response = requests.get(API_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def upsert_channels(channels):
    session = Session()
    for channel in channels:
        stmt = text("""
            INSERT INTO channels (id, name, description, image_url, url)
            VALUES (:id, :name, :description, :image_url, :url)
            ON CONFLICT (id) DO UPDATE
            SET name = :name,
                description = :description,
                image_url = :image_url,
                url = :url
        """)
        session.execute(stmt, {
            'id': channel['id'],
            'name': channel['name'],
            'description': channel['description'],
            'image_url': channel['image_url'],
            'url': channel['url']
        })
    session.commit()
    session.close()

def main():
    cursor = None
    total_channels = 0
    while True:
        data = fetch_channels(cursor)
        channels = data.get('channels', [])
        if not channels:
            break
        upsert_channels(channels)
        total_channels += len(channels)
        logging.info(f"Processed {len(channels)} channels. Total: {total_channels}")
        cursor = data.get('next', {}).get('cursor')
        if not cursor:
            break
    logging.info(f"Finished processing. Total channels: {total_channels}")

if __name__ == "__main__":
    main()