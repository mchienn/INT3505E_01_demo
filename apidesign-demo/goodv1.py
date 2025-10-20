from flask import Flask, jsonify, request

app = Flask(__name__)

# GET all users
@app.route("/users", methods=["GET"])
def get_users():
    return jsonify([
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ])

# plural noun, lowercase, dùng hyphen thay vì underscore
@app.route("/api/v1/user-profiles/<int:user_id>", methods=["GET"])
def get_user_profile(user_id):
    return jsonify({"id": user_id, "bio": "Loves REST design"})

# clarity: tên endpoint mô tả rõ chức năng
@app.route("/api/v1/users/<int:user_id>/orders", methods=["GET"])
def get_user_orders(user_id):
    return jsonify({
        "user_id": user_id,
        "orders": [{"id": 10, "item": "Laptop"}, {"id": 11, "item": "Mouse"}]
    })
# GET user by id
@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return jsonify({"id": user_id, "name": "Alice"})

# POST create new user
@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    return jsonify({"message": "User created", "data": data}), 201

# PUT update user
@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()
    return jsonify({"message": f"User {user_id} updated", "data": data})

# DELETE user
@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    return jsonify({"message": f"User {user_id} deleted"})

if __name__ == "__main__":
    app.run(port=5000, debug=True)