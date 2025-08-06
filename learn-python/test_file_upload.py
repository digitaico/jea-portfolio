#!/usr/bin/env python3
"""
Test script for File Upload & Image Processing API
==================================================

This script tests the file upload API functionality.
"""

import requests
import time
import os
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8003"

def test_api_health():
    """Test if the API is running."""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ API is running and accessible")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API is not running. Please start it with: python3 file_upload_api.py")
        return False

def test_file_upload():
    """Test file upload functionality."""
    # Check if test image exists
    test_image_path = Path("sources/1.jpg")
    if not test_image_path.exists():
        print("❌ Test image not found: sources/1.jpg")
        return False
    
    print("📁 Testing file upload...")
    
    try:
        # Upload file
        with open(test_image_path, 'rb') as f:
            files = {'file': ('test_image.jpg', f, 'image/jpeg')}
            response = requests.post(f"{BASE_URL}/upload", files=files)
        
        if response.status_code == 200:
            upload_result = response.json()
            print(f"✅ File uploaded successfully: {upload_result['upload_id']}")
            return upload_result['upload_id']
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def test_image_processing(upload_id):
    """Test image processing functionality."""
    if not upload_id:
        print("❌ No upload ID provided")
        return False
    
    print("🔄 Testing image processing...")
    
    try:
        # Start processing
        response = requests.post(f"{BASE_URL}/process/{upload_id}")
        
        if response.status_code == 200:
            process_result = response.json()
            print(f"✅ Processing started: {process_result['status']}")
            
            # Wait for processing to complete
            max_wait = 30  # seconds
            wait_time = 0
            
            while wait_time < max_wait:
                time.sleep(2)
                wait_time += 2
                
                # Check status
                status_response = requests.get(f"{BASE_URL}/status/{upload_id}")
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"📊 Progress: {status['progress']}% - {status['message']}")
                    
                    if status['status'] == 'completed':
                        print("✅ Processing completed successfully!")
                        print(f"🎯 Transformations: {len(status['transformations'])}")
                        for transformation in status['transformations']:
                            print(f"  - {transformation['type']}: {transformation['processing_time']}ms")
                        return True
                    elif status['status'] == 'error':
                        print(f"❌ Processing failed: {status['message']}")
                        return False
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    return False
            
            print("⏰ Processing timeout")
            return False
            
        else:
            print(f"❌ Processing failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Processing error: {e}")
        return False

def test_download(upload_id):
    """Test download functionality."""
    if not upload_id:
        print("❌ No upload ID provided")
        return False
    
    print("📥 Testing download functionality...")
    
    try:
        # Test download for each transformation type
        transformations = ["brightness", "contrast", "sepia", "grayscale", "gaussian_blur"]
        
        for transformation_type in transformations:
            response = requests.get(f"{BASE_URL}/download/{upload_id}/{transformation_type}")
            
            if response.status_code == 200:
                # Save downloaded file
                output_dir = Path("output/test_downloads")
                output_dir.mkdir(exist_ok=True)
                
                output_path = output_dir / f"{upload_id}_{transformation_type}.jpg"
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Downloaded: {transformation_type} -> {output_path}")
            else:
                print(f"❌ Download failed for {transformation_type}: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing File Upload & Image Processing API")
    print("=" * 50)
    
    # Test 1: API health
    if not test_api_health():
        return
    
    # Test 2: File upload
    upload_id = test_file_upload()
    if not upload_id:
        return
    
    # Test 3: Image processing
    if not test_image_processing(upload_id):
        return
    
    # Test 4: Download
    if not test_download(upload_id):
        return
    
    print("\n🎉 All tests completed successfully!")
    print(f"📁 Check the output/test_downloads directory for downloaded files")
    print(f"🌐 Visit http://localhost:8003 for the web interface")

if __name__ == "__main__":
    main() 