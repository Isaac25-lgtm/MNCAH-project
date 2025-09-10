"""
Flask Application Factory
This module creates and configures the Flask application with all necessary extensions
and blueprints for the MOH MNCAH Dashboard System.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import Table

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name='development'):
    """
    Create and configure Flask application
    
    Args:
        config_name: Configuration environment (development, production, testing)
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    from config.config import config
    config_class = config.get(config_name, config['default'])
    app.config.from_object(config_class)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Configure CORS for API endpoints
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/upload/*": {"origins": "*"}
    })
    
    # Configure Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Configure proxy headers if behind reverse proxy
    if app.config.get('BEHIND_PROXY'):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        return db.session.get(User, int(user_id))
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Configure logging
    configure_logging(app)
    
    # Create database tables
    with app.app_context():
        create_database_tables()
        create_default_users()
    
    # Register CLI commands
    register_cli_commands(app)
    
    return app


def register_blueprints(app):
    """Register application blueprints"""
    from .views.auth import auth_bp
    from .views.dashboard import dashboard_bp
    from .views.upload import upload_bp
    from .views.analysis import analysis_bp
    from .views.reports import reports_bp
    from .views.api import api_bp
    
    # Register blueprints with URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(upload_bp, url_prefix='/upload')
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Main route
    @app.route('/')
    def index():
        """Redirect to dashboard or login"""
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))


def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.errorhandler(400)
    def bad_request(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Bad request', 'message': str(error)}), 400
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
        return render_template('errors/401.html'), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def payload_too_large(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'File too large', 'message': 'Maximum file size is 15MB'}), 413
        return render_template('errors/413.html'), 413


def configure_logging(app):
    """Configure application logging"""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Configure file logging
        file_handler = RotatingFileHandler(
            'logs/moh_dashboard.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('MOH MNCAH Dashboard startup')


def create_database_tables():
    """Create database tables if they don't exist"""
    try:
        # Import all models to ensure they're registered
        from .models.user import User
        from .models.upload import DataUpload
        # Import Base metadata objects from models that use declarative_base
        from .models.user import Base as UserBase
        from .models.upload import Base as UploadBase

        # Attach query_property so Model.query works on these Bases
        # Attach query_property so Model.query works on these Bases across the app
        try:
            UserBase.query = db.session.query_property()
            UploadBase.query = db.session.query_property()
        except Exception:
            pass

        # Create tables defined on Flask-SQLAlchemy models (if any)
        db.create_all()

        # Also create tables defined on standalone SQLAlchemy Base models
        # Bind to the same engine used by Flask-SQLAlchemy
        engine = db.engine
        UserBase.metadata.create_all(bind=engine)
        # Reflect users table into UploadBase metadata so FK can resolve
        try:
            Table('users', UploadBase.metadata, autoload_with=engine)
        except Exception:
            pass
        UploadBase.metadata.create_all(bind=engine)
        
        logging.info("Database tables created successfully")
        
    except Exception as e:
        logging.error(f"Error creating database tables: {str(e)}")
        raise


def create_default_users():
    """Create default users if they don't exist"""
    try:
        from .models.user import User, UserManager, UserType
        
        # Check if users already exist
        if db.session.query(User).count() == 0:
            # Create default users
            default_users = User.create_default_users()
            
            for user in default_users:
                db.session.add(user)
            
            db.session.commit()
            logging.info("Default users created successfully")
        else:
            logging.info("Users already exist, skipping default user creation")
            
    except Exception as e:
        logging.error(f"Error creating default users: {str(e)}")
        db.session.rollback()


def register_cli_commands(app):
    """Register CLI commands for database management"""
    
    @app.cli.command()
    def init_db():
        """Initialize the database with tables and default data."""
        create_database_tables()
        create_default_users()
        print("Database initialized successfully!")
    
    @app.cli.command()
    def reset_db():
        """Reset the database (WARNING: This will delete all data)."""
        from flask import current_app
        if not current_app.config['DEBUG']:
            print("This command can only be run in debug mode!")
            return
        
        db.drop_all()
        db.create_all()
        create_default_users()
        print("Database reset successfully!")
    
    @app.cli.command()
    def create_admin():
        """Create a new admin user."""
        from .models.user import User, UserType
        import getpass
        
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
        full_name = input("Enter full name: ")
        email = input("Enter email (optional): ") or None
        
        try:
            user = User(
                username=username,
                password=password,
                user_type=UserType.ADMIN,
                full_name=full_name,
                email=email,
                organization="Ministry of Health Uganda",
                position="System Administrator"
            )
            
            db.session.add(user)
            db.session.commit()
            print(f"Admin user '{username}' created successfully!")
            
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            db.session.rollback()
    
    @app.cli.command()
    def list_users():
        """List all users in the system."""
        from .models.user import User
        
        users = db.session.query(User).all()
        print(f"\nFound {len(users)} users:")
        print("-" * 80)
        print(f"{'ID':<5} {'Username':<15} {'Type':<12} {'Full Name':<25} {'Status':<10}")
        print("-" * 80)
        
        for user in users:
            print(f"{user.id:<5} {user.username:<15} {user.user_type.value:<12} "
                  f"{user.full_name or 'N/A':<25} {user.status.value:<10}")
    
    @app.cli.command()
    def process_pending_uploads():
        """Process any pending data uploads."""
        from .models.upload import DataUpload, UploadStatus
        
        pending_uploads = db.session.query(DataUpload).filter_by(status=UploadStatus.PENDING).all()
        
        if not pending_uploads:
            print("No pending uploads found.")
            return
        
        print(f"Processing {len(pending_uploads)} pending uploads...")
        
        for upload in pending_uploads:
            try:
                success, message = upload.process_upload()
                if success:
                    print(f"✓ Processed upload {upload.id} - {upload.facility_name}")
                else:
                    print(f"✗ Failed to process upload {upload.id}: {message}")
                
                db.session.commit()
                
            except Exception as e:
                print(f"✗ Error processing upload {upload.id}: {str(e)}")
                db.session.rollback()
        
        print("Upload processing completed.")
    
    @app.cli.command()
    def generate_sample_data():
        """Generate sample data for testing."""
        from .models.upload import DataUpload
        from .models.base import PeriodType
        from datetime import datetime, timedelta
        import random
        
        if not app.config['DEBUG']:
            print("This command can only be run in debug mode!")
            return
        
        # Sample facilities
        facilities = [
            ("Mulago National Referral Hospital", "Kampala", 50000),
            ("Mbarara Regional Referral Hospital", "Mbarara", 35000),
            ("Gulu Regional Referral Hospital", "Gulu", 25000),
            ("Jinja Regional Referral Hospital", "Jinja", 30000),
            ("Hoima Regional Referral Hospital", "Hoima", 20000)
        ]
        
        # Generate sample data for each facility
        for facility_name, district, population in facilities:
            for i in range(3):  # Generate 3 months of data
                upload_date = datetime.utcnow() - timedelta(days=30 * i)
                reporting_period = f"2025-{3-i:02d}"
                
                # Generate sample raw data
                sample_raw_data = generate_sample_raw_data()
                
                upload = DataUpload(
                    filename=f"{facility_name.replace(' ', '_')}_data_{reporting_period}.csv",
                    original_filename=f"{facility_name}_data_{reporting_period}.csv",
                    facility_name=facility_name,
                    district=district,
                    total_population=population,
                    period_type=PeriodType.MONTHLY,
                    reporting_period=reporting_period,
                    uploaded_by=1,  # Assume admin user ID is 1
                    raw_data=sample_raw_data,
                    file_size=random.randint(1000, 5000)
                )
                
                db.session.add(upload)
        
        db.session.commit()
        print("Sample data generated successfully!")


def generate_sample_raw_data():
    """Generate sample raw data for testing"""
    import random
    
    # Base values with some randomization
    return {
        # ANC indicators
        '105-AN01a': random.randint(80, 120),
        '105-AN01b': random.randint(60, 90),
        '105-AN02': random.randint(70, 100),
        '105-AN04': random.randint(60, 85),
        '105-AN010': random.randint(65, 95),
        '105-AN17': random.randint(70, 90),
        '105-AN21': random.randint(65, 85),
        '105-AN23': random.randint(75, 95),
        '105-AN24a': random.randint(40, 70),
        
        # Intrapartum indicators
        '105-MA04a': random.randint(95, 125),
        '105-MA04b1': random.randint(90, 120),
        '105-MA04b2': random.randint(4, 12),
        '105-MA04c1': random.randint(1, 5),
        '105-MA04d1': random.randint(0, 3),
        '105-MA07': random.randint(3, 10),
        '105-MA11': random.randint(0, 3),
        '105-MA12': random.randint(0, 2),
        '105-MA13': random.randint(0, 2),
        '105-MA24': random.randint(1, 4),
        '105-MA25': random.randint(1, 4),
        
        # PNC indicators
        'bf_1hour': random.randint(85, 110),
        'pnc_24hrs': random.randint(80, 105),
        'pnc_6days': random.randint(70, 95),
        'pnc_6weeks': random.randint(60, 85)
    }


# Import routes and models at the end to avoid circular imports
from flask import render_template, redirect, url_for
