"""Test script to verify admin dashboard redirects to auth."""
import requests

def test_admin_redirect():
    """Test that /admin/ redirects to auth for web requests."""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Admin Dashboard Redirect")
    print("=" * 40)
    
    try:
        # Test /admin/ without authentication (should redirect)
        print("\n📍 Testing: /admin/ (web request)")
        response = requests.get(f"{base_url}/admin/", allow_redirects=False)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print(f"   ✅ Redirects to: {location}")
            if '/auth/login' in location:
                print(f"   ✅ Correctly redirects to auth!")
            else:
                print(f"   ❌ Unexpected redirect location")
        elif response.status_code == 401:
            print(f"   ❌ Returns 401 instead of redirect")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            
        # Test /admin/api/stats (should return 401 JSON)
        print("\n📍 Testing: /admin/api/stats (API request)")
        response = requests.get(f"{base_url}/admin/api/stats", 
                              headers={'Content-Type': 'application/json'})
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 401:
            try:
                json_response = response.json()
                print(f"   ✅ JSON Response: {json_response}")
            except:
                print(f"   ❌ Non-JSON Response")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - is the server running?")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 Expected:")
    print("   - /admin/ should redirect (302) to /auth/login")  
    print("   - /admin/api/* should return 401 JSON")

if __name__ == '__main__':
    test_admin_redirect()
