"""
Authentication Views
This module handles user authentication (login/logout) for the MOH MNCAH Dashboard.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
try:
    from werkzeug.urls import url_parse
except ImportError:
    from urllib.parse import urlparse
    def url_parse(url):
        return urlparse(url)
import logging

from ..models.user import User, UserManager, UserSession, UserType
from .. import db


# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login for both admin and stakeholder users
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        # Handle both form and JSON requests
        if request.is_json:
            data = request.get_json()
            username = data.get('username', '').strip()
            password = data.get('password', '')
            remember_me = data.get('remember', False)
        else:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            remember_me = bool(request.form.get('remember'))
        
        # Validate input
        if not username or not password:
            error_msg = 'Username and password are required'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/login.html')
        
        # Authenticate user
        try:
            user = UserManager.authenticate_user(username, password, db.session)
            
            if user:
                # Successful authentication
                login_user(user, remember=remember_me)
                
                # Create user session
                user_session = UserSession(user)
                session['user_session'] = user_session.to_session_dict()
                
                # Log successful login
                logger.info(f"User {username} logged in successfully from {request.remote_addr}")
                
                # Determine redirect URL
                next_page = request.args.get('next')
                if not next_page or url_parse(next_page).netloc != '':
                    next_page = url_for('dashboard.index')
                
                success_msg = f'Welcome, {user.full_name or user.username}!'
                
                if request.is_json:
                    return jsonify({
                        'success': True,
                        'message': success_msg,
                        'redirect': next_page,
                        'user': {
                            'username': user.username,
                            'user_type': user.user_type.value,
                            'full_name': user.full_name,
                            'permissions': user.get_permissions()
                        }
                    })
                
                flash(success_msg, 'success')
                return redirect(next_page)
            
            else:
                # Authentication failed
                error_msg = 'Invalid username or password'
                logger.warning(f"Failed login attempt for username: {username} from {request.remote_addr}")
                
                if request.is_json:
                    return jsonify({'success': False, 'message': error_msg}), 401
                
                flash(error_msg, 'error')
                return render_template('auth/login.html')
        
        except Exception as e:
            error_msg = 'An error occurred during login. Please try again.'
            logger.error(f"Login error for {username}: {str(e)}")
            
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 500
            
            flash(error_msg, 'error')
            return render_template('auth/login.html')
    
    # GET request - show login form
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Public registration for stakeholder users
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip() or None
        email = request.form.get('email', '').strip() or None

        # Basic validation
        if not username or not password or not confirm:
            flash('Username and both password fields are required.', 'error')
            return render_template('auth/register.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')

        # Uniqueness check
        existing = db.session.query(User).filter(User.username == username.lower()).first()
        if existing:
            flash('Username is already taken.', 'error')
            return render_template('auth/register.html')

        try:
            # Create stakeholder by default
            user = UserManager.create_user(
                username=username,
                password=password,
                user_type=UserType.STAKEHOLDER,
                session=db.session,
                full_name=full_name,
                email=email
            )
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error for {username}: {str(e)}")
            flash('Error creating account. Please try again.', 'error')
            return render_template('auth/register.html')

    # GET
    return render_template('auth/register.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """
    Handle user logout
    """
    username = current_user.username
    user_type = current_user.user_type.value
    
    # Clear session data
    session.pop('user_session', None)
    
    # Logout user
    logout_user()
    
    # Log logout
    logger.info(f"User {username} ({user_type}) logged out from {request.remote_addr}")
    
    # Handle JSON requests
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Logged out successfully',
            'redirect': url_for('auth.login')
        })
    
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/status')
@login_required
def status():
    """
    Get current authentication status (API endpoint)
    """
    user_session_data = session.get('user_session', {})
    
    return jsonify({
        'authenticated': True,
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'user_type': current_user.user_type.value,
            'full_name': current_user.full_name,
            'organization': current_user.organization,
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None,
            'permissions': current_user.get_permissions()
        },
        'session': user_session_data
    })


@auth_bp.route('/check')
def check():
    """
    Check authentication status without requiring login (for AJAX calls)
    """
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user_type': current_user.user_type.value,
            'username': current_user.username,
            'permissions': current_user.get_permissions()
        })
    
    return jsonify({'authenticated': False})


@auth_bp.route('/profile')
@login_required
def profile():
    """
    Display user profile information
    """
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """
    Update user profile information
    """
    try:
        # Get form data
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip() or None
        phone_number = request.form.get('phone_number', '').strip() or None
        organization = request.form.get('organization', '').strip() or None
        position = request.form.get('position', '').strip() or None
        
        # Update user information
        current_user.full_name = full_name
        current_user.email = email
        current_user.phone_number = phone_number
        current_user.organization = organization
        current_user.position = position
        
        # Commit changes
        db.session.commit()
        
        logger.info(f"User {current_user.username} updated profile information")
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully'
            })
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating profile for {current_user.username}: {str(e)}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'message': 'Error updating profile. Please try again.'
            }), 500
        
        flash('Error updating profile. Please try again.', 'error')
        return redirect(url_for('auth.profile'))


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    Change user password
    """
    try:
        # Get form data
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate input
        if not current_password or not new_password or not confirm_password:
            error_msg = 'All password fields are required'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('auth.profile'))
        
        # Verify current password
        if not current_user.check_password(current_password):
            error_msg = 'Current password is incorrect'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('auth.profile'))
        
        # Check password confirmation
        if new_password != confirm_password:
            error_msg = 'New passwords do not match'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('auth.profile'))
        
        # Validate password strength (basic)
        if len(new_password) < 6:
            error_msg = 'Password must be at least 6 characters long'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('auth.profile'))
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        logger.info(f"User {current_user.username} changed password")
        
        success_msg = 'Password changed successfully'
        if request.is_json:
            return jsonify({'success': True, 'message': success_msg})
        
        flash(success_msg, 'success')
        return redirect(url_for('auth.profile'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing password for {current_user.username}: {str(e)}")
        
        error_msg = 'Error changing password. Please try again.'
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg}), 500
        
        flash(error_msg, 'error')
        return redirect(url_for('auth.profile'))


