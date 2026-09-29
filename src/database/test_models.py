from src.database.base import Base
from src.database import models


print("Registered tables:")

for table in Base.metadata.tables.values():
    print(f"- {table.name}")