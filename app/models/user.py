from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(120))
    credit_balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    websites = db.relationship('Website', backref='owner', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')
    scheduled_checks = db.relationship('ScheduledCheck', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def add_credits(self, amount):
        self.credit_balance += amount
        db.session.commit()
    
    def deduct_credits(self, amount):
        if self.credit_balance >= amount:
            self.credit_balance -= amount
            db.session.commit()
            return True
        return False

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
