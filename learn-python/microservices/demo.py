#!/usr/bin/env python3
"""
Demo script for testing the microservices architecture.
"""

import asyncio
import json
import time
from typing import Dict, Any
import httpx


class MicroservicesDemo:
    """Demo class for testing microservices."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.event_bus_url = "http://localhost:8001"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_user = None
        self.access_token = None
    
    async def test_health_checks(self):
        """Test health checks for all services."""
        print("🏥 Testing health checks...")
        
        services = [
            ("API Gateway", "http://localhost:8000/health"),
            ("Event Bus", "http://localhost:8001/health"),
            ("Image Service", "http://localhost:8002/health"),
            ("User Service", "http://localhost:8003/health"),
            ("Auth Service", "http://localhost:8004/health"),
            ("Notification Service", "http://localhost:8005/health")
        ]
        
        for service_name, url in services:
            try:
                response = await self.client.get(url)
                if response.status_code == 200:
                    print(f"✅ {service_name}: Healthy")
                else:
                    print(f"❌ {service_name}: Unhealthy ({response.status_code})")
            except Exception as e:
                print(f"❌ {service_name}: Error - {e}")
    
    async def test_user_registration(self):
        """Test user registration."""
        print("\n👤 Testing user registration...")
        
        user_data = {
            "email": "demo@example.com",
            "username": "demo_user",
            "password": "demo123",
            "full_name": "Demo User"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/auth/register",
                json=user_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test_user = data["data"]
                print(f"✅ User registered: {self.test_user['email']}")
                return True
            else:
                print(f"❌ Registration failed: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    async def test_user_login(self):
        """Test user login."""
        print("\n🔐 Testing user login...")
        
        login_data = {
            "email": "demo@example.com",
            "password": "demo123"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["data"]["access_token"]
                print(f"✅ Login successful: {data['data']['user']['email']}")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    async def test_get_current_user(self):
        """Test getting current user."""
        print("\n👤 Testing get current user...")
        
        if not self.access_token:
            print("❌ No access token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = await self.client.get(
                f"{self.base_url}/users/me",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Current user: {data['data']['email']}")
                return True
            else:
                print(f"❌ Get user failed: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Get user error: {e}")
            return False
    
    async def test_event_publishing(self):
        """Test event publishing."""
        print("\n📡 Testing event publishing...")
        
        event_data = {
            "type": "demo.event",
            "data": {
                "message": "Hello from demo!",
                "timestamp": time.time()
            },
            "user_id": "demo-user"
        }
        
        try:
            response = await self.client.post(
                f"{self.event_bus_url}/events/publish",
                json=event_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Event published: {data['data']['id']}")
                return True
            else:
                print(f"❌ Event publishing failed: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Event publishing error: {e}")
            return False
    
    async def test_get_events(self):
        """Test getting events."""
        print("\n📋 Testing get events...")
        
        try:
            response = await self.client.get(f"{self.event_bus_url}/events?limit=5")
            
            if response.status_code == 200:
                data = response.json()
                events = data["data"]["events"]
                print(f"✅ Retrieved {len(events)} events")
                return True
            else:
                print(f"❌ Get events failed: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Get events error: {e}")
            return False
    
    async def test_notifications(self):
        """Test notifications."""
        print("\n🔔 Testing notifications...")
        
        if not self.access_token:
            print("❌ No access token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = await self.client.get(
                f"{self.base_url}/notifications?user_id={self.test_user['id']}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                notifications = data["data"]["notifications"]
                print(f"✅ Retrieved {len(notifications)} notifications")
                return True
            else:
                print(f"❌ Get notifications failed: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Get notifications error: {e}")
            return False
    
    async def test_service_statistics(self):
        """Test service statistics."""
        print("\n📊 Testing service statistics...")
        
        # Test event bus stats
        try:
            response = await self.client.get(f"{self.event_bus_url}/stats")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Event Bus Stats: {data['data']['total_events']} events")
        except Exception as e:
            print(f"❌ Event bus stats error: {e}")
        
        # Test notification service stats
        try:
            response = await self.client.get("http://localhost:8005/stats")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Notification Stats: {data['data']['total_notifications']} notifications")
        except Exception as e:
            print(f"❌ Notification stats error: {e}")
    
    async def run_demo(self):
        """Run the complete demo."""
        print("🚀 Starting Microservices Demo...")
        print("=" * 50)
        
        # Test health checks
        await self.test_health_checks()
        
        # Test user registration
        if await self.test_user_registration():
            # Test user login
            if await self.test_user_login():
                # Test authenticated endpoints
                await self.test_get_current_user()
                await self.test_notifications()
        
        # Test event-driven features
        await self.test_event_publishing()
        await self.test_get_events()
        
        # Test statistics
        await self.test_service_statistics()
        
        print("\n" + "=" * 50)
        print("🎉 Demo completed!")
        print("\n📝 Next Steps:")
        print("1. Open http://localhost:8000/docs to explore the API")
        print("2. Check Redis Commander at http://localhost:8081")
        print("3. Monitor logs: docker-compose logs -f")
        print("4. Try uploading an image and processing it")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Main demo function."""
    demo = MicroservicesDemo()
    try:
        await demo.run_demo()
    finally:
        await demo.close()


if __name__ == "__main__":
    asyncio.run(main())
