from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Website, Page, Violation, HTMLFix, Transaction
from app.forms.website import WebsiteForm
from app.services import WebsiteCrawler, AhpraComplianceAnalyzer, HTMLSemanticFixer, ReportGenerator, PaymentService
import os
from celery import shared_task

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # Get user's websites
    websites = Website.query.filter_by(user_id=current_user.id).all()
    
    # Get recent transactions
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.created_at.desc()).limit(5).all()
    
    return render_template('dashboard/index.html', 
                           title='Dashboard', 
                           websites=websites,
                           transactions=recent_transactions)

@dashboard_bp.route('/website/add', methods=['GET', 'POST'])
@login_required
def add_website():
    form = WebsiteForm()
    if form.validate_on_submit():
        website = Website(
            user_id=current_user.id,
            url=form.url.data,
            name=form.name.data
        )
        db.session.add(website)
        db.session.commit()
        
        flash('Website added successfully! We will start crawling it shortly.', 'success')
        
        # Start the crawling process in the background
        crawl_website.delay(website.id)
        
        return redirect(url_for('dashboard.website_detail', website_id=website.id))
    
    return render_template('dashboard/add_website.html', title='Add Website', form=form)

@dashboard_bp.route('/website/<int:website_id>')
@login_required
def website_detail(website_id):
    website = Website.query.filter_by(id=website_id, user_id=current_user.id).first_or_404()
    pages = website.pages.order_by(Page.url).all()
    
    return render_template('dashboard/website_detail.html', 
                           title=f'Website: {website.name}',
                           website=website,
                           pages=pages)

@dashboard_bp.route('/page/<int:page_id>')
@login_required
def page_detail(page_id):
    page = Page.query.join(Website).filter(
        Page.id == page_id,
        Website.user_id == current_user.id
    ).first_or_404()
    
    violations = page.violations.all()
    html_fix = HTMLFix.query.filter_by(page_id=page.id).first()
    
    return render_template('dashboard/page_detail.html',
                           title=f'Page: {page.title or page.url}',
                           page=page,
                           violations=violations,
                           html_fix=html_fix)

@dashboard_bp.route('/page/<int:page_id>/analyze', methods=['POST'])
@login_required
def analyze_page(page_id):
    page = Page.query.join(Website).filter(
        Page.id == page_id,
        Website.user_id == current_user.id
    ).first_or_404()
    
    if page.analyzed:
        flash('This page has already been analyzed.', 'info')
        return redirect(url_for('dashboard.page_detail', page_id=page.id))
    
    # Check if payment is required
    payment_service = PaymentService()
    
    # Count how many pages user has already analyzed
    analyzed_pages = Page.query.join(Website).filter(
        Website.user_id == current_user.id,
        Page.analyzed == True,
        Page.analysis_paid == True
    ).count()
    
    if analyzed_pages >= current_app.config['FREE_PAGE_LIMIT']:
        # Payment required
        success, message = payment_service.charge_for_page_analysis(current_user.id, 1)
        if not success:
            flash(message, 'danger')
            return redirect(url_for('dashboard.page_detail', page_id=page.id))
        
        page.analysis_paid = True
        db.session.commit()
    else:
        # Free analysis
        page.analysis_paid = True
        db.session.commit()
        
        # Create a free transaction record
        transaction = Transaction(
            user_id=current_user.id,
            amount=0,
            credits=0,
            description=f"Free page analysis (page ID: {page.id})",
            type='page_analysis',
            status='completed'
        )
        db.session.add(transaction)
        db.session.commit()
    
    # Start analysis in background
    analyze_page_task.delay(page.id)
    
    flash('Page analysis has started. You will be notified when it completes.', 'info')
    return redirect(url_for('dashboard.page_detail', page_id=page.id))

@dashboard_bp.route('/page/<int:page_id>/fix-html', methods=['POST'])
@login_required
def fix_html(page_id):
    page = Page.query.join(Website).filter(
        Page.id == page_id,
        Website.user_id == current_user.id
    ).first_or_404()
    
    # Check if already paid for
    if not page.html_fix_paid:
        # Charge for HTML fix
        payment_service = PaymentService()
        success, message = payment_service.charge_for_html_fix(current_user.id, page.id)
        
        if not success:
            flash(message, 'danger')
            return redirect(url_for('dashboard.page_detail', page_id=page.id))
        
        # Mark as paid
        page.html_fix_paid = True
        db.session.commit()
    
    # Generate HTML fix in background
    generate_html_fix_task.delay(page.id)
    
    flash('HTML fix generation has started. You will be notified when it completes.', 'info')
    return redirect(url_for('dashboard.page_detail', page_id=page.id))

@dashboard_bp.route('/website/<int:website_id>/report')
@login_required
def generate_report(website_id):
    website = Website.query.filter_by(id=website_id, user_id=current_user.id).first_or_404()
    
    # Check if the website has analyzed pages
    if website.pages.filter(Page.analyzed == True).count() == 0:
        flash('No analyzed pages found. Please analyze pages before generating a report.', 'warning')
        return redirect(url_for('dashboard.website_detail', website_id=website.id))
    
    # Generate report
    report_generator = ReportGenerator(website.id)
    
    try:
        # First try to generate a PDF report
        report_path = report_generator.generate_pdf()
        file_extension = os.path.splitext(report_path)[1].lower()
        
        # Determine if it's a PDF or HTML based on file extension
        if file_extension == '.pdf':
            mime_type = 'application/pdf'
            download_name = f"{website.name.replace(' ', '_')}_compliance_report.pdf"
        else:
            mime_type = 'text/html'
            download_name = f"{website.name.replace(' ', '_')}_compliance_report.html"
        
        # Serve the file
        from flask import send_file
        return send_file(
            report_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=download_name
        )
        
    except Exception as e:
        # Fallback: render HTML report directly
        flash(f'PDF generation is not available. Showing HTML report instead. Error: {str(e)}', 'warning')
        return render_template('reports/report_preview.html', 
                               website=website,
                               report_html=report_generator.generate_html_report())

# Celery background tasks
@shared_task
def crawl_website(website_id):
    """Background task to crawl a website"""
    crawler = WebsiteCrawler(website_id)
    crawler.crawl()

@shared_task
def analyze_page_task(page_id):
    """Background task to analyze a page"""
    analyzer = AhpraComplianceAnalyzer()
    analyzer.analyze_page(page_id)

@shared_task
def generate_html_fix_task(page_id):
    """Background task to generate HTML fix"""
    fixer = HTMLSemanticFixer()
    fixer.generate_html_fix(page_id)
