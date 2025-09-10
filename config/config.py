"""
Application Configuration
This module contains configuration settings for different environments
(development, testing, production) for the MOH MNCAH Dashboard System.
"""

import os
from datetime import timedelta


class BaseConfig:
    """Base configuration with common settings"""
    
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    EXPORT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
    
    # Session configuration
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    
    # CSRF configuration
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    WTF_CSRF_SSL_STRICT = False  # Set to True in production with HTTPS
    
    # Mail configuration (for future notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '25'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Application specific settings
    APP_NAME = 'MOH MNCAH Dashboard'
    APP_VERSION = '1.0.0'
    ORGANIZATION = 'Ministry of Health Uganda'
    
    # Pagination settings
    UPLOADS_PER_PAGE = 20
    REPORTS_PER_PAGE = 10
    
    # File processing settings
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    PROCESSING_TIMEOUT = 300  # 5 minutes
    
    # Data validation settings
    ENABLE_STRICT_VALIDATION = True
    VALIDATION_LOG_LEVEL = 'INFO'
    
    # Cache settings
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Security settings
    PASSWORD_MIN_LENGTH = 6
    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = 30  # minutes
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = '100 per hour'
    
    @staticmethod
    def init_app(app):
        """Initialize application with base configuration"""
        # Create necessary directories
        os.makedirs(BaseConfig.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(BaseConfig.EXPORT_FOLDER, exist_ok=True)


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    
    DEBUG = True
    TESTING = False
    
    # Database - SQLite for development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'moh_dashboard_dev.db')
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    SQLALCHEMY_ECHO = True  # Log SQL queries
    
    # Development-specific settings
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 1
    
    # Disable CSRF for API testing in development
    WTF_CSRF_ENABLED = True
    
    # Sample data settings
    GENERATE_SAMPLE_DATA = True
    SAMPLE_FACILITIES = [
        'Mulago National Referral Hospital',
        'Mbarara Regional Referral Hospital', 
        'Gulu Regional Referral Hospital'
    ]


class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    
    DEBUG = False
    TESTING = True
    
    # In-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Fast password hashing for tests
    BCRYPT_LOG_ROUNDS = 4
    
    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False
    
    # Test-specific settings
    LOGIN_DISABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Database - PostgreSQL for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"postgresql://{os.environ.get('DB_USERNAME', 'postgres')}:" \
        f"{os.environ.get('DB_PASSWORD', '')}@" \
        f"{os.environ.get('DB_HOST', 'localhost')}:" \
        f"{os.environ.get('DB_PORT', '5432')}/" \
        f"{os.environ.get('DB_NAME', 'moh_dashboard')}"
    
    # Security settings for production
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True
    
    # Logging
    LOG_LEVEL = 'INFO'
    SQLALCHEMY_ECHO = False
    
    # Production-specific settings
    BEHIND_PROXY = True  # If behind nginx/apache
    PREFERRED_URL_SCHEME = 'https'
    
    # Cache settings for production
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Email settings for production notifications
    MAIL_SUBJECT_PREFIX = '[MOH Dashboard] '
    MAIL_SENDER = f"{BaseConfig.APP_NAME} <noreply@health.go.ug>"
    ADMINS = os.environ.get('ADMINS', '').split(',') if os.environ.get('ADMINS') else []
    
    # File storage for production
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/var/moh-dashboard/uploads')
    EXPORT_FOLDER = os.environ.get('EXPORT_FOLDER', '/var/moh-dashboard/exports')
    
    # Performance settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    @staticmethod
    def init_app(app):
        """Initialize production application"""
        BaseConfig.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


class DockerConfig(ProductionConfig):
    """Docker container configuration"""
    
    # Docker-specific overrides
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 
        'postgresql://postgres:postgres@db:5432/moh_dashboard')
    
    # Redis for caching in Docker
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
    
    # File paths for Docker volumes
    UPLOAD_FOLDER = '/app/uploads'
    EXPORT_FOLDER = '/app/exports'
    
    @staticmethod
    def init_app(app):
        """Initialize Docker application"""
        ProductionConfig.init_app(app)
        
        # Configure for containerized environment
        import logging
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


class ConfigHelper:
    """Helper class for configuration management"""
    
    @staticmethod
    def get_config(config_name=None):
        """
        Get configuration class by name
        
        Args:
            config_name: Name of configuration ('development', 'production', etc.)
            
        Returns:
            Configuration class
        """
        if config_name is None:
            config_name = os.environ.get('FLASK_ENV', 'development')
        
        return config.get(config_name, config['default'])
    
    @staticmethod
    def validate_config(app):
        """
        Validate application configuration
        
        Args:
            app: Flask application instance
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required environment variables for production
        if not app.debug:
            required_vars = ['SECRET_KEY']
            if app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('postgresql'):
                required_vars.extend(['DB_PASSWORD'])
            
            for var in required_vars:
                if not os.environ.get(var):
                    errors.append(f"Missing required environment variable: {var}")
        
        # Validate directories
        for folder in [app.config['UPLOAD_FOLDER'], app.config['EXPORT_FOLDER']]:
            if not os.path.exists(folder):
                try:
                    os.makedirs(folder, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create directory {folder}: {str(e)}")
        
        # Validate file permissions
        for folder in [app.config['UPLOAD_FOLDER'], app.config['EXPORT_FOLDER']]:
            if os.path.exists(folder):
                if not os.access(folder, os.W_OK):
                    errors.append(f"No write permission for directory: {folder}")
        
        return errors
    
    @staticmethod
    def setup_logging(app):
        """
        Setup application logging based on configuration
        
        Args:
            app: Flask application instance
        """
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Set log level
        log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
        app.logger.setLevel(log_level)
        
        # Setup file handler for non-testing environments
        if not app.testing:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                os.path.join(log_dir, 'moh_dashboard.log'),
                maxBytes=1024 * 1024 * 15,  # 15MB
                backupCount=10
            )
            
            formatter = logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            app.logger.addHandler(file_handler)
    
    @staticmethod
    def get_database_url(config_name=None):
        """
        Get database URL for given configuration
        
        Args:
            config_name: Configuration name
            
        Returns:
            Database URL string
        """
        config_class = ConfigHelper.get_config(config_name)
        return config_class.SQLALCHEMY_DATABASE_URI
    
    @staticmethod
    def is_production():
        """Check if running in production mode"""
        return os.environ.get('FLASK_ENV') == 'production'
    
    @staticmethod
    def is_development():
        """Check if running in development mode"""
        return os.environ.get('FLASK_ENV', 'development') == 'development'