from flask import Flask, request, Response
import requests

app = Flask(__name__)

@app.route('/data')
def proxy_data():
    # Gửi request đến tầng backend (API server)
    backend_response = requests.get("http://localhost:5001/data")
    
    # Có thể thêm bước kiểm tra/log ở đây
    print("Forwarding request from middleware to API server...")

    return Response(
        backend_response.content,
        status=backend_response.status_code,
        content_type=backend_response.headers['Content-Type']
    )

if __name__ == '__main__':
    app.run(port=5000)