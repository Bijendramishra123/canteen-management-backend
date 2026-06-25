import requests
import json
import time

BASE_URL = "http://localhost:8000"

def create_user():
    """Create a test user for login"""
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "Test@123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    print(f"User created: {response.status_code}")
    if response.status_code == 200:
        print(f"User: {response.json()['user']['email']}")
        print(f"Password: Test@123")
    return response.json()

def create_food():
    """Create a test food item"""
    food_data = {
        "name": "Margherita Pizza",
        "price": 12.99,
        "category": "Pizza",
        "image": "https://example.com/pizza.jpg",
        "description": "Classic pizza with tomato sauce and mozzarella",
        "availability": True
    }
    response = requests.post(f"{BASE_URL}/api/foods", json=food_data)
    print(f"Food created: {response.status_code}")
    if response.status_code == 201:
        print(f"Food ID: {response.json()['id']}")
    return response.json()

def create_order():
    """Create a test order"""
    order_data = {
        "items": [
            {
                "food_id": 1,
                "quantity": 2,
                "price": 12.99,
                "name": "Margherita Pizza"
            }
        ],
        "total_amount": 25.98,
        "customer_name": "John Doe",
        "customer_phone": "+1234567890",
        "customer_email": "john@example.com",
        "special_instructions": "Extra cheese please",
        "tip_amount": 5.00,
        "number_of_people": 2
    }
    response = requests.post(f"{BASE_URL}/api/orders", json=order_data)
    print(f"Order created: {response.status_code}")
    if response.status_code == 201:
        print(f"Order ID: {response.json()['id']}")
    return response.json()

if __name__ == "__main__":
    print("=" * 50)
    print("Seeding Data into Database")
    print("=" * 50)
    
    try:
        # Check API health
        health = requests.get(f"{BASE_URL}/")
        print(f"API is running: {health.status_code}")
        print("=" * 50)
        
        # Create user
        print("Creating test user...")
        user = create_user()
        print("=" * 50)
        time.sleep(0.5)
        
        # Create food
        print("Creating test food...")
        food = create_food()
        print("=" * 50)
        time.sleep(0.5)
        
        # Create order
        print("Creating test order...")
        order = create_order()
        print("=" * 50)
        
        print("\nData seeded successfully!")
        print(f"User: test@example.com (Password: Test@123)")
        print(f"Food ID: {food.get('id', 'N/A')}")
        print(f"Order ID: {order.get('id', 'N/A')}")
        
    except requests.exceptions.ConnectionError:
        print("ERROR: API is not running!")
        print("Start API first: uvicorn app.main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"Error: {e}")