@auth_bp.route('/admin/users')
@login_required
def list_users():
    """
    List all users (admin only)
    """
    # Check if user is admin
    if not current_user.is_admin():
        if request.is_json:
            return jsonify({'error': 'Access denied'}), 403
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    try:
        users = db.session.query(User).all()
        
        if request.is_json:
            return jsonify({
                'users': [user.to_dict() for user in users]
            })
        
        return render_template('auth/users.html', users=users)
    
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        
        if request.is_json:
            return jsonify({'error': 'Error retrieving users'}), 500
        
        flash('Error retrieving user list.', 'error')
        return redirect(url_for('dashboard.index'))


@auth_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """
    Toggle user active/inactive status (admin only)
    """
    # Check if user is admin
    if not current_user.is_admin():
        if request.is_json:
            return jsonify({'error': 'Access denied'}), 403
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    try:
        user = db.session.get(User, user_id)
        if not user:
            if request.is_json:
                return jsonify({'error': 'User not found'}), 404
            flash('User not found.', 'error')
            return redirect(url_for('auth.list_users'))
        
        # Don't allow admin to deactivate themselves
        if user.id == current_user.id:
            error_msg = 'Cannot change your own account status'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('auth.list_users'))
        
        # Toggle status
        if user.is_active():
            user.deactivate()
            action = 'deactivated'
        else:
            user.activate()
            action = 'activated'
        
        db.session.commit()
        
        logger.info(f"Admin {current_user.username} {action} user {user.username}")
        
        success_msg = f'User {user.username} has been {action}'
        if request.is_json:
            return jsonify({
                'success': True,
                'message': success_msg,
                'user_status': user.status.value
            })
        
        flash(success_msg, 'success')
        return redirect(url_for('auth.list_users'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling user status: {str(e)}")
        
        error_msg = 'Error updating user status'
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg}), 500
        
        flash(error_msg, 'error')
        return redirect(url_for('auth.list_users'))


# Error handlers for authentication blueprint
@auth_bp.errorhandler(401)
def handle_unauthorized(error):
    """Handle unauthorized access"""
    if request.is_json:
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
    return redirect(url_for('auth.login'))


@auth_bp.errorhandler(403)
def handle_forbidden(error):
    """Handle forbidden access"""
    if request.is_json:
        return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403
    flash('Access denied. Insufficient privileges.', 'error')
    return redirect(url_for('dashboard.index'))


# Context processor for authentication templates
@auth_bp.app_context_processor
def inject_auth_data():
    """Inject authentication data into templates"""
    return {
        'current_user': current_user,
        'user_session': session.get('user_session', {}),
        'app_name': 'MOH MNCAH Dashboard'
    }
