from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Website, Page, Violation, HTMLFix, ScheduledCheck
from app.services import WebsiteCrawler, AhpraComplianceAnalyzer, HTMLSemanticFixer
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__)

@api_bp.route('/website/<int:website_id>/status')
@login_required
def website_status(website_id):
    """Get the crawling status of a website"""
    website = Website.query.filter_by(id=website_id, user_id=current_user.id).first_or_404()
    
    return jsonify({
        'id': website.id,
        'status': website.crawl_status,
        'last_crawled': website.last_crawled.isoformat() if website.last_crawled else None,
        'page_count': website.pages.count(),
        'compliance_score': website.compliance_score,
        'is_compliant': website.is_compliant
    })

@api_bp.route('/page/<int:page_id>/status')
@login_required
def page_status(page_id):
    """Get the analysis status of a page"""
    page = Page.query.join(Website).filter(
        Page.id == page_id,
        Website.user_id == current_user.id
    ).first_or_404()
    
    return jsonify({
        'id': page.id,
        'analyzed': page.analyzed,
        'compliance_score': page.compliance_score,
        'is_compliant': page.is_compliant,
        'violation_count': page.violations.count(),
        'html_fix_available': bool(HTMLFix.query.filter_by(page_id=page.id).first()),
        'html_fix_paid': page.html_fix_paid
    })

@api_bp.route('/scheduled-checks/<int:website_id>', methods=['POST'])
@login_required
def schedule_check(website_id):
    """Schedule periodic checks for a website"""
    website = Website.query.filter_by(id=website_id, user_id=current_user.id).first_or_404()
    
    # Get frequency from request
    frequency = request.json.get('frequency')
    if frequency not in ['daily', 'weekly', 'monthly']:
        return jsonify({'error': 'Invalid frequency'}), 400
    
    # Calculate next check date
    now = datetime.utcnow()
    if frequency == 'daily':
        next_check = now + timedelta(days=1)
    elif frequency == 'weekly':
        next_check = now + timedelta(weeks=1)
    else:  # monthly
        next_check = now + timedelta(days=30)
    
    # Create or update scheduled check
    scheduled_check = ScheduledCheck.query.filter_by(
        website_id=website.id,
        user_id=current_user.id
    ).first()
    
    if scheduled_check:
        scheduled_check.frequency = frequency
        scheduled_check.next_check = next_check
        scheduled_check.active = True
    else:
        scheduled_check = ScheduledCheck(
            user_id=current_user.id,
            website_id=website.id,
            frequency=frequency,
            next_check=next_check,
            active=True
        )
        db.session.add(scheduled_check)
    
    db.session.commit()
    
    return jsonify({
        'id': scheduled_check.id,
        'frequency': scheduled_check.frequency,
        'next_check': scheduled_check.next_check.isoformat(),
        'active': scheduled_check.active
    })

@api_bp.route('/scheduled-checks/<int:check_id>/cancel', methods=['POST'])
@login_required
def cancel_check(check_id):
    """Cancel a scheduled check"""
    scheduled_check = ScheduledCheck.query.filter_by(
        id=check_id,
        user_id=current_user.id
    ).first_or_404()
    
    scheduled_check.active = False
    db.session.commit()
    
    return jsonify({'status': 'success'})

@api_bp.route('/html-fix/<int:page_id>/regenerate', methods=['POST'])
@login_required
def regenerate_html_fix(page_id):
    """Regenerate HTML fix for a page"""
    page = Page.query.join(Website).filter(
        Page.id == page_id,
        Website.user_id == current_user.id
    ).first_or_404()
    
    # Check if already paid for HTML fix
    if not page.html_fix_paid:
        return jsonify({'error': 'HTML fix not purchased for this page'}), 403
    
    # Start HTML fix generation
    fixer = HTMLSemanticFixer()
    try:
        result = fixer.generate_html_fix(page.id)
        return jsonify({
            'status': 'success',
            'html': result.get('fixed_html', ''),
            'justification': result.get('justification', '')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
