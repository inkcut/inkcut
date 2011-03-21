"""SQLAlchemy Metadata and Session object"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLAlchemy session manager. Updated by model.init_model()
Session = sessionmaker()

# The declarative Base
Base = declarative_base()
