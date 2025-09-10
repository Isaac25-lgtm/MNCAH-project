"""
User Model for Authentication and Authorization
This module handles user management for the MOH MNCAH Dashboard System.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates

Base = declarative_base()


class UserType(Enum):
    """User types for the MNCAH dashboard system"""
    ADMIN = "admin"        # Ministry of Health users - can upload and view data
    STAKEHOLDER = "stakeholder"  # External stakeholders - can only view data


class UserStatus(Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(Base, UserMixin):
    """
    User model for authentication and authorization
    
    Supports two user types:
    1. ADMIN (Ministry of Health): Can upload data, view all analyses, generate reports
    2. STAKEHOLDER: Can only view data and analyses, no upload permissions
    """
    
    __tablename__ = 'users'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Authentication fields
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User information
    full_name = Column(String(200), nullable=True)
    organization = Column(String(200), nullable=True)
    position = Column(String(150), nullable=True)
    phone_number = Column(String(20), nullable=True)
    
    # Authorization
    user_type = Column(SQLEnum(UserType), nullable=False, default=UserType.STAKEHOLDER)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    
    # Security features
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    
    def __init__(self, username: str, password: str, user_type: UserType = UserType.STAKEHOLDER, **kwargs):
        """
        Initialize user with required fields
        
        Args:
            username: Unique username for authentication
            password: Plain text password (will be hashed)
            user_type: Type of user (admin or stakeholder)
            **kwargs: Additional user fields
        """
        self.username = username.lower().strip()
        self.set_password(password)
        self.user_type = user_type
        
        # Set optional fields
        for field, value in kwargs.items():
            if hasattr(self, field):
                setattr(self, field, value)
    
    def set_password(self, password: str) -> None:
        """
        Set user password (automatically hashed)
        
        Args:
            password: Plain text password
        """
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def check_password(self, password: str) -> bool:
        """
        Check if provided password matches stored hash
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self) -> bool:
        """Check if user is an admin (can upload data)"""
        return self.user_type == UserType.ADMIN
    
    def is_stakeholder(self) -> bool:
        """Check if user is a stakeholder (view-only)"""
        return self.user_type == UserType.STAKEHOLDER
    
    def can_upload_data(self) -> bool:
        """Check if user can upload data"""
        return self.is_admin() and self.is_active()
    
    def can_view_data(self) -> bool:
        """Check if user can view data and analyses"""
        return self.is_active()
    
    def can_generate_reports(self) -> bool:
        """Check if user can generate reports"""
        return self.is_active()  # Both admin and stakeholder can generate reports
    
    def is_active(self) -> bool:
        """Check if user account is active"""
        return (self.status == UserStatus.ACTIVE and 
                (self.account_locked_until is None or 
                 self.account_locked_until < datetime.utcnow()))
    
    def is_authenticated(self) -> bool:
        """Required by Flask-Login"""
        return True
    
    def is_anonymous(self) -> bool:
        """Required by Flask-Login"""
        return False
    
    def get_id(self) -> str:
        """Required by Flask-Login - return user ID as string"""
        return str(self.id)
    
    def record_login(self) -> None:
        """Record successful login"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        self.failed_login_attempts = 0  # Reset failed attempts on successful login
    
    def record_failed_login(self) -> None:
        """Record failed login attempt"""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def unlock_account(self) -> None:
        """Unlock user account (admin function)"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
    
    def deactivate(self) -> None:
        """Deactivate user account"""
        self.status = UserStatus.INACTIVE
    
    def activate(self) -> None:
        """Activate user account"""
        self.status = UserStatus.ACTIVE
        self.unlock_account()
    
    def suspend(self) -> None:
        """Suspend user account"""
        self.status = UserStatus.SUSPENDED
    
    def get_permissions(self) -> List[str]:
        """
        Get list of user permissions
        
        Returns:
            List of permission strings
        """
        permissions = []
        
        if self.can_view_data():
            permissions.extend([
                'view_dashboard',
                'view_analysis',
                'view_indicators',
                'view_trends'
            ])
        
        if self.can_generate_reports():
            permissions.extend([
                'generate_reports',
                'export_data',
                'download_reports'
            ])
        
        if self.can_upload_data():
            permissions.extend([
                'upload_data',
                'manage_uploads',
                'validate_data',
                'edit_data'
            ])
        
        if self.is_admin():
            permissions.extend([
                'manage_settings',
                'view_audit_logs',
                'manage_validation_rules'
            ])
        
        return permissions
    
    def to_dict(self) -> dict:
        """
        Convert user to dictionary (for JSON responses)
        
        Returns:
            Dictionary representation of user (excluding sensitive data)
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'organization': self.organization,
            'position': self.position,
            'user_type': self.user_type.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'permissions': self.get_permissions()
        }
    
    @validates('username')
    def validate_username(self, key, username):
        """Validate username format"""
        if not username:
            raise ValueError("Username cannot be empty")
        
        username = username.lower().strip()
        
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if len(username) > 80:
            raise ValueError("Username cannot exceed 80 characters")
        
        # Basic username validation - alphanumeric and underscore only
        if not username.replace('_', '').isalnum():
            raise ValueError("Username can only contain letters, numbers, and underscores")
        
        return username
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format"""
        if email:
            import re
            email = email.lower().strip()
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                raise ValueError("Invalid email format")
        return email
    
    @classmethod
    def create_default_users(cls) -> List['User']:
        """
        Create default users for the system
        
        Returns:
            List of default User objects
        """
        default_users = [
            cls(
                username="isaac",
                password="isaac",
                user_type=UserType.ADMIN,
                full_name="Isaac - MOH Administrator",
                organization="Ministry of Health Uganda",
                position="Health Information System Administrator",
                email="isaac@health.go.ug"
            ),
            cls(
                username="stakeholder",
                password="stakeholder123",
                user_type=UserType.STAKEHOLDER,
                full_name="Stakeholder User",
                organization="Development Partner",
                position="Health Data Analyst",
                email="stakeholder@partner.org"
            )
        ]
        
        return default_users
    
    def __repr__(self):
        return f'<User {self.username} ({self.user_type.value})>'


