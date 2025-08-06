#!/usr/bin/env python3
"""
Run All Stages - Learning Progression Demo
==========================================

This script demonstrates how to run all stages of the learning progression.
Each stage builds upon the previous one, showing the evolution from simple
scripts to complex real-time systems.

Usage:
    python3 run_all_stages.py [stage_number]
    
Examples:
    python3 run_all_stages.py 1    # Run Stage 1 only
    python3 run_all_stages.py 6    # Run Stage 6 only
    python3 run_all_stages.py      # Show all stages
"""

import sys
import subprocess
import os
from pathlib import Path

# Stage definitions
STAGES = {
    1: {
        "name": "Basic Python & OOP",
        "description": "Simple standalone scripts with object-oriented programming",
        "files": ["image_transformer.py", "main.py", "calculator.py"],
        "command": "python3 main.py",
        "port": None
    },
    2: {
        "name": "Advanced Image Processing",
        "description": "Enhanced functionality with multiple libraries",
        "files": ["enhanced_image_transformer.py", "pillow_example.py", "image_reading_comparison.py"],
        "command": "python3 enhanced_image_transformer.py",
        "port": None
    },
    3: {
        "name": "Web API Development",
        "description": "FastAPI application with database integration",
        "files": ["api.py", "config.py", "database.py", "env_manager.py"],
        "command": "python3 api.py",
        "port": 8000
    },
    4: {
        "name": "Advanced Features",
        "description": "Redis integration, shopping cart, and microservices",
        "files": ["shopping_cart_api.py", "redis_manager.py", "redis_demo.py"],
        "command": "python3 shopping_cart_api.py",
        "port": 8001
    },
    5: {
        "name": "Production Ready",
        "description": "Docker, monitoring, and deployment",
        "files": ["docker-compose.yml", "start_db.sh", "start_redis.sh", "init.sql"],
        "command": "docker-compose up -d",
        "port": None
    },
    6: {
        "name": "Real-Time Features",
        "description": "Server-Sent Events, WebSockets, and real-time progress tracking",
        "files": ["stage6_realtime_features.py", "stage6_client.html"],
        "command": "python3 stage6_realtime_features.py",
        "port": 8002
    }
}


def print_stage_info(stage_num: int, stage_info: dict):
    """Print information about a specific stage."""
    print(f"\n{'='*60}")
    print(f"🎯 STAGE {stage_num}: {stage_info['name']}")
    print(f"{'='*60}")
    print(f"📝 Description: {stage_info['description']}")
    print(f"📁 Key Files: {', '.join(stage_info['files'])}")
    if stage_info['port']:
        print(f"🌐 Port: {stage_info['port']}")
    print(f"🚀 Command: {stage_info['command']}")


def check_files_exist(stage_num: int, stage_info: dict) -> bool:
    """Check if all files for a stage exist."""
    missing_files = []
    for file in stage_info['files']:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️  Missing files for Stage {stage_num}: {', '.join(missing_files)}")
        return False
    
    return True


def run_stage(stage_num: int, stage_info: dict):
    """Run a specific stage."""
    print_stage_info(stage_num, stage_info)
    
    if not check_files_exist(stage_num, stage_info):
        print("❌ Cannot run stage - missing files")
        return False
    
    print(f"\n🚀 Starting Stage {stage_num}...")
    print(f"Command: {stage_info['command']}")
    
    try:
        if stage_info['port']:
            print(f"🌐 API will be available at: http://localhost:{stage_info['port']}")
            if stage_num == 6:
                print(f"📱 Client will be available at: http://localhost:{stage_info['port']}/stage6_client.html")
        
        # For now, just show the command (in real implementation, you'd run it)
        print(f"\n✅ Stage {stage_num} ready to run!")
        print(f"💡 To run this stage manually: {stage_info['command']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error running Stage {stage_num}: {e}")
        return False


def show_all_stages():
    """Show information about all stages."""
    print("🚀 Python Learning Path - All Stages")
    print("=" * 60)
    print("This project demonstrates progression from basic Python to advanced microservices.")
    print("Each stage builds upon the previous one, preserving all code for learning review.\n")
    
    for stage_num, stage_info in STAGES.items():
        print_stage_info(stage_num, stage_info)
        check_files_exist(stage_num, stage_info)
        print()


def main():
    """Main function to run stages."""
    if len(sys.argv) > 1:
        try:
            stage_num = int(sys.argv[1])
            if stage_num not in STAGES:
                print(f"❌ Invalid stage number: {stage_num}")
                print(f"Available stages: {list(STAGES.keys())}")
                return
            
            run_stage(stage_num, STAGES[stage_num])
            
        except ValueError:
            print("❌ Invalid stage number. Please provide a number between 1-6.")
            return
    else:
        show_all_stages()
        print("\n💡 Usage:")
        print("  python3 run_all_stages.py [stage_number]")
        print("  python3 run_all_stages.py 1    # Run Stage 1")
        print("  python3 run_all_stages.py 6    # Run Stage 6")
        print("\n🎯 Each stage can be run independently while preserving all previous stages!")


if __name__ == "__main__":
    main() 