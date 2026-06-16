import jwt
import datetime
from django.conf import settings
from django.contrib.auth.models import User
from ninja.security import HttpBearer
from employees.models import Employee

JWT_SECRET = getattr(settings, 'SECRET_KEY', 'default_secret_key')
JWT_ALGORITHM = 'HS256'
TOKEN_EXPIRATION_HOURS = 24

def generate_token(user: User) -> str:
    """Generates a JWT token containing user details and expiration"""
    # Determine the employee's role
    role = 'GUEST'
    employee_id = None
    try:
        if hasattr(user, 'employee') and user.employee:
            role = user.employee.role
            employee_id = user.employee.id
    except Employee.DoesNotExist:
        pass
        
    # If user is superuser, override role to SUPER_ADMIN
    if user.is_superuser:
        role = 'SUPER_ADMIN'

    payload = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'role': role,
        'employee_id': employee_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decodes a JWT token. Returns payload dict or None if invalid/expired"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


class JWTAuth(HttpBearer):
    """
    HTTP Bearer Auth class for Django Ninja APIs.
    Authenticates requests using JWT and returns the User model instance.
    """
    def authenticate(self, request, token: str):
        payload = decode_token(token)
        if not payload:
            return None
            
        try:
            user = User.objects.get(id=payload['user_id'], is_active=True)
            # Store the decoded payload inside the request object for easy authorization checks
            request.jwt_payload = payload
            return user
        except User.DoesNotExist:
            return None
