# Import all services to make them available when importing from the services package
from app.services.crawler import WebsiteCrawler
from app.services.analyzer import AhpraComplianceAnalyzer
from app.services.html_fixer import HTMLSemanticFixer
from app.services.report_generator import ReportGenerator
from app.services.payment_service import PaymentService
