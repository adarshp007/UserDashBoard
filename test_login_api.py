import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000/account/api"

def test_login_api():
    """Test the login API endpoint."""

    # Login credentials
    data = {
        "email": "adarsh@beinex.com",  # Replace with your superuser email
        "password": "Admin@123"  # Replace with your superuser password
    }

    # Send the login request
    response = requests.post(f"{BASE_URL}/login/", json=data)
    print("Login Response Status:", response.status_code)

    if response.status_code == 200:
        result = response.json()

        # Print user details
        print("\nUser Details:")
        print(f"Email: {result['user']['email']}")
        print(f"Name: {result['user']['first_name']} {result['user']['last_name']}")
        print(f"Status: {result['user']['status']}")

        # Print token information
        print("\nToken Information:")
        print(f"Access Token: {result['access'][:30]}...")
        print(f"Refresh Token: {result['refresh'][:30]}...")

        # Test user details endpoint with the token
        headers = {
            "Authorization": f"Bearer {result['access']}"
        }

        user_response = requests.get(f"{BASE_URL}/user/", headers=headers)
        print("\nUser Details API Response Status:", user_response.status_code)

        if user_response.status_code == 200:
            user_result = user_response.json()
            print("User Details from API:")
            print(json.dumps(user_result, indent=2))
        else:
            print("Error Response:", user_response.json())
    else:
        print("Error Response:", response.json())

if __name__ == "__main__":
    print("Testing login API...")
    test_login_api()
