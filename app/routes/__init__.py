# Import all route blueprints to make them available when importing from the routes package
from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.payment import payment_bp
from app.routes.api import api_bp
