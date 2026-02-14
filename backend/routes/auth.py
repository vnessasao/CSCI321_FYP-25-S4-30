"""
Authentication routes for the Traffic Analysis system.
Handles user registration and login with JWT authentication.
"""

from flask import Blueprint, request, jsonify
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import re
import sys
import os

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.jwt_handler import generate_jwt_token, validate_jwt_token
from utils.permission_handler import get_user_permissions
from database_config import get_db_connection

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize password hasher
ph = PasswordHasher()

# Valid roles (must match database constraint)
VALID_ROLES = ['public', 'government', 'developer', 'analyst']

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength."""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, None

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Register a new user.
    Expected JSON: {'email': str, 'password': str, 'role': str}
    """
    try:
        # Check Content-Type header
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', '').lower()

        # Validate inputs
        if not email or not password or not role:
            return jsonify({'error': 'Email, password, and role are required'}), 400

        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400

        is_valid_password, password_error = validate_password(password)
        if not is_valid_password:
            return jsonify({'error': password_error}), 400

        if role not in VALID_ROLES:
            return jsonify({'error': f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}'}), 400

        # Check if user already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Email already registered'}), 400

        # Hash password
        password_hash = ph.hash(password)

        # Insert new user
        cursor.execute("""
            INSERT INTO users (email, password_hash, role, is_active) 
            VALUES (%s, %s, %s, %s) 
            RETURNING id
        """, (email, password_hash, role, True))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()

        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id
        }), 201

    except Exception as e:
        print(f"Signup error: {str(e)}")  # Debug logging
        import traceback
        traceback.print_exc()  # Full stack trace
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user login.
    Expected JSON: {'email': str, 'password': str, 'role': str}
    """
    try:
        # Check Content-Type header
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', '').lower()

        # Validate inputs
        if not email or not password or not role:
            return jsonify({'error': 'Email, password, and role are required'}), 400

        # Fetch user from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, password_hash, role, is_active 
            FROM users WHERE email = %s
        """, (email,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401

        user_id, db_email, password_hash, db_role, is_active = user

        # Check if user is active
        if not is_active:
            return jsonify({'error': 'Account is deactivated'}), 401

        # Verify role matches
        if db_role != role:
            return jsonify({'error': 'Invalid role for this account'}), 401

        # Verify password
        try:
            ph.verify(password_hash, password)
        except VerifyMismatchError:
            return jsonify({'error': 'Invalid email or password'}), 401

        # Generate JWT token using jwt_handler
        token = generate_jwt_token(user_id, db_email, db_role)

        # Get user permissions
        permissions = get_user_permissions(db_role)

        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user_id,
                'email': db_email,
                'role': db_role
            },
            'permissions': permissions
        }), 200

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """
    Verify JWT token validity.
    Expected JSON: {'token': str}
    """
    try:
        # Check Content-Type header
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({'error': 'Token is required'}), 400

        token = data['token']
        
        # Use jwt_handler to validate token
        success, response_data, status_code = validate_jwt_token(token)
        return jsonify(response_data), status_code

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500
