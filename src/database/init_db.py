from src.database.connection import create_tables, engine
from src.database.base import Base
from src.database import models


if __name__ == "__main__":
    Base.metadata.drop_all(bind=engine)
    create_tables()

    print("Database tables dropped and recreated successfully.")