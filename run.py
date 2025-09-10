#!/usr/bin/env python3
"""
Ministry of Health MNCAH Dashboard
Flask application runner - Fixed version
"""

import os
import logging
from flask.logging import default_handler

# Reduce SQLAlchemy logging noise
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from app import create_app, db
from config.config import config, DevelopmentConfig

# Get configuration from environment variable or use default
config_name = os.environ.get('FLASK_CONFIG', 'development')
app = create_app(config_name)

# Configure logging
if not app.debug:
    # Use console logging for simplicity
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('MOH MNCAH Dashboard startup')

@app.shell_context_processor
def make_shell_context():
    """Make database and models available in Flask shell"""
    from app.models.user import User
    from app.models.upload import DataUpload
    from app.models.anc import AntenatalCare
    from app.models.intrapartum import IntrapartumCare
    from app.models.pnc import PostnatalCare
    from app.services.calculation_service import MNCHACalculationService
    from app.services.validation_service import DataValidationService
    
    return {
        'db': db, 
        'User': User, 
        'DataUpload': DataUpload,
        'AntenatalCare': AntenatalCare,
        'IntrapartumCare': IntrapartumCare,
        'PostnatalCare': PostnatalCare,
        'MNCHACalculationService': MNCHACalculationService,
        'DataValidationService': DataValidationService
    }

def create_default_users():
    """Create default users if they don't exist"""
    try:
        from app.models.user import User, UserType
        from app import db

        # Check if users already exist
        existing_users = db.session.query(User).count()
        if existing_users > 0:
            app.logger.info(f"Found {existing_users} existing users, skipping default user creation")
            return

        # Create admin user (isaac/isaac)
        admin_user = User(
            username='isaac',
            email='isaac@health.go.ug',
            full_name='Isaac Adminisrator',
            organization='Ministry of Health Uganda',
            position='System Administrator',
            user_type=UserType.ADMIN
        )
        admin_user.set_password('isaac')
        
        # Create stakeholder user
        stakeholder_user = User(
            username='stakeholder',
            email='stakeholder@health.go.ug', 
            full_name='Health Stakeholder',
            organization='Health Partner Organization',
            position='Data Analyst',
            user_type=UserType.STAKEHOLDER
        )
        stakeholder_user.set_password('stakeholder123')
        
        db.session.add(admin_user)
        db.session.add(stakeholder_user)
        db.session.commit()

        app.logger.info("Default users created successfully")

    except Exception as e:
        app.logger.error(f"Error creating default users: {e}")
        db.session.rollback()

def init_database():
    """Initialize database tables"""
    try:
        with app.app_context():
            # Create all database tables
            # Create Flask-SQLAlchemy tables
            db.create_all()
            # Also ensure Base models are created
            from app.models.user import Base as UserBase
            from app.models.upload import Base as UploadBase
            engine = db.engine
            UserBase.metadata.create_all(bind=engine)
            UploadBase.metadata.create_all(bind=engine)
            app.logger.info("Database tables created")
            
            # Create default users
            create_default_users()
            
    except Exception as e:
        app.logger.error(f"Error initializing database: {e}")

# CLI Commands
@app.cli.command('init-db')
def init_db_command():
    """Initialize the database with tables and default users"""
    init_database()
    print("Database initialized successfully!")

@app.cli.command('create-admin')
def create_admin_command():
    """Create a new admin user interactively"""
    from app.models.user import User, UserType
    
    username = input("Username: ")
    password = input("Password: ")
    email = input("Email: ")
    full_name = input("Full Name: ")
    
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        organization='Ministry of Health Uganda',
        user_type=UserType.ADMIN
    )
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        print(f"Admin user '{username}' created successfully!")
    except Exception as e:
        print(f"Error creating user: {e}")
        db.session.rollback()

