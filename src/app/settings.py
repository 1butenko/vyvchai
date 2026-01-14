from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

Base = declarative_base()
# Ensure DATABASE_URL is present and has type `str` for mypy
_database_url = os.getenv("DATABASE_URL")
if _database_url is None:
    raise RuntimeError("DATABASE_URL environment variable is not set")

engine = create_engine(_database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()
