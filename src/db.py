from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import os

import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)

Base = declarative_base()

class NFTMetadata(Base):
    __tablename__ = 'nft_metadata'

    id = Column(Integer, primary_key=True, autoincrement=True)
    network_name = Column(String, nullable=False)
    contract_address = Column(String, nullable=False)
    collection_name = Column(String, nullable=False)
    token_id = Column(Integer, nullable=False)
    token_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    mint_date = Column(DateTime, nullable=True)
    ai_image_description = Column(Text, nullable=True)

class DatabaseManager:
    def __init__(self, db_uri: str):
        self.db_uri = db_uri
        self.engine = create_engine(self.db_uri)
        self.Session = sessionmaker(bind=self.engine)
        
        self._create_database()
        db_path = self._get_db_file_path()
        if db_path and not os.path.exists(db_path):
            print(f'A new database has been created: {db_path}')

    def _get_db_file_path(self):
        if self.db_uri.startswith('sqlite:///'):
            return self.db_uri.replace('sqlite:///', '')
        return None

    def _create_database(self):
        try:
            Base.metadata.create_all(self.engine)
        except OperationalError as e:
            raise RuntimeError(f'Error during database creation: {e}')

    def get_session(self):
        return self.Session()
