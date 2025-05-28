from datetime import datetime
from app import db

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # Amount in GBP
    credits = db.Column(db.Float, nullable=False)  # Credit amount added/deducted
    description = db.Column(db.String(255))
    stripe_payment_id = db.Column(db.String(255))  # Stripe payment ID for reference
    type = db.Column(db.String(20))  # 'credit_purchase', 'page_analysis', 'html_fix'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'failed', 'refunded'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CreditPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    credits = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price in GBP
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<CreditPackage {self.name}: {self.credits} credits for £{self.price}>'
