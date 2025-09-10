"""
Development configuration for MOH MNCAH Dashboard
"""
import os
from config.config import Config


class DevelopmentConfig(Config):
    """Development configuration class"""
    
    DEBUG = True
    FLASK_ENV = 'development'
    
    # Use SQLite for development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(Config.BASE_DIR, 'moh_dashboard_dev.db')
    
    # Development security settings (less strict)
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_SSL_STRICT = False
    
    # Enable template auto-reload
    TEMPLATES_AUTO_RELOAD = True
    
    # Development cache (simple in-memory)
    CACHE_TYPE = 'simple'
    
    # Development file paths
    UPLOAD_FOLDER = os.path.join(Config.BASE_DIR, 'uploads')
    EXPORT_FOLDER = os.path.join(Config.BASE_DIR, 'exports')
    
    # Ensure directories exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(EXPORT_FOLDER, exist_ok=True)
    
    # Development logging
    LOG_TO_STDOUT = True
    LOG_LEVEL = 'DEBUG'