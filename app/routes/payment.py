from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Transaction, CreditPackage
from app.services import PaymentService
import stripe

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/credits')
@login_required
def credits():
    # Get available credit packages
    packages = CreditPackage.query.filter_by(is_active=True).all()
    
    # Get user's transaction history
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.created_at.desc()).all()
    
    return render_template('payment/credits.html', 
                           title='Manage Credits',
                           packages=packages,
                           transactions=transactions)

@payment_bp.route('/purchase/<int:package_id>', methods=['POST'])
@login_required
def purchase_credits(package_id):
    package = CreditPackage.query.get_or_404(package_id)
    
    payment_service = PaymentService()
    try:
        checkout_session = payment_service.create_checkout_session(
            user_id=current_user.id,
            package_id=package.id
        )
        
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 403

@payment_bp.route('/success')
@login_required
def payment_success():
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Invalid payment session', 'danger')
        return redirect(url_for('payment.credits'))
    
    # Verify payment was successful
    transaction = Transaction.query.filter_by(
        user_id=current_user.id,
        stripe_payment_id=session_id
    ).first()
    
    if not transaction:
        flash('Transaction not found', 'danger')
        return redirect(url_for('payment.credits'))
    
    flash(f'Payment successful! {transaction.credits} credits have been added to your account.', 'success')
    return redirect(url_for('payment.credits'))

@payment_bp.route('/cancel')
@login_required
def payment_cancel():
    flash('Payment was cancelled.', 'info')
    return redirect(url_for('payment.credits'))

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    payment_service = PaymentService()
    
    try:
        payment_service.process_checkout_webhook(payload, sig_header)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
