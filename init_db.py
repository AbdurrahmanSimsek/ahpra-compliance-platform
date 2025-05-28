import os
import dotenv
from app import create_app, db
from app.models import CreditPackage

# Load environment variables
dotenv.load_dotenv()

# Create app context
app = create_app()

def init_db():
    """Initialize the database with default data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Add default credit packages if they don't exist
        if CreditPackage.query.count() == 0:
            packages = [
                CreditPackage(name="Basic", credits=50, price=45, is_active=True),
                CreditPackage(name="Standard", credits=100, price=80, is_active=True),
                CreditPackage(name="Premium", credits=250, price=180, is_active=True),
            ]
            db.session.add_all(packages)
            db.session.commit()
            print("Added default credit packages")
        
        print("Database initialization complete!")

if __name__ == "__main__":
    init_db()