@app.cli.command('list-users')
def list_users_command():
    """List all users in the system"""
    from app.models.user import User

    users = db.session.query(User).all()
    if not users:
        print("No users found.")
        return
    
    print("\nCurrent Users:")
    print("-" * 50)
    for user in users:
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Type: {user.user_type.value}")
        print(f"Status: {user.status.value}")
        print(f"Created: {user.created_at}")
        print("-" * 50)

@app.cli.command('reset-db')
def reset_db_command():
    """Reset database (development only)"""
    if app.config['FLASK_ENV'] != 'development':
        print("This command can only be run in development mode!")
        return
    
    if input("Are you sure you want to reset the database? (yes/no): ").lower() == 'yes':
        db.drop_all()
        db.create_all()
        create_default_users()
        print("Database reset successfully!")
    else:
        print("Database reset cancelled.")

@app.cli.command('generate-sample-data')
def generate_sample_data_command():
    """Generate sample MNCAH data for testing"""
    from datetime import datetime, timedelta
    from app.models.upload import DataUpload, UploadStatus
    import random
    
    facilities = [
        {"name": "Mulago National Referral Hospital", "district": "Kampala", "population": 150000},
        {"name": "Mbarara Regional Referral Hospital", "district": "Mbarara", "population": 85000},
        {"name": "Gulu Regional Referral Hospital", "district": "Gulu", "population": 75000},
        {"name": "Mbale Regional Referral Hospital", "district": "Mbale", "population": 80000},
        {"name": "Fort Portal Regional Referral Hospital", "district": "Kabarole", "population": 65000},
        {"name": "Hoima Regional Referral Hospital", "district": "Hoima", "population": 55000},
        {"name": "Soroti Regional Referral Hospital", "district": "Soroti", "population": 60000},
        {"name": "Arua Regional Referral Hospital", "district": "Arua", "population": 70000}
    ]
    
    try:
        from app.models.user import User
        from app import db
        admin_user = db.session.query(User).filter_by(username='isaac').first()
        
        if not admin_user:
            print("Admin user not found. Run 'flask init-db' first.")
            return
        
        for i, facility in enumerate(facilities):
            # Generate data for last 6 months
            for month_offset in range(6):
                reporting_date = datetime.now() - timedelta(days=30 * month_offset)
                
                # Generate realistic MNCAH data with some randomness
                sample_data = {
                    '105-AN01a_ANC_1st_Visit_women': int(facility['population'] * 0.05 * random.uniform(0.8, 1.2)),
                    '105-AN01b_ANC_1st_Visit_1st_Trimester': int(facility['population'] * 0.05 * random.uniform(0.3, 0.5)),
                    '105-AN02_ANC_4th_Visit_women': int(facility['population'] * 0.05 * random.uniform(0.6, 0.9)),
                    '105-AN04_ANC_8_contacts_women': int(facility['population'] * 0.05 * random.uniform(0.4, 0.7)),
                    '105-AN010_Third_dose_IPT': int(facility['population'] * 0.05 * random.uniform(0.7, 0.9)),
                    '105-MA04b1_Deliveries_live_births_total': int(facility['population'] * 0.0485 * random.uniform(0.6, 0.8)),
                    '105-MA04b2_Deliveries_live_births_less_2_5kg': int(facility['population'] * 0.0485 * random.uniform(0.05, 0.12)),
                    'Post_Natal_Attendances_24Hrs': int(facility['population'] * 0.0485 * random.uniform(0.8, 1.0)),
                }
                
                upload = DataUpload(
                    facility_name=facility['name'],
                    district=facility['district'],
                    reporting_period='monthly',
                    reporting_date=reporting_date,
                    population=facility['population'],
                    filename=f"{facility['name'].replace(' ', '_')}_sample_data_{month_offset}.xlsx",
                    file_size=1024,
                    raw_data=sample_data,
                    processed_data={},
                    status=UploadStatus.COMPLETED,
                    uploaded_by=admin_user.id
                )
                
                db.session.add(upload)
        
        db.session.commit()
        print(f"Sample data generated for {len(facilities)} facilities over 6 months!")
        
    except Exception as e:
        print(f"Error generating sample data: {e}")
        db.session.rollback()

