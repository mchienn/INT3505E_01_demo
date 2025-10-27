from flask import Flask, jsonify, request

app = Flask(__name__)

USERS = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
]


@app.after_request
def add_version_header(response):
    response.headers["X-API-Version"] = "1.0"
    response.headers["X-Extensions-Policy"] = "ignore x-*"
    return response


def v1_user(user):
    return {"id": user["id"], "name": user["name"]}


@app.route("/api/v1/users", methods=["GET"])
def list_users():
    return jsonify({
        "version": "1.0",
        "data": [v1_user(user) for user in USERS],
    })


@app.route("/api/v1/users/<int:user_id>", methods=["GET"])
def retrieve_user(user_id):
    user = next((u for u in USERS if u["id"] == user_id), None)
    if not user:
        return jsonify({
            "error": "USER_NOT_FOUND",
            "message": f"User {user_id} not found",
        }), 404

    return jsonify({
        "version": "1.0",
        "data": v1_user(user),
    })


@app.route("/api/v1/users", methods=["POST"])
def create_user():
    payload = request.get_json(force=True)
    if not payload or "name" not in payload:
        return jsonify({
            "error": "VALIDATION_ERROR",
            "message": "Field 'name' is required",
        }), 400

    new_id = max(user["id"] for user in USERS) + 1
    new_user = {"id": new_id, "name": payload["name"]}
    USERS.append(new_user)

    return jsonify({
        "version": "1.0",
        "data": v1_user(new_user),
    }), 201

if __name__ == "__main__":
    app.run(port=5000, debug=True)