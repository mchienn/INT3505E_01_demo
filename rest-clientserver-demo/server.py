
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Sample data
students = [
    {"id": 1, "name": "Nguyen Van A", "age": 20},
    {"id": 2, "name": "Tran Thi B", "age": 21},
    {"id": 3, "name": "Le Van C", "age": 22}
]

users = [
    {"id": 1, "username": "admin", "role": "admin"},
    {"id": 2, "username": "user1", "role": "user"},
    {"id": 3, "username": "user2", "role": "user"}
]

@app.route('/api/students', methods=['GET'])
def get_students():
    """Get all students"""
    return jsonify(students)

@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    """Get specific student by ID"""
    student = next((s for s in students if s['id'] == student_id), None)
    if student:
        return jsonify(student)
    return jsonify({"error": "Student not found"}), 404

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    return jsonify(users)

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user by ID"""
    user = next((u for u in users if u['id'] == user_id), None)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404

if __name__ == '__main__':
    print("🚀 REST API Server is running on http://localhost:5000")
    print("📚 Endpoints:")
    print("  - GET /api/students")
    print("  - GET /api/students/<id>")
    print("  - GET /api/users")
    print("  - GET /api/users/<id>")
    app.run(debug=True, port=5000)
