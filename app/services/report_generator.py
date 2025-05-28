from flask import render_template, current_app
import tempfile
import os
from app.models import Website, Page, Violation, HTMLFix

# Try to import WeasyPrint, but provide a fallback if it's not available
WEASYPRINT_AVAILABLE = False
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    # WeasyPrint not available, we'll use an alternative approach
    pass

class ReportGenerator:
    def __init__(self, website_id):
        self.website = Website.query.get(website_id)
        if not self.website:
            raise ValueError(f"Website with ID {website_id} not found")
        
        self.pages = self.website.pages.filter(Page.analyzed == True).all()
    
    def generate_pdf(self):
        """Generate a PDF report for the website"""
        # Prepare data for the report template
        data = {
            'website': self.website,
            'pages': self.pages,
            'overview': self._generate_overview(),
            'date': self._get_formatted_date()
        }
        
        # Render the HTML template
        html_content = render_template('reports/website_report.html', **data)
        
        if WEASYPRINT_AVAILABLE:
            # Create temporary file for the PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                # Configure fonts
                font_config = FontConfiguration()
                
                # Convert HTML to PDF
                HTML(string=html_content).write_pdf(
                    temp_file.name,
                    stylesheets=[
                        CSS(string='@page { size: A4; margin: 1cm }'),
                        CSS(filename=os.path.join(current_app.static_folder, 'css/report.css'))
                    ],
                    font_config=font_config
                )
                
                temp_file_path = temp_file.name
            
            return temp_file_path
        else:
            # Fallback: Save as HTML if WeasyPrint is not available
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as temp_file:
                temp_file.write(html_content)
                temp_file_path = temp_file.name
            
            return temp_file_path
    
    def generate_html_report(self):
        """Generate an HTML report for the website (alternative to PDF)"""
        # Prepare data for the report template
        data = {
            'website': self.website,
            'pages': self.pages,
            'overview': self._generate_overview(),
            'date': self._get_formatted_date()
        }
        
        # Render the HTML template
        return render_template('reports/website_report.html', **data)
    
    def _generate_overview(self):
        """Generate overview statistics for the report"""
        total_pages = len(self.pages)
        compliant_pages = sum(1 for page in self.pages if page.is_compliant)
        total_violations = sum(page.violations.count() for page in self.pages)
        html_fixes_purchased = sum(1 for page in self.pages if page.html_fix_paid)
        
        return {
            'total_pages': total_pages,
            'compliant_pages': compliant_pages,
            'compliance_percentage': round((compliant_pages / total_pages) * 100, 2) if total_pages > 0 else 0,
            'total_violations': total_violations,
            'average_violations_per_page': round(total_violations / total_pages, 2) if total_pages > 0 else 0,
            'html_fixes_purchased': html_fixes_purchased
        }
    
    def _get_formatted_date(self):
        """Return a formatted date for the report"""
        from datetime import datetime
        return datetime.utcnow().strftime("%d %B %Y")
