from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)
# Mock data v2
users_v2 = [
    {
        "id": 1,
        "name": "Alice",
        "email": "alice@example.com",  
        "status": "active",
        "created_at": "2024-01-01T10:00:00Z" 
    },
    {
        "id": 2,
        "name": "Bob",
        "email": "bob@example.com",
        "status": "inactive",
        "created_at": "2024-01-02T10:00:00Z"
    },
    {
        "id": 3,
        "name": "Charlie",
        "email": "charlie@example.com",
        "status": "active",
        "created_at": "2024-01-03T10:00:00Z"
    }
]

@app.route("/api/v2/users", methods=["GET"])
def get_users_v2():
    # V2: Support filtering and pagination
    status = request.args.get("status")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    sort = request.args.get("sort", "id")
    
    # Filter
    filtered = users_v2
    if status:
        filtered = [u for u in filtered if u["status"] == status]
    
    # Sort
    if sort == "name":
        filtered = sorted(filtered, key=lambda x: x["name"])
    elif sort == "created_at":
        filtered = sorted(filtered, key=lambda x: x["created_at"])
    
    # Paginate
    start = (page - 1) * limit
    end = start + limit
    paginated = filtered[start:end]
    
    # V2: Wrapped response with metadata
    return jsonify({
        "success": True,
        "data": paginated,
        "meta": {
            "page": page,
            "limit": limit,
            "total": len(filtered),
            "total_pages": (len(filtered) + limit - 1) // limit
        },
        "timestamp": datetime.now().isoformat()
    }), 200

# GET user by id (V2)
@app.route("/api/v2/users/<int:user_id>", methods=["GET"])
def get_user_v2(user_id):
    user = next((u for u in users_v2 if u["id"] == user_id), None)
    
    if not user:
        return jsonify({
            "success": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": f"User with id {user_id} not found"
            },
            "timestamp": datetime.now().isoformat()
        }), 404
    
    # V2: Wrapped response
    return jsonify({
        "success": True,
        "data": user,
        "timestamp": datetime.now().isoformat()
    }), 200

# POST create new user (V2)
@app.route("/api/v2/users", methods=["POST"])
def create_user_v2():
    data = request.get_json()
    
    # V2: Required field validation
    if not data or not data.get("name") or not data.get("email"):
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Name and email are required",
                "fields": {
                    "name": "Required" if not data.get("name") else None,
                    "email": "Required" if not data.get("email") else None
                }
            },
            "timestamp": datetime.now().isoformat()
        }), 400
    
    # V2: Auto-generate fields
    new_user = {
        "id": len(users_v2) + 1,
        "name": data["name"],
        "email": data["email"],
        "status": data.get("status", "active"),  # Default value
        "created_at": datetime.now().isoformat()
    }
    
    users_v2.append(new_user)
    
    # V2: Return 201 with Location header
    return jsonify({
        "success": True,
        "data": new_user,
        "message": "User created successfully",
        "timestamp": datetime.now().isoformat()
    }), 201

# PUT update user (V2)
@app.route("/api/v2/users/<int:user_id>", methods=["PUT"])
def update_user_v2(user_id):
    user = next((u for u in users_v2 if u["id"] == user_id), None)
    
    if not user:
        return jsonify({
            "success": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": f"User with id {user_id} not found"
            },
            "timestamp": datetime.now().isoformat()
        }), 404
    
    data = request.get_json()
    
    # V2: Full replacement (PUT semantic)
    user.update({
        "name": data.get("name", user["name"]),
        "email": data.get("email", user["email"]),
        "status": data.get("status", user["status"]),
        "updated_at": datetime.now().isoformat()  # New field
    })
    
    return jsonify({
        "success": True,
        "data": user,
        "message": "User updated successfully",
        "timestamp": datetime.now().isoformat()
    }), 200

# DELETE user (V2)
@app.route("/api/v2/users/<int:user_id>", methods=["DELETE"])
def delete_user_v2(user_id):
    global users_v2
    user = next((u for u in users_v2 if u["id"] == user_id), None)
    
    if not user:
        return jsonify({
            "success": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": f"User with id {user_id} not found"
            },
            "timestamp": datetime.now().isoformat()
        }), 404
    
    users_v2 = [u for u in users_v2 if u["id"] != user_id]
    
    # V2: Return 204 No Content
    return '', 204

# Root endpoint showing API version info
@app.route("/api/v2", methods=["GET"])
def api_info_v2():
    return jsonify({
        "version": "2.0.0",
        "name": "User Management API V2",
        "description": "Enhanced version with breaking changes",
        "changes": [
            "Added email, status, created_at fields",
            "Changed response structure (wrapped in data key)",
            "Added pagination and filtering",
            "Changed bio -> description in profiles",
            "Added PATCH method for partial updates",
            "Enhanced error responses",
            "Added metadata to responses"
        ],
        "endpoints": {
            "users": "/api/v2/users",
            "user_detail": "/api/v2/users/{id}",
            "user_profile": "/api/v2/user-profiles/{id}",
            "user_orders": "/api/v2/users/{id}/orders"
        }
    }), 200

if __name__ == "__main__":
    app.run(port=5001, debug=True)