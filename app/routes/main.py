from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('main/index.html', title='Ahpra Compliance Audit Platform')

@main_bp.route('/about')
def about():
    return render_template('main/about.html', title='About')

@main_bp.route('/pricing')
def pricing():
    from app.models import CreditPackage
    packages = CreditPackage.query.filter_by(is_active=True).all()
    return render_template('main/pricing.html', title='Pricing', packages=packages)

@main_bp.route('/features')
def features():
    return render_template('main/features.html', title='Features')

@main_bp.route('/contact')
def contact():
    return render_template('main/contact.html', title='Contact Us')

@main_bp.route('/faq')
def faq():
    return render_template('main/faq.html', title='Frequently Asked Questions')
