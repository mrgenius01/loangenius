"""Test script to verify admin API endpoints return 401 instead of redirecting."""
import requests
import json

def test_admin_endpoints():
    """Test that admin endpoints return proper JSON errors."""
    base_url = "http://localhost:5000"
    
    # Test endpoints that should return 401 JSON response
    endpoints = [
        "/admin/api/stats",
        "/admin/api/transactions", 
        "/admin/api/system/health",
        "/auth/api/user"
    ]
    
    print("🧪 Testing Admin API Endpoints Authentication")
    print("=" * 50)
    
    for endpoint in endpoints:
        try:
            print(f"\n📍 Testing: {endpoint}")
            
            # Test without authentication
            response = requests.get(f"{base_url}{endpoint}", 
                                  headers={'Content-Type': 'application/json'})
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'Not set')}")
            
            if response.status_code == 401:
                try:
                    json_response = response.json()
                    print(f"   ✅ JSON Response: {json_response}")
                except:
                    print(f"   ❌ Non-JSON Response: {response.text[:100]}...")
            elif response.status_code == 302:
                print(f"   ❌ Redirect Response (should be 401 JSON)")
                print(f"   Location: {response.headers.get('Location', 'Not set')}")
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                print(f"   Response: {response.text[:100]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed - is the server running?")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Expected behavior: All endpoints should return 401 with JSON error")

if __name__ == '__main__':
    test_admin_endpoints()
