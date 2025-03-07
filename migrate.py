from app import app, db
from flask_migrate import Migrate, init, migrate, upgrade
import os

migrate_obj = Migrate(app, db)

def run_migrations():
    with app.app_context():
        # Initialize migrations if the folder does not exist
        if not os.path.exists("migrations"):
            try:
                init()
                print("Initialized migrations folder.")
            except Exception as e:
                print("Migrations folder already exists or error:", e)
        # Generate migration script
        migrate(message="Add profile_pic_url to Admin and User models")
        # Apply the migration (upgrade the database schema)
        upgrade()
        print("Migration complete.")

if __name__ == '__main__':
    run_migrations()