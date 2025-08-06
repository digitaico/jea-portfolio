#!/usr/bin/env python3
"""
Environment Variable Management Example
Demonstrates best practices for using python-dotenv in a FastAPI application.
"""

import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import json


def load_environment():
    """
    Load environment variables from .env file.
    This is the basic way to use python-dotenv.
    """
    print("🔧 Loading environment variables...")
    
    # Load .env file (searches for .env in current directory and parents)
    load_dotenv()
    
    # Now environment variables are available via os.getenv()
    app_name = os.getenv('APP_NAME', 'Default App Name')
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    api_port = int(os.getenv('API_PORT', '8000'))
    
    print(f"  App Name: {app_name}")
    print(f"  Debug Mode: {debug_mode}")
    print(f"  API Port: {api_port}")
    
    return {
        'app_name': app_name,
        'debug_mode': debug_mode,
        'api_port': api_port
    }


def demonstrate_env_usage():
    """
    Demonstrate various ways to use environment variables.
    """
    print("\n🎯 Environment Variable Usage Examples:")
    
    # 1. Basic usage with defaults
    database_url = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/default')
    print(f"1. Database URL: {database_url}")
    
    # 2. Type conversion
    max_file_size = int(os.getenv('MAX_FILE_SIZE', '10485760'))
    print(f"2. Max File Size: {max_file_size} bytes ({max_file_size / 1024 / 1024:.1f} MB)")
    
    # 3. Boolean conversion
    debug_enabled = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes', 'on')
    print(f"3. Debug Enabled: {debug_enabled}")
    
    # 4. List conversion (comma-separated)
    allowed_hosts = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    print(f"4. Allowed Hosts: {allowed_hosts}")
    
    # 5. JSON conversion
    try:
        config_json = os.getenv('CONFIG_JSON', '{}')
        config = json.loads(config_json)
        print(f"5. Config JSON: {config}")
    except json.JSONDecodeError:
        print("5. Config JSON: Invalid JSON format")


def check_required_variables():
    """
    Check if required environment variables are set.
    """
    print("\n🔍 Checking Required Variables:")
    
    required_vars = [
        'DB_HOST',
        'DB_PORT', 
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value is None:
            missing_vars.append(var)
            print(f"  ❌ {var}: Not set")
        else:
            # Mask sensitive values
            if 'password' in var.lower():
                display_value = '*' * len(value)
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
    
    if missing_vars:
        print(f"\n⚠️  Missing required variables: {', '.join(missing_vars)}")
        print("   Please update your .env file with the missing variables.")
        return False
    else:
        print("\n✅ All required variables are set!")
        return True


def demonstrate_env_manager():
    """
    Demonstrate the custom EnvManager class.
    """
    print("\n🚀 Using Custom EnvManager:")
    
    try:
        from env_manager import EnvManager
        
        # Initialize environment manager
        env = EnvManager()
        
        # Get typed values
        api_port = env.get_int('API_PORT', 8000)
        debug_mode = env.get_bool('DEBUG', True)
        max_size = env.get_int('MAX_FILE_SIZE', 10485760)
        
        print(f"  API Port: {api_port}")
        print(f"  Debug Mode: {debug_mode}")
        print(f"  Max File Size: {max_size} bytes")
        
        # Validate database configuration
        from env_manager import validate_database_config
        is_valid = validate_database_config(env)
        
        if is_valid:
            print("  ✅ Database configuration is valid")
        else:
            print("  ❌ Database configuration needs attention")
        
        # Print summary
        env.print_summary(include_values=False)
        
    except ImportError:
        print("  ⚠️  EnvManager not available (run this from the learn-python directory)")


def create_sample_env():
    """
    Create a sample .env file if it doesn't exist.
    """
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"\n📝 {env_file} already exists")
        return
    
    print(f"\n📝 Creating sample {env_file} file...")
    
    sample_content = """# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/image_processor
DB_HOST=localhost
DB_PORT=5432
DB_NAME=image_processor
DB_USER=postgres
DB_PASSWORD=password

# Application Configuration
APP_NAME=Image Processor API
DEBUG=True
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Storage
UPLOAD_DIR=uploads
OUTPUT_DIR=output
MAX_FILE_SIZE=10485760

# Optional: pgAdmin
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(sample_content)
        print(f"✅ Created {env_file}")
        print("📝 Please update the values according to your setup")
    except Exception as e:
        print(f"❌ Error creating {env_file}: {e}")


def main():
    """
    Main function to demonstrate environment variable management.
    """
    print("🌍 Environment Variable Management Demo")
    print("=" * 50)
    
    # 1. Load environment
    config = load_environment()
    
    # 2. Demonstrate usage
    demonstrate_env_usage()
    
    # 3. Check required variables
    check_required_variables()
    
    # 4. Demonstrate custom EnvManager
    demonstrate_env_manager()
    
    # 5. Create sample .env if needed
    create_sample_env()
    
    print("\n🎯 Key Takeaways:")
    print("1. Use python-dotenv to load .env files automatically")
    print("2. Always provide default values for optional variables")
    print("3. Convert types explicitly (int, bool, etc.)")
    print("4. Validate required variables early")
    print("5. Mask sensitive values in logs")
    print("6. Use environment-specific .env files (.env.local, .env.prod)")
    
    print("\n📚 Next Steps:")
    print("1. Update your .env file with actual database credentials")
    print("2. Test the database connection: python database.py")
    print("3. Start the API: python api.py")
    print("4. Visit: http://localhost:8000/docs")


if __name__ == "__main__":
    main() 