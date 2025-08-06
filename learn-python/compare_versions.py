#!/usr/bin/env python3
"""
Version Comparison Script
=========================

This script shows the differences between the different versions
of the main script to demonstrate the learning progression.

Versions:
- v1: Basic image transformations (Stage 1) - standalone, no database
- v2: Database integration (Stage 3+) - stores transformation history
- v3: Advanced features (Stage 4+) - batch processing, enhanced error handling
"""

import os
from pathlib import Path

def print_version_info():
    """Print information about all versions."""
    print("🚀 Main Script Versions - Learning Progression")
    print("=" * 60)
    
    versions = [
        {
            "version": "v1",
            "file": "main.py",
            "stage": "Stage 1",
            "description": "Basic Python & OOP",
            "features": [
                "✅ Image transformations",
                "✅ File system operations",
                "✅ Command-line interface",
                "❌ No database storage",
                "❌ No progress tracking",
                "❌ No error handling"
            ],
            "usage": "python3 main.py [image_path]"
        },
        {
            "version": "v2",
            "file": "main_v2.py",
            "stage": "Stage 3+",
            "description": "Database Integration",
            "features": [
                "✅ All v1 features",
                "✅ Database storage",
                "✅ Transformation history",
                "✅ Progress tracking",
                "✅ Error handling",
                "❌ No batch processing",
                "❌ No configuration management"
            ],
            "usage": "python3 main_v2.py [image_path]"
        },
        {
            "version": "v3",
            "file": "main_v3.py",
            "stage": "Stage 4+",
            "description": "Advanced Features",
            "features": [
                "✅ All v2 features",
                "✅ Batch processing",
                "✅ Configuration management",
                "✅ Enhanced error handling",
                "✅ Performance monitoring",
                "✅ Detailed logging",
                "✅ Command-line arguments"
            ],
            "usage": "python3 main_v3.py [image_path] [--batch] [--config config.json]"
        }
    ]
    
    for version_info in versions:
        print(f"\n{'='*60}")
        print(f"🎯 {version_info['version'].upper()}: {version_info['description']}")
        print(f"{'='*60}")
        print(f"📁 File: {version_info['file']}")
        print(f"🎓 Stage: {version_info['stage']}")
        print(f"📝 Description: {version_info['description']}")
        print(f"🚀 Usage: {version_info['usage']}")
        
        # Check if file exists
        if os.path.exists(version_info['file']):
            print(f"✅ File exists")
        else:
            print(f"❌ File not found")
        
        print(f"\n📋 Features:")
        for feature in version_info['features']:
            print(f"  {feature}")
    
    print(f"\n{'='*60}")
    print("💡 Learning Progression:")
    print("  v1 → v2: Added database integration")
    print("  v2 → v3: Added advanced features and batch processing")
    print("  Each version builds upon the previous while preserving functionality")
    print(f"{'='*60}")


def show_file_differences():
    """Show key differences between versions."""
    print(f"\n🔍 Key Differences Between Versions:")
    print(f"{'='*60}")
    
    differences = [
        {
            "aspect": "Database Integration",
            "v1": "❌ No database",
            "v2": "✅ PostgreSQL with SQLAlchemy",
            "v3": "✅ Enhanced database with error handling"
        },
        {
            "aspect": "Error Handling",
            "v1": "❌ Basic try/catch",
            "v2": "✅ Database error handling",
            "v3": "✅ Comprehensive error handling with logging"
        },
        {
            "aspect": "Configuration",
            "v1": "❌ Hardcoded values",
            "v2": "✅ Environment variables",
            "v3": "✅ JSON config files + environment variables"
        },
        {
            "aspect": "Progress Tracking",
            "v1": "❌ No progress tracking",
            "v2": "✅ Basic progress with database",
            "v3": "✅ Detailed progress with timing and statistics"
        },
        {
            "aspect": "Batch Processing",
            "v1": "❌ Single image only",
            "v2": "❌ Single image only",
            "v3": "✅ Batch processing capabilities"
        },
        {
            "aspect": "Command Line",
            "v1": "✅ Basic arguments",
            "v2": "✅ Basic arguments",
            "v3": "✅ Advanced arguments with argparse"
        }
    ]
    
    print(f"{'Aspect':<20} {'v1':<15} {'v2':<15} {'v3':<15}")
    print(f"{'-'*20} {'-'*15} {'-'*15} {'-'*15}")
    
    for diff in differences:
        print(f"{diff['aspect']:<20} {diff['v1']:<15} {diff['v2']:<15} {diff['v3']:<15}")


def main():
    """Main function to show version comparison."""
    print_version_info()
    show_file_differences()
    
    print(f"\n🎯 Recommendation:")
    print(f"  - Start with v1 to understand basic concepts")
    print(f"  - Move to v2 to learn database integration")
    print(f"  - Use v3 for production-ready features")
    print(f"\n💡 Each version is preserved independently for learning review!")


if __name__ == "__main__":
    main() 