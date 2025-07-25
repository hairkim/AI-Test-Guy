from app.database import engine
from app.models import Base

# Run this once to create tables
def init_db():
    Base.metadata.create_all(bind=engine)

init_db()
