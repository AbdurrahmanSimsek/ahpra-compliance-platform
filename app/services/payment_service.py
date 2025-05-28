import stripe
from flask import current_app
from app import db
from app.models import User, Transaction, CreditPackage

class PaymentService:
    def __init__(self):
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        self.page_analysis_cost = current_app.config['PAGE_ANALYSIS_COST']
        self.html_fix_cost = current_app.config['HTML_FIX_COST']
        self.free_page_limit = current_app.config['FREE_PAGE_LIMIT']
    
    def create_checkout_session(self, user_id, package_id):
        """Create a Stripe checkout session for credit purchase"""
        user = User.query.get(user_id)
        package = CreditPackage.query.get(package_id)
        
        if not user or not package:
            raise ValueError("Invalid user or package")
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': f'{package.name} - {package.credits} Credits',
                    },
                    'unit_amount': int(package.price * 100),  # Amount in pence
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=current_app.config['BASE_URL'] + '/payment/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=current_app.config['BASE_URL'] + '/payment/cancel',
            client_reference_id=str(user.id),
            metadata={
                'package_id': package.id,
                'credits': package.credits
            }
        )
        
        # Create pending transaction
        transaction = Transaction(
            user_id=user.id,
            amount=package.price,
            credits=package.credits,
            description=f"Purchase of {package.name} ({package.credits} credits)",
            stripe_payment_id=checkout_session.id,
            type='credit_purchase',
            status='pending'
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return checkout_session
    
    def process_checkout_webhook(self, payload, sig_header):
        """Process webhook events from Stripe"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET']
            )
        except ValueError as e:
            # Invalid payload
            raise e
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise e
        
        # Handle the checkout.session.completed event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Find the corresponding transaction
            transaction = Transaction.query.filter_by(stripe_payment_id=session.id).first()
            if transaction and transaction.status == 'pending':
                # Update transaction status
                transaction.status = 'completed'
                
                # Add credits to user
                user = User.query.get(transaction.user_id)
                if user:
                    user.add_credits(transaction.credits)
                
                db.session.commit()
        
        return {'status': 'success'}
    
    def charge_for_page_analysis(self, user_id, num_pages):
        """Charge user for page analysis"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Calculate free pages remaining
        used_free_pages = Transaction.query.filter_by(
            user_id=user.id, 
            type='page_analysis', 
            amount=0
        ).count()
        
        free_pages_remaining = max(0, self.free_page_limit - used_free_pages)
        free_pages_to_use = min(free_pages_remaining, num_pages)
        paid_pages = max(0, num_pages - free_pages_to_use)
        
        # Calculate cost
        total_cost = paid_pages * self.page_analysis_cost
        
        # Check if user has enough credits
        if user.credit_balance < total_cost:
            return False, f"Insufficient credits. You need £{total_cost} for {paid_pages} pages."
        
        # Create transactions for free pages
        if free_pages_to_use > 0:
            free_transaction = Transaction(
                user_id=user.id,
                amount=0,
                credits=0,
                description=f"Free page analysis ({free_pages_to_use} pages)",
                type='page_analysis',
                status='completed'
            )
            db.session.add(free_transaction)
        
        # Create transaction for paid pages
        if paid_pages > 0:
            # Deduct credits
            if not user.deduct_credits(total_cost):
                return False, "Credit deduction failed"
            
            # Create transaction record
            paid_transaction = Transaction(
                user_id=user.id,
                amount=total_cost,
                credits=-total_cost,  # Negative to indicate usage
                description=f"Page analysis charge ({paid_pages} pages at £{self.page_analysis_cost} each)",
                type='page_analysis',
                status='completed'
            )
            db.session.add(paid_transaction)
        
        db.session.commit()
        return True, f"Successfully charged for {num_pages} pages (£{total_cost})"
    
    def charge_for_html_fix(self, user_id, page_id):
        """Charge user for HTML fix"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Check if user has enough credits
        if user.credit_balance < self.html_fix_cost:
            return False, f"Insufficient credits. You need £{self.html_fix_cost} for HTML fix."
        
        # Deduct credits
        if not user.deduct_credits(self.html_fix_cost):
            return False, "Credit deduction failed"
        
        # Create transaction record
        transaction = Transaction(
            user_id=user.id,
            amount=self.html_fix_cost,
            credits=-self.html_fix_cost,  # Negative to indicate usage
            description=f"HTML fix for page ID {page_id}",
            type='html_fix',
            status='completed'
        )
        db.session.add(transaction)
        
        db.session.commit()
        return True, f"Successfully charged £{self.html_fix_cost} for HTML fix"