class UserSession:
    """
    Helper class to manage user session information
    """
    
    def __init__(self, user: User):
        self.user = user
        self.login_time = datetime.utcnow()
        self.permissions = user.get_permissions()
    
    def has_permission(self, permission: str) -> bool:
        """Check if current session has specific permission"""
        return permission in self.permissions
    
    def to_session_dict(self) -> dict:
        """Convert to dictionary for session storage"""
        return {
            'user_id': self.user.id,
            'username': self.user.username,
            'user_type': self.user.user_type.value,
            'full_name': self.user.full_name,
            'permissions': self.permissions,
            'login_time': self.login_time.isoformat()
        }


# User management utility functions
class UserManager:
    """Utility class for common user management operations"""
    
    @staticmethod
    def authenticate_user(username: str, password: str, session) -> Optional[User]:
        """
        Authenticate user with username and password
        
        Args:
            username: Username to authenticate
            password: Password to verify
            session: Database session
            
        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            user = session.query(User).filter(
                User.username == username.lower().strip()
            ).first()
            
            if user and user.check_password(password):
                if user.is_active():
                    user.record_login()
                    return user
                else:
                    # Account is locked or inactive
                    return None
            else:
                if user:
                    user.record_failed_login()
                return None
                
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    @staticmethod
    def create_user(username: str, password: str, user_type: UserType, session, **kwargs) -> User:
        """
        Create new user
        
        Args:
            username: Unique username
            password: User password
            user_type: Type of user (admin/stakeholder)
            session: Database session
            **kwargs: Additional user fields
            
        Returns:
            Created User object
        """
        user = User(username=username, password=password, user_type=user_type, **kwargs)
        session.add(user)
        session.commit()
        return user
    
    @staticmethod
    def get_user_by_id(user_id: int, session) -> Optional[User]:
        """Get user by ID"""
        return session.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(username: str, session) -> Optional[User]:
        """Get user by username"""
        return session.query(User).filter(
            User.username == username.lower().strip()
        ).first()
