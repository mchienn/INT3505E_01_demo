from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

USERS_V2 = [
    {
        "id": 1,
        "name": "Alice",
        "contact": {"email": "alice@example.com"},
        "status": {"state": "active", "joined_at": "2024-01-01T10:00:00Z"},
    },
    {
        "id": 2,
        "name": "Bob",
        "contact": {"email": "bob@example.com"},
        "status": {"state": "inactive", "joined_at": "2024-02-15T14:30:00Z"},
    },
]

STABLE_FIELDS = ("id", "name")
OPTIONAL_COMPONENTS = {"contact", "status"}


def parse_include(raw_include):
    if not raw_include:
        return set()
    requested = {item.strip() for item in raw_include.split(",") if item.strip()}
    return requested & OPTIONAL_COMPONENTS


def shape_user(user, includes):
    payload = {field: user[field] for field in STABLE_FIELDS}
    extensions = {}
    for component in includes:
        extensions[component] = user.get(component, {})

    if extensions:
        payload["x_extensions"] = extensions
    return payload


@app.after_request
def add_version_header(response):
    response.headers["X-API-Version"] = "2.0"
    response.headers["X-Extensions-Available"] = ",".join(sorted(OPTIONAL_COMPONENTS))
    return response


@app.route("/api/v2/users", methods=["GET"])
def list_users_v2():
    includes = parse_include(request.args.get("include"))
    legacy_mode = request.args.get("legacy") == "true"

    if legacy_mode:
        includes = set()

    data = [shape_user(user, includes) for user in USERS_V2]
    response = {
        "version": "2.0",
        "mode": "legacy" if legacy_mode else "extended",
        "data": data,
        "extensions": {
            "always": list(STABLE_FIELDS),
            "available": sorted(OPTIONAL_COMPONENTS),
            "active": sorted(includes),
        },
    }
    return jsonify(response)


@app.route("/api/v2/users/<int:user_id>", methods=["GET"])
def retrieve_user_v2(user_id):
    includes = parse_include(request.args.get("include"))
    legacy_mode = request.args.get("legacy") == "true"
    user = next((item for item in USERS_V2 if item["id"] == user_id), None)

    if not user:
        return jsonify({
            "version": "2.0",
            "error": {
                "code": "USER_NOT_FOUND",
                "message": f"User {user_id} not found",
            },
        }), 404

    if legacy_mode:
        includes = set()

    return jsonify({
        "version": "2.0",
        "mode": "legacy" if legacy_mode else "extended",
        "data": shape_user(user, includes),
        "extensions": {
            "always": list(STABLE_FIELDS),
            "available": sorted(OPTIONAL_COMPONENTS),
            "active": sorted(includes),
        },
    })


@app.route("/api/v2/users", methods=["POST"])
def create_user_v2():
    payload = request.get_json(force=True)

    if not payload or "name" not in payload:
        return jsonify({
            "version": "2.0",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Field 'name' is required",
            },
        }), 400

    new_user = {
        "id": max(user["id"] for user in USERS_V2) + 1,
        "name": payload["name"],
        "contact": payload.get("contact", {}),
        "status": payload.get("status", {"state": "active", "joined_at": datetime.utcnow().isoformat() + "Z"}),
    }
    USERS_V2.append(new_user)

    includes = parse_include(request.args.get("include"))
    return jsonify({
        "version": "2.0",
        "data": shape_user(new_user, includes),
        "extensions": {
            "always": list(STABLE_FIELDS),
            "available": sorted(OPTIONAL_COMPONENTS),
            "active": sorted(includes),
        },
    }), 201

if __name__ == "__main__":
    app.run(port=5001, debug=True)