"""
Password Validation Utilities
Enforces strong password requirements for security
"""

import re
from typing import Tuple, List


class PasswordValidator:
    """Validates passwords against security requirements"""
    
    MIN_LENGTH = 12
    
    @staticmethod
    def validate(password: str) -> Tuple[bool, List[str]]:
        """
        Validate password against security requirements
        
        Requirements:
        - Minimum 12 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check minimum length
        if len(password) < PasswordValidator.MIN_LENGTH:
            errors.append(f"Password must be at least {PasswordValidator.MIN_LENGTH} characters long")
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter (A-Z)")
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter (a-z)")
        
        # Check for digit
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number (0-9)")
        
        # Check for special character
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            errors.append("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
        
        # Check for common weak patterns
        weak_patterns = [
            (r'(.)\1{3,}', "Password cannot contain 4 or more repeated characters"),
            (r'(012|123|234|345|456|567|678|789|890)', "Password cannot contain sequential numbers"),
            (r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', "Password cannot contain sequential letters"),
        ]
        
        for pattern, message in weak_patterns:
            if re.search(pattern, password.lower()):
                errors.append(message)
        
        # Check for common passwords (basic check)
        common_passwords = [
            'password', 'Password1!', '123456789012', 'qwerty123456',
            'admin123456!', 'Welcome12345', 'P@ssw0rd1234'
        ]
        
        if password.lower() in [p.lower() for p in common_passwords]:
            errors.append("Password is too common, please choose a more unique password")
        
        return (len(errors) == 0, errors)
    
    @staticmethod
    def get_requirements_text() -> str:
        """Get human-readable password requirements"""
        return f"""Password Requirements:
• Minimum {PasswordValidator.MIN_LENGTH} characters
• At least one uppercase letter (A-Z)
• At least one lowercase letter (a-z)
• At least one number (0-9)
• At least one special character (!@#$%^&*()_+-=[]{{}}|;:,.<>?)
• No sequential or repeated characters"""


# Singleton validator instance
password_validator = PasswordValidator()
