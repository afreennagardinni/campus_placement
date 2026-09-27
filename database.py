from app import app
from models import db

def init_db():
    with app.app_context():
        db.create_all()           # ← 4 spaces ka indent
        print("Database initialized successfully!")
        print("Check instance folder for placements.db")

if __name__ == "__main__":
    init_db()