from datetime import datetime
from app import db

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120))
    last_crawled = db.Column(db.DateTime)
    crawl_status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    pages = db.relationship('Page', backref='website', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def compliance_score(self):
        """Calculate overall website compliance score"""
        pages = self.pages.all()
        if not pages:
            return 0
        
        total_score = sum(page.compliance_score for page in pages)
        return round(total_score / len(pages), 2)
    
    @property
    def is_compliant(self):
        """Check if website is fully compliant"""
        return self.compliance_score >= 95  # Consider 95% or higher as compliant


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'), nullable=False)
    url = db.Column(db.String(512), nullable=False)
    title = db.Column(db.String(255))
    html_content = db.Column(db.Text)
    text_content = db.Column(db.Text)
    analyzed = db.Column(db.Boolean, default=False)
    compliance_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Payment tracking
    analysis_paid = db.Column(db.Boolean, default=False)  # True if paid or part of free allocation
    html_fix_paid = db.Column(db.Boolean, default=False)  # True if HTML fix has been purchased
    
    # Relationships
    violations = db.relationship('Violation', backref='page', lazy='dynamic', cascade='all, delete-orphan')
    html_fixes = db.relationship('HTMLFix', backref='page', uselist=False, cascade='all, delete-orphan')
    
    @property
    def is_compliant(self):
        """Check if page is compliant"""
        return self.compliance_score >= 95


class Violation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)
    text_content = db.Column(db.Text, nullable=False)  # The non-compliant text
    guideline_reference = db.Column(db.String(20))  # e.g., "Section 8.3f"
    justification = db.Column(db.Text)  # Explanation of why this violates guidelines
    suggested_revision = db.Column(db.Text)  # Compliant version of the text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class HTMLFix(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False, unique=True)
    original_html = db.Column(db.Text)  # Original HTML structure
    fixed_html = db.Column(db.Text)  # Improved semantic HTML
    justification = db.Column(db.Text)  # Explanation of the changes made
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScheduledCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'), nullable=False)
    frequency = db.Column(db.String(20))  # daily, weekly, monthly
    next_check = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to website
    website = db.relationship('Website', backref='scheduled_checks')
