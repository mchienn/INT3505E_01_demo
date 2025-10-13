import requests

response = requests.get("http://localhost:5000/data")
print(response.json())