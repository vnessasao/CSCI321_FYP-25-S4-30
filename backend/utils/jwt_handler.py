"""
JWT Handler utility for Traffic Analysis system.
Handles JWT token generation, verification, and validation.
"""

import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

class JWTHandler:
    """Handles JWT token operations with consistent configuration."""
    
    def __init__(self):
        # JWT secret key (should be in environment variables)
        self.secret_key = os.getenv('JWT_SECRET', 'your-secret-key-change-this-in-production')
        self.algorithm = 'HS256'
        self.token_expiry_hours = 24
    
    def generate_token(self, user_id, email, role):
        """
        Generate JWT token for authenticated user.
        
        Args:
            user_id (int): User's database ID
            email (str): User's email address
            role (str): User's role (public, government, developer, analyst)
        
        Returns:
            str: Encoded JWT token
        """
        payload = {
            'user_id': user_id,
            'email': email,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token):
        """
        Verify and decode JWT token.
        
        Args:
            token (str): JWT token to verify
        
        Returns:
            dict: Decoded payload if valid
            
        Raises:
            jwt.ExpiredSignatureError: If token has expired
            jwt.InvalidTokenError: If token is invalid
        """
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
    
    def extract_token_from_request(self, request):
        """
        Extract JWT token from Flask request headers.
        
        Args:
            request: Flask request object
        
        Returns:
            str or None: Token if found, None otherwise
        """
        # Check Authorization header (Bearer token)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        
        # Check for token in request JSON (fallback)
        if request.is_json:
            data = request.get_json()
            if data and 'token' in data:
                return data['token']
        
        return None
    
    def validate_token_response(self, token):
        """
        Validate token and return standardized response.
        
        Args:
            token (str): JWT token to validate
        
        Returns:
            tuple: (success_bool, response_dict, status_code)
        """
        try:
            payload = self.verify_token(token)
            return True, {
                'valid': True,
                'user': {
                    'id': payload['user_id'],
                    'email': payload['email'],
                    'role': payload['role']
                }
            }, 200
        
        except jwt.ExpiredSignatureError:
            return False, {'error': 'Token has expired'}, 401
        except jwt.InvalidTokenError:
            return False, {'error': 'Invalid token'}, 401
        except Exception:
            return False, {'error': 'Token validation failed'}, 500

# Create singleton instance
jwt_handler = JWTHandler()

def token_required(allowed_roles=None):
    """
    Decorator to require valid JWT token for route access.
    
    Args:
        allowed_roles (list, optional): List of roles allowed to access the route
    
    Returns:
        decorator: Function decorator that validates JWT and role access
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = jwt_handler.extract_token_from_request(request)
            
            if not token:
                return jsonify({'error': 'Token is missing'}), 401
            
            try:
                payload = jwt_handler.verify_token(token)
                current_user = {
                    'id': payload['user_id'],
                    'email': payload['email'],
                    'role': payload['role']
                }
                
                # Check role permissions if specified
                if allowed_roles and current_user['role'] not in allowed_roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Add current_user to kwargs for use in route function
                kwargs['current_user'] = current_user
                
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401
            except Exception:
                return jsonify({'error': 'Token validation failed'}), 500
            
            return f(*args, **kwargs)
        return decorated
    return decorator

# Convenience functions for direct usage
def generate_jwt_token(user_id, email, role):
    """Generate JWT token - convenience wrapper."""
    return jwt_handler.generate_token(user_id, email, role)

def verify_jwt_token(token):
    """Verify JWT token - convenience wrapper."""
    return jwt_handler.verify_token(token)

def validate_jwt_token(token):
    """Validate JWT token with response - convenience wrapper."""
    return jwt_handler.validate_token_response(token)
