from flask import Flask, jsonify, request

app = Flask(__name__)

# Không dùng plural, không RESTful
@app.route("/getAllUsersDataList", methods=["GET"])
def get_all_users():
    return jsonify([{"uid": "U001", "uname": "Alice"}])

# Sai HTTP method (POST thay vì GET)
@app.route("/getUserInfo", methods=["POST"])
def get_user_info():
    data = request.get_json()
    return jsonify({"uid": data.get("uid"), "uname": "Alice"})

# Có verb trong URL (sai chuẩn REST)
@app.route("/deleteUserById/<int:id>", methods=["GET"])
def delete_user(id):
    return jsonify({"message": f"Deleted user {id}"})

# Không dùng plural và không có path param
@app.route("/userUpdate", methods=["PUT"])
def user_update():
    return jsonify({"message": "Updated"})

if __name__ == "__main__":
    app.run(port=4000, debug=True)