# Initialize database on first run
if __name__ == '__main__':
    with app.app_context():
        try:
            # Try to create tables if they don't exist
            db.create_all()
            from app.models.user import Base as UserBase
            from app.models.upload import Base as UploadBase
            engine = db.engine
            UserBase.metadata.create_all(bind=engine)
            UploadBase.metadata.create_all(bind=engine)
            create_default_users()
        except Exception as e:
            app.logger.error(f"Startup initialization error: {e}")
    
    # Run only on localhost for security
    app.run(host="127.0.0.1", port=5000, debug=True)
#!/usr/bin/env python3
"""
Application Entry Point
This is the main entry point for the MOH MNCAH Dashboard Flask application.
"""

import os
import logging
from flask.logging import default_handler

from app import create_app, db
from config import ConfigHelper

# Get configuration name from environment
config_name = os.environ.get('FLASK_ENV', 'development')

# Create Flask application
app = create_app(config_name)

# Configure logging
ConfigHelper.setup_logging(app)

# Validate configuration
config_errors = ConfigHelper.validate_config(app)
if config_errors:
    app.logger.error("Configuration errors detected:")
    for error in config_errors:
        app.logger.error(f"  - {error}")
    
    if not app.debug:
        raise SystemExit("Configuration errors prevent application startup")
    else:
        app.logger.warning("Running in debug mode despite configuration errors")


@app.shell_context_processor
def make_shell_context():
    """
    Shell context processor to make objects available in Flask shell
    """
    from app.models.user import User, UserType, UserStatus
    from app.models.upload import DataUpload, UploadStatus
    from app.models.base import PopulationData, PeriodType, ValidationStatus
    from app.models.anc import AntenatalCare
    from app.models.intrapartum import IntrapartumCare
    from app.models.pnc import PostnatalCare
    from app.services.calculation_service import MNCHACalculationService
    from app.services.validation_service import DataValidationService
    
    return {
        'db': db,
        'app': app,
        'User': User,
        'UserType': UserType,
        'UserStatus': UserStatus,
        'DataUpload': DataUpload,
        'UploadStatus': UploadStatus,
        'PopulationData': PopulationData,
        'PeriodType': PeriodType,
        'ValidationStatus': ValidationStatus,
        'AntenatalCare': AntenatalCare,
        'IntrapartumCare': IntrapartumCare,
        'PostnatalCare': PostnatalCare,
        'MNCHACalculationService': MNCHACalculationService,
        'DataValidationService': DataValidationService
    }


