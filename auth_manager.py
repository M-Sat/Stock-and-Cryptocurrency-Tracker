"""
User authentication and authorization with CSV storage.
"""

import csv
import os
import hashlib
from pathlib import Path


class AuthManager:
    """Manages user authentication and CSV-based persistence"""
    
    def __init__(self):
        self.users_file = "users.csv"
        self.current_user = None
        self.ensure_users_file()
    
    def ensure_users_file(self):
        """Ensure users.csv exists with proper headers"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['email', 'name', 'password_hash'])
    
    @staticmethod
    def hash_password(password):
        """Hash password for security"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def email_exists(self, email):
        """Check if email already exists in database"""
        with open(self.users_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['email'].strip().lower() == email.strip().lower():
                    return True
        return False
    
    def sign_up(self, name, email, password):
        """
        Register a new user
        Returns: (success: bool, message: str)
        """
        email = email.strip().lower()
        name = name.strip()
        password = password.strip()
        
        # Validation
        if not email or not name or not password:
            return False, "All fields are required"
        
        if '@' not in email:
            return False, "Invalid email format"
        
        if len(password) < 4:
            return False, "Password must be at least 4 characters"
        
        if self.email_exists(email):
            return False, "Email already in use, SIGN IN instead"
        
        # Add user to CSV
        password_hash = self.hash_password(password)
        with open(self.users_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([email, name, password_hash])
        
        self.current_user = email
        return True, "Sign up successful!"
    
    def sign_in(self, email, password):
        """
        Authenticate user
        Returns: (success: bool, message: str, user_name: str or None)
        """
        email = email.strip().lower()
        password = password.strip()
        
        if not email or not password:
            return False, "Email and password are required", None
        
        with open(self.users_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['email'].strip().lower() == email:
                    password_hash = self.hash_password(password)
                    if row['password_hash'] == password_hash:
                        self.current_user = email
                        return True, "Sign in successful!", row['name']
                    else:
                        return False, "Wrong password", None
        
        return False, "Email not in use, SIGN UP instead", None
    
    def sign_out(self):
        """Sign out current user"""
        self.current_user = None
    
    def is_signed_in(self):
        """Check if a user is currently signed in"""
        return self.current_user is not None
    
    def get_current_user(self):
        """Get currently signed-in user email"""
        return self.current_user
    
    def get_user_name(self):
        """Get currently signed-in user's name"""
        if not self.current_user:
            return None
        
        with open(self.users_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['email'].strip().lower() == self.current_user.lower():
                    return row['name']
        return None
