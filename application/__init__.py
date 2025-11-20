from flask import Flask, redirect, url_for
from flask_mongoengine import MongoEngine
from flask_login import LoginManager
import os

# Initialize Flask extensions
db = MongoEngine()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    # MongoDB Settings
    app.config['MONGODB_SETTINGS'] = {
        'host': os.environ.get('MONGO_URI', 'mongodb://localhost:27017/school_fee_db'),
        'tls': True,
        'tlsAllowInvalidCertificates': True
    }

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # Add user_loader for Flask-Login
    from application.models import Admin
    @login_manager.user_loader
    def load_user(user_id):
        return Admin.objects(pk=user_id).first()

    with app.app_context():
        # Import parts of our application
        from application.models import Admin, Student, Fee, PaymentHistory, AuditLog
        from application.routes import auth, student, fee, admin

        # Register blueprints
        app.register_blueprint(auth.bp)
        app.register_blueprint(student.bp)
        app.register_blueprint(fee.bp)
        app.register_blueprint(admin.bp)

        # Create default admin if none exists
        if not Admin.objects.first():
            default_admin = Admin(
                username='admin',
                email='admin@school.com'
            )
            default_admin.set_password('admin123')
            default_admin.save()

    return app

# Expose app for WSGI servers
app = create_app()