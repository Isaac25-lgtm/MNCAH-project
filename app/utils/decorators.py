"""
Utility Decorators
This module provides decorators for authentication, authorization, and other utility functions
for the MOH MNCAH Dashboard System.
"""

from functools import wraps
from flask import abort, request, jsonify, flash, redirect, url_for
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)


def admin_required(f):
    """
    Decorator to require admin privileges
    
    Usage:
        @admin_required
        def admin_only_view():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            logger.warning(f"Non-admin user {current_user.username} attempted to access admin-only resource")
            
            if request.is_json:
                return jsonify({'error': 'Admin privileges required'}), 403
            
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def stakeholder_or_admin_required(f):
    """
    Decorator to require stakeholder or admin privileges (any authenticated user)
    
    Usage:
        @stakeholder_or_admin_required
        def view_data():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        if not current_user.is_active():
            logger.warning(f"Inactive user {current_user.username} attempted to access protected resource")
            
            if request.is_json:
                return jsonify({'error': 'Account is inactive'}), 403
            
            flash('Your account is inactive. Please contact administrator.', 'error')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def permission_required(permission):
    """
    Decorator to require specific permission
    
    Args:
        permission: Permission string to check
        
    Usage:
        @permission_required('upload_data')
        def upload_view():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('auth.login'))
            
            if permission not in current_user.get_permissions():
                logger.warning(f"User {current_user.username} lacks permission '{permission}' for resource")
                
                if request.is_json:
                    return jsonify({'error': f'Permission "{permission}" required'}), 403
                
                flash(f'Access denied. Required permission: {permission}', 'error')
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def can_upload_data(f):
    """
    Decorator to check if user can upload data
    
    Usage:
        @can_upload_data
        def upload_view():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        if not current_user.can_upload_data():
            logger.warning(f"User {current_user.username} cannot upload data")
            
            if request.is_json:
                return jsonify({'error': 'Data upload permission required'}), 403
            
            flash('Access denied. Data upload permission required.', 'error')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def json_required(f):
    """
    Decorator to require JSON content type
    
    Usage:
        @json_required
        def api_endpoint():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'JSON content type required'}), 400
        return f(*args, **kwargs)
    
    return decorated_function


def validate_json_fields(required_fields):
    """
    Decorator to validate required JSON fields
    
    Args:
        required_fields: List of required field names
        
    Usage:
        @validate_json_fields(['name', 'email'])
        def create_user():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'JSON content type required'}), 400
            
            data = request.get_json()
            missing_fields = []
            
            for field in required_fields:
                if field not in data or data[field] is None or str(data[field]).strip() == '':
                    missing_fields.append(field)
            
            if missing_fields:
                return jsonify({
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def rate_limit(max_requests=100, window=3600):
    """
    Simple rate limiting decorator
    
    Args:
        max_requests: Maximum requests allowed
        window: Time window in seconds
        
    Usage:
        @rate_limit(max_requests=10, window=60)
        def api_endpoint():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple implementation - in production, use Redis or proper rate limiter
            # This is a placeholder for demonstration
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def log_activity(action_type=None):
    """
    Decorator to log user activity
    
    Args:
        action_type: Type of action being performed
        
    Usage:
        @log_activity('data_upload')
        def upload_data():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Log the activity
            user_info = f"{current_user.username} ({current_user.user_type.value})" if current_user.is_authenticated else "Anonymous"
            action = action_type or f.__name__
            
            logger.info(f"Activity: {action} by {user_info} from {request.remote_addr}")
            
            # Execute the function
            result = f(*args, **kwargs)
            
            # Log completion
            logger.info(f"Completed: {action} by {user_info}")
            
            return result
        
        return decorated_function
    return decorator


def handle_file_upload(allowed_extensions=None, max_size=None):
    """
    Decorator to handle file upload validation
    
    Args:
        allowed_extensions: Set of allowed file extensions
        max_size: Maximum file size in bytes
        
    Usage:
        @handle_file_upload(allowed_extensions={'csv', 'xlsx'}, max_size=15*1024*1024)
        def upload_file():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                if request.is_json:
                    return jsonify({'error': 'No file uploaded'}), 400
                flash('No file uploaded', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                if request.is_json:
                    return jsonify({'error': 'No file selected'}), 400
                flash('No file selected', 'error')
                return redirect(request.url)
            
            # Check file extension
            if allowed_extensions:
                if '.' not in file.filename or \
                   file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                    error_msg = f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
                    if request.is_json:
                        return jsonify({'error': error_msg}), 400
                    flash(error_msg, 'error')
                    return redirect(request.url)
            
            # Check file size (this is approximate as file is in memory)
            if max_size:
                # Note: This is a simplified check. In production, you'd want more robust size checking
                pass
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def cache_response(timeout=300):
    """
    Decorator to cache response (placeholder - implement with Redis/Memcached in production)
    
    Args:
        timeout: Cache timeout in seconds
        
    Usage:
        @cache_response(timeout=600)
        def expensive_calculation():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Placeholder implementation
            # In production, implement proper caching with Redis/Memcached
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_form_fields(required_fields):
    """
    Decorator to validate required form fields
    
    Args:
        required_fields: List of required field names
        
    Usage:
        @validate_form_fields(['facility_name', 'population'])
        def process_form():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            missing_fields = []
            
            for field in required_fields:
                value = request.form.get(field, '').strip()
                if not value:
                    missing_fields.append(field)
            
            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                if request.is_json:
                    return jsonify({
                        'error': error_msg,
                        'missing_fields': missing_fields
                    }), 400
                
                flash(error_msg, 'error')
                return redirect(request.url)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def exception_handler(f):
    """
    Decorator to handle exceptions gracefully
    
    Usage:
        @exception_handler
        def risky_function():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Exception in {f.__name__}: {str(e)}", exc_info=True)
            
            if request.is_json:
                return jsonify({
                    'error': 'An error occurred',
                    'message': 'Please try again or contact support'
                }), 500
            
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('dashboard.index'))
    
    return decorated_function


def measure_performance(f):
    """
    Decorator to measure function performance
    
    Usage:
        @measure_performance
        def slow_function():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import time
        start_time = time.time()
        
        result = f(*args, **kwargs)
        
        execution_time = time.time() - start_time
        
        if execution_time > 1.0:  # Log slow operations
            logger.warning(f"Slow operation: {f.__name__} took {execution_time:.2f} seconds")
        else:
            logger.debug(f"Performance: {f.__name__} took {execution_time:.3f} seconds")
        
        return result
    
    return decorated_function


def require_fresh_login(f):
    """
    Decorator to require fresh login for sensitive operations
    
    Usage:
        @require_fresh_login
        def change_password():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import fresh_login_required
        
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        # Check if login is fresh (implement based on your session management)
        # This is a placeholder - implement based on your fresh login requirements
        
        return f(*args, **kwargs)
    
    return decorated_function


# Utility functions for decorators
def get_client_ip():
    """Get client IP address accounting for proxies"""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    else:
        return request.remote_addr


def is_safe_url(target):
    """Check if redirect URL is safe"""
    from urllib.parse import urlparse, urljoin
    from flask import request
    
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc
