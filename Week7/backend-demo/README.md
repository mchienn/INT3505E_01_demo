# JWT Authentication API with MongoDB Integration
```powershell
cd Week7\auth-demo

# Tạo virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt
```

```powershell
# Start tất cả services (API + MongoDB)
docker-compose up -d

# Xem logs
docker-compose logs -f

# Stop
docker-compose down
```

```powershell
# Cần MongoDB đang chạy
net start MongoDB

# Chạy backend
python run.py
```

Server sẽ chạy tại: http://localhost:5000
