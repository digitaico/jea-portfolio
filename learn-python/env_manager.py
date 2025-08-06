"""
Environment variable management utility.
Demonstrates best practices for handling environment variables with python-dotenv.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv, find_dotenv
import json


class EnvManager:
    """
    Environment variable manager with dotenv support.
    Provides utilities for loading, validating, and managing environment variables.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize environment manager.
        
        Args:
            env_file: Path to .env file. If None, will search for .env files.
        """
        self.env_file = env_file or find_dotenv()
        self.loaded_vars = {}
        self._load_env()
    
    def _load_env(self):
        """Load environment variables from .env file."""
        if self.env_file and os.path.exists(self.env_file):
            load_dotenv(self.env_file)
            print(f"✅ Loaded environment from: {self.env_file}")
        else:
            print(f"⚠️  No .env file found at: {self.env_file}")
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value or default
        """
        value = os.getenv(key, default)
        self.loaded_vars[key] = value
        return value
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get environment variable as integer."""
        value = self.get(key)
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            print(f"⚠️  Warning: {key} is not a valid integer, using default: {default}")
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get environment variable as boolean."""
        value = self.get(key)
        if value is None:
            return default
        
        # Handle various boolean representations
        if isinstance(value, bool):
            return value
        
        value_lower = str(value).lower().strip()
        return value_lower in ('true', '1', 'yes', 'on', 'enabled')
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get environment variable as float."""
        value = self.get(key)
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            print(f"⚠️  Warning: {key} is not a valid float, using default: {default}")
            return default
    
    def get_json(self, key: str, default: Optional[Dict] = None) -> Optional[Dict]:
        """Get environment variable as JSON object."""
        value = self.get(key)
        if not value:
            return default
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            print(f"⚠️  Warning: {key} is not valid JSON, using default: {default}")
            return default
    
    def set(self, key: str, value: str):
        """Set environment variable (for current session only)."""
        os.environ[key] = value
        self.loaded_vars[key] = value
    
    def has(self, key: str) -> bool:
        """Check if environment variable exists."""
        return key in os.environ
    
    def required(self, key: str) -> str:
        """
        Get required environment variable.
        Raises ValueError if not found.
        
        Args:
            key: Environment variable name
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If environment variable is not set
        """
        value = self.get(key)
        if value is None:
            raise ValueError(f"Required environment variable '{key}' is not set")
        return value
    
    def validate_required(self, required_keys: list) -> bool:
        """
        Validate that all required environment variables are set.
        
        Args:
            required_keys: List of required environment variable names
            
        Returns:
            True if all required variables are set, False otherwise
        """
        missing = []
        for key in required_keys:
            if not self.has(key):
                missing.append(key)
        
        if missing:
            print(f"❌ Missing required environment variables: {', '.join(missing)}")
            return False
        
        print("✅ All required environment variables are set")
        return True
    
    def print_summary(self, include_values: bool = False):
        """
        Print summary of loaded environment variables.
        
        Args:
            include_values: Whether to include actual values (be careful with sensitive data)
        """
        print(f"\n🔧 Environment Summary (from {self.env_file}):")
        print(f"  Total variables loaded: {len(self.loaded_vars)}")
        
        if include_values:
            for key, value in sorted(self.loaded_vars.items()):
                # Mask sensitive values
                if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                    display_value = '*' * len(str(value)) if value else 'None'
                else:
                    display_value = str(value) if value else 'None'
                
                print(f"  {key}: {display_value}")
        else:
            print(f"  Variables: {', '.join(sorted(self.loaded_vars.keys()))}")


def create_env_file(env_file: str = ".env", template_file: str = "env.example"):
    """
    Create .env file from template.
    
    Args:
        env_file: Path to create .env file
        template_file: Path to template file
    """
    if os.path.exists(env_file):
        print(f"⚠️  {env_file} already exists")
        return
    
    if not os.path.exists(template_file):
        print(f"❌ Template file {template_file} not found")
        return
    
    try:
        with open(template_file, 'r') as template:
            content = template.read()
        
        with open(env_file, 'w') as env:
            env.write(content)
        
        print(f"✅ Created {env_file} from {template_file}")
        print(f"📝 Please update {env_file} with your actual values")
        
    except Exception as e:
        print(f"❌ Error creating {env_file}: {e}")


def validate_database_config(env_manager: EnvManager) -> bool:
    """
    Validate database configuration.
    
    Args:
        env_manager: Environment manager instance
        
    Returns:
        True if database config is valid
    """
    required_db_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    
    print("\n🔍 Validating database configuration...")
    
    # Check if DATABASE_URL is set directly
    if env_manager.has('DATABASE_URL'):
        print("✅ DATABASE_URL is set")
        return True
    
    # Check individual database variables
    if env_manager.validate_required(required_db_vars):
        # Validate port is a number
        try:
            port = env_manager.get_int('DB_PORT')
            if port <= 0 or port > 65535:
                print("❌ DB_PORT must be between 1 and 65535")
                return False
        except ValueError:
            print("❌ DB_PORT must be a valid integer")
            return False
        
        print("✅ Database configuration is valid")
        return True
    
    return False


# Example usage and testing
if __name__ == "__main__":
    print("🚀 Environment Manager Demo")
    
    # Initialize environment manager
    env_manager = EnvManager()
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        create_env_file()
    
    # Validate database configuration
    validate_database_config(env_manager)
    
    # Print summary
    env_manager.print_summary(include_values=False)
    
    # Example of getting different types
    print(f"\n📊 Example values:")
    print(f"  API Port: {env_manager.get_int('API_PORT', 8000)}")
    print(f"  Debug Mode: {env_manager.get_bool('DEBUG', True)}")
    print(f"  Max File Size: {env_manager.get_int('MAX_FILE_SIZE', 10485760)} bytes") 