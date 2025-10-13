import requests
import json

BASE_URL = "http://localhost:5000"

def fetch_students():
    """Fetch all students from API"""
    try:
        response = requests.get(f"{BASE_URL}/api/students")
        data = response.json()
        print("Students:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as error:
        print(f"Error fetching students: {error}")

def fetch_student(student_id):
    """Fetch specific student by ID"""
    try:
        response = requests.get(f"{BASE_URL}/api/students/{student_id}")
        data = response.json()
        print(f"\nStudent {student_id}:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as error:
        print(f"Error fetching student {student_id}: {error}")

def fetch_users():
    """Fetch all users from API"""
    try:
        response = requests.get(f"{BASE_URL}/api/users")
        data = response.json()
        print("\nUsers:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as error:
        print(f"Error fetching users: {error}")

def fetch_user(user_id):
    """Fetch specific user by ID"""
    try:
        response = requests.get(f"{BASE_URL}/api/users/{user_id}")
        data = response.json()
        print(f"\nUser {user_id}:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as error:
        print(f"Error fetching user {user_id}: {error}")

def run_demo():
    """Run the client demo"""
    print("=== REST Client-Server Demo ===\n")
    
    fetch_students()
    fetch_student(1)
    fetch_users()
    fetch_user(2)

if __name__ == "__main__":
    run_demo()
