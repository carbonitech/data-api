from dotenv import load_dotenv

load_dotenv()
from os import getenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_url = getenv("DATABASE_URL").replace("postgres://", "postgresql://")
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(e)
    finally:
        db.close()
