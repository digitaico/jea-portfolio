#!/usr/bin/env python3
"""
Test script for the DICOM Validator System
"""

import os
import sys
import json
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        # Test shared modules (without external dependencies)
        sys.path.append('shared')
        from shared.constants.events import STUDY_UPLOADED
        from shared.constants.dicom_tags import REQUIRED_TAGS
        print("✅ Shared constants imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import shared constants: {e}")
        return False
    
    try:
        # Test shared utils (may fail if redis not installed)
        from shared.utils.logger import setup_logger
        print("✅ Shared logger imported successfully")
    except ImportError as e:
        print(f"⚠️  Shared logger import failed (expected if redis not installed): {e}")
    
    try:
        # Test API Gateway
        sys.path.insert(0, 'api-gateway/src')
        from utils.config import Config
        print("✅ API Gateway modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import API Gateway modules: {e}")
        return False
    
    try:
        # Test Validator Service
        sys.path.insert(0, 'validator-service/src')
        from validators.dicom_validator import DICOMValidator
        print("✅ Validator Service modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Validator Service modules: {e}")
        return False
    
    try:
        # Test Descriptor Service
        sys.path.insert(0, 'descriptor-service/src')
        from extractors.metadata_extractor import MetadataExtractor
        print("✅ Descriptor Service modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Descriptor Service modules: {e}")
        return False
    
    try:
        # Test Status Service
        sys.path.insert(0, 'status-service/src')
        from utils.config import Config
        print("✅ Status Service modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Status Service modules: {e}")
        return False
    
    return True

def test_directories():
    """Test if required directories exist"""
    print("\nTesting directories...")
    
    required_dirs = [
        'api-gateway',
        'validator-service', 
        'descriptor-service',
        'status-service',
        'shared',
        'uploads',
        'archive',
        'plan'
    ]
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ Directory {dir_name} exists")
        else:
            print(f"❌ Directory {dir_name} missing")
            return False
    
    return True

def test_files():
    """Test if required files exist"""
    print("\nTesting files...")
    
    required_files = [
        'compose.yaml',
        'README.md',
        'api-gateway/requirements.txt',
        'api-gateway/Dockerfile',
        'api-gateway/src/main.py',
        'validator-service/requirements.txt',
        'validator-service/Dockerfile',
        'validator-service/src/main.py',
        'descriptor-service/requirements.txt',
        'descriptor-service/Dockerfile',
        'descriptor-service/src/main.py',
        'status-service/requirements.txt',
        'status-service/Dockerfile',
        'status-service/src/main.py',
        'shared/utils/redis_client.py',
        'shared/utils/logger.py',
        'shared/constants/events.py',
        'shared/constants/dicom_tags.py'
    ]
    
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"✅ File {file_name} exists")
        else:
            print(f"❌ File {file_name} missing")
            return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        # Add the correct path
        sys.path.insert(0, 'api-gateway/src')
        from utils.config import Config
        config = Config()
        print(f"✅ API Gateway config loaded: {config.service_name}")
    except Exception as e:
        print(f"❌ Failed to load API Gateway config: {e}")
        return False
    
    return True

def test_docker_compose():
    """Test Docker Compose configuration"""
    print("\nTesting Docker Compose...")
    
    try:
        with open('compose.yaml', 'r') as f:
            content = f.read()
            if 'api-gateway' in content and 'validator-service' in content:
                print("✅ Docker Compose configuration looks good")
                return True
            else:
                print("❌ Docker Compose configuration missing required services")
                return False
    except Exception as e:
        print(f"❌ Failed to read Docker Compose file: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing DICOM Validator System\n")
    
    tests = [
        ("Directory Structure", test_directories),
        ("Required Files", test_files),
        ("Module Imports", test_imports),
        ("Configuration", test_config),
        ("Docker Compose", test_docker_compose)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
        print("\nTo start the system:")
        print("  docker compose up -d")
        print("\nTo view logs:")
        print("  docker compose logs -f")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\nNote: Some import failures are expected if dependencies are not installed.")
        print("This is normal for a test run without installing requirements.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 