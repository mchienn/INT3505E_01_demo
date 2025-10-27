from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/data')
def get_data():
    return jsonify({
        "source": "API server",
        "data": [1, 2, 3, 4]
    })

if __name__ == '__main__':
    app.run(port=5001)