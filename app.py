import os
from app import create_app, db
from app.models import User, Website, Page, Violation, HTMLFix, Transaction, CreditPackage, ScheduledCheck

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Website': Website,
        'Page': Page,
        'Violation': Violation,
        'HTMLFix': HTMLFix,
        'Transaction': Transaction,
        'CreditPackage': CreditPackage,
        'ScheduledCheck': ScheduledCheck
    }

# Initialize the database if it doesn't exist
@app.before_first_request
def initialize_database():
    if not os.path.exists('app.db'):
        with app.app_context():
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

if __name__ == '__main__':
    # Get port from environment variable for Replit compatibility
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