@app.before_request
def before_first_request():
    """
    Actions to perform before handling first request
    """
    if not hasattr(app, '_startup_logged'):
        app.logger.info("MOH MNCAH Dashboard starting up...")
        app.logger.info(f"Configuration: {config_name}")
        app.logger.info(f"Debug mode: {app.debug}")
        app.logger.info(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'}")
        app._startup_logged = True


@app.after_request
def after_request(response):
    """
    Add security headers and log requests
    """
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Only add HSTS in production with HTTPS
    if not app.debug and app.config.get('PREFERRED_URL_SCHEME') == 'https':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Log requests (only errors and warnings in production)
    if response.status_code >= 400:
        app.logger.warning(f"{response.status_code} response for {request.method} {request.path}")
    
    return response


@app.errorhandler(Exception)
def handle_exception(error):
    """
    Global exception handler
    """
    # Log the exception
    app.logger.error(f"Unhandled exception: {error}", exc_info=True)
    
    # Return appropriate response
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    
    return render_template('errors/500.html'), 500


# CLI Commands
@app.cli.command()
def deploy():
    """
    Run deployment tasks for production
    """
    from flask_migrate import upgrade
    from app.models.user import User
    
    print("Starting deployment...")
    
    # Create database tables
    print("Creating/updating database tables...")
    upgrade()
    
    # Create default admin user if none exists
    if db.session.query(User).filter_by(user_type='admin').count() == 0:
        print("Creating default admin user...")
        admin = User.create_default_users()[0]  # Get the admin user
        db.session.add(admin)
        db.session.commit()
        print(f"Created admin user: {admin.username}")
    
    print("Deployment completed successfully!")


@app.cli.command()
def test():
    """
    Run unit tests
    """
    import unittest
    import sys
    
    print("Running tests...")
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with non-zero code if tests failed
    if not result.wasSuccessful():
        sys.exit(1)


@app.cli.command()
def lint():
    """
    Run code linting
    """
    import subprocess
    import sys
    
    print("Running flake8...")
    result = subprocess.run(['flake8', 'app/', '--max-line-length=120'], 
                          capture_output=True, text=True)
    
    if result.stdout:
        print("Linting issues found:")
        print(result.stdout)
    
    if result.stderr:
        print("Linting errors:")
        print(result.stderr)
    
    if result.returncode != 0:
        print("Linting failed!")
        sys.exit(1)
    else:
        print("Linting passed!")


@app.cli.command()
def backup_db():
    """
    Create database backup
    """
    import subprocess
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
        # PostgreSQL backup
        backup_file = f"backup_moh_dashboard_{timestamp}.sql"
        
        # Extract database connection info
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        # Parse URL and create pg_dump command
        print(f"Creating PostgreSQL backup: {backup_file}")
        # Implementation would depend on your PostgreSQL setup
        
    elif app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
        # SQLite backup
        import shutil
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        backup_file = f"backup_moh_dashboard_{timestamp}.db"
        
        print(f"Creating SQLite backup: {backup_file}")
        shutil.copy2(db_path, backup_file)
        print(f"Backup created successfully: {backup_file}")
    
    else:
        print("Unsupported database type for backup")


@app.cli.command()
def create_sample_data():
    """
    Create sample data for development/testing
    """
    from app.models.upload import DataUpload
    from app.models.base import PeriodType
    from datetime import datetime, timedelta
    import random
    
    if not app.debug:
        print("Sample data can only be created in debug mode")
        return
    
    print("Creating sample data...")
    
    # Sample facilities
    facilities = [
        ("Mulago National Referral Hospital", "Kampala", "Central", 50000),
        ("Mbarara Regional Referral Hospital", "Mbarara", "Western", 35000),
        ("Gulu Regional Referral Hospital", "Gulu", "Northern", 25000),
        ("Jinja Regional Referral Hospital", "Jinja", "Eastern", 30000),
        ("Hoima Regional Referral Hospital", "Hoima", "Western", 20000),
        ("Mbale Regional Referral Hospital", "Mbale", "Eastern", 28000),
        ("Arua Regional Referral Hospital", "Arua", "Northern", 22000),
        ("Fort Portal Regional Referral Hospital", "Kabarole", "Western", 18000)
    ]
    
    created_uploads = 0
    
    for facility_name, district, region, population in facilities:
        # Create 6 months of data for each facility
        for i in range(6):
            upload_date = datetime.utcnow() - timedelta(days=30 * i)
            reporting_period = upload_date.strftime("%Y-%m")
            
            # Generate realistic sample data
            raw_data = generate_realistic_raw_data(population, i)
            
            upload = DataUpload(
                filename=f"{facility_name.replace(' ', '_')}_data_{reporting_period}.csv",
                original_filename=f"{facility_name}_data_{reporting_period}.csv",
                facility_name=facility_name,
                district=district,
                region=region,
                total_population=population,
                period_type=PeriodType.MONTHLY,
                reporting_period=reporting_period,
                uploaded_by=1,  # Admin user
                raw_data=raw_data,
                file_size=random.randint(2000, 8000),
                uploaded_at=upload_date
            )
            
            db.session.add(upload)
            created_uploads += 1
    
    # Process all uploads
    db.session.commit()
    
    print(f"Created {created_uploads} sample uploads")
    
    # Process the uploads
    print("Processing uploads...")
    pending_uploads = db.session.query(DataUpload).all()
    
    for upload in pending_uploads:
        try:
            upload.process_upload()
            db.session.commit()
        except Exception as e:
            print(f"Error processing upload {upload.id}: {str(e)}")
            db.session.rollback()
    
    print("Sample data creation completed!")


def generate_realistic_raw_data(population, month_offset=0):
    """Generate realistic raw data with some variation"""
    import random
    
    # Base values that vary by facility and time
    base_multiplier = 1.0 + (random.random() - 0.5) * 0.3  # ±15% variation
    seasonal_factor = 1.0 + 0.1 * math.sin(month_offset * math.pi / 6)  # Seasonal variation
    
    # Expected pregnancies and deliveries
    expected_pregnancies = int(population * 0.05 / 12 * base_multiplier * seasonal_factor)
    expected_deliveries = int(population * 0.0485 / 12 * base_multiplier * seasonal_factor)
    
    return {
        # ANC indicators - based on expected pregnancies
        '105-AN01a': int(expected_pregnancies * random.uniform(0.8, 1.2)),
        '105-AN01b': int(expected_pregnancies * random.uniform(0.6, 0.9)),
        '105-AN02': int(expected_pregnancies * random.uniform(0.65, 0.95)),
        '105-AN04': int(expected_pregnancies * random.uniform(0.55, 0.85)),
        '105-AN010': int(expected_pregnancies * random.uniform(0.7, 0.95)),
        '105-AN17': int(expected_pregnancies * random.uniform(0.65, 0.9)),
        '105-AN21': int(expected_pregnancies * random.uniform(0.6, 0.85)),
        '105-AN23': int(expected_pregnancies * random.uniform(0.75, 0.95)),
        '105-AN24a': int(expected_pregnancies * random.uniform(0.4, 0.7)),
        
        # Intrapartum indicators - based on expected deliveries
        '105-MA04a': int(expected_deliveries * random.uniform(0.95, 1.05)),
        '105-MA04b1': int(expected_deliveries * random.uniform(0.92, 1.02)),
        '105-MA04b2': max(0, int(expected_deliveries * random.uniform(0.04, 0.12))),
        '105-MA04c1': max(0, int(expected_deliveries * random.uniform(0.002, 0.01))),
        '105-MA04d1': max(0, int(expected_deliveries * random.uniform(0.001, 0.005))),
        '105-MA07': max(0, int(expected_deliveries * random.uniform(0.03, 0.1))),
        '105-MA11': max(0, int(expected_deliveries * random.uniform(0.002, 0.008))),
        '105-MA12': max(0, int(expected_deliveries * random.uniform(0.001, 0.004))),
        '105-MA13': max(0, int(expected_deliveries * random.uniform(0.0001, 0.003))),
        '105-MA24': max(0, int(expected_deliveries * random.uniform(0.005, 0.02))),
        '105-MA25': max(0, int(expected_deliveries * random.uniform(0.004, 0.018))),
        
        # PNC indicators - based on deliveries
        'bf_1hour': int(expected_deliveries * random.uniform(0.85, 1.0)),
        'pnc_24hrs': int(expected_deliveries * random.uniform(0.8, 0.98)),
        'pnc_6days': int(expected_deliveries * random.uniform(0.65, 0.9)),
        'pnc_6weeks': int(expected_deliveries * random.uniform(0.55, 0.8))
    }


if __name__ == '__main__':
    import math
    from flask import request, jsonify, render_template
    
    # Run the application
    app.run(
        host=os.environ.get('FLASK_HOST', '127.0.0.1'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=app.debug
    )
