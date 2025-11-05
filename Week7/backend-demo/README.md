# JWT Authentication API with MongoDB Integration

Backend API được sinh từ OpenAPI specification và tích hợp với MongoDB.

## 🚀 Features

- ✅ **OpenAPI-based Development** - Backend generated from OpenAPI spec
- ✅ **JWT Authentication** - Access & Refresh Tokens with rotation
- ✅ **MongoDB Integration** - Full database connectivity with Pymongo
- ✅ **Product CRUD Operations** - Complete Create, Read, Update, Delete
- ✅ **Pydantic Validation** - Request/response data validation
- ✅ **Role-based Authorization** - Admin and user roles
- ✅ **Swagger UI Documentation** - Interactive API testing
- ✅ **Modular Architecture** - Clean separation of concerns
- ✅ **Docker Support** - Easy deployment with docker-compose

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP/JSON
       ▼
┌─────────────────────────────────┐
│      Flask Application          │
│  ┌──────────────────────────┐  │
│  │    Routes (Blueprints)   │  │
│  │  • auth.py               │  │
│  │  • products.py           │  │
│  └────────┬─────────────────┘  │
│           │                     │
│  ┌────────▼─────────────────┐  │
│  │    Business Logic        │  │
│  │  • JWT Authentication    │  │
│  │  • CRUD Operations       │  │
│  └────────┬─────────────────┘  │
│           │                     │
│  ┌────────▼─────────────────┐  │
│  │   Models (Pydantic)      │  │
│  │  • Data Validation       │  │
│  └────────┬─────────────────┘  │
│           │                     │
│  ┌────────▼─────────────────┐  │
│  │  Database Layer          │  │
│  │  • Connection Pool       │  │
│  │  • Indexes               │  │
│  └────────┬─────────────────┘  │
└───────────┼─────────────────────┘
            │
            ▼
    ┌───────────────┐
    │    MongoDB    │
    │  • users      │
    │  • products   │
    │  • tokens     │
    └───────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- MongoDB (local hoặc MongoDB Atlas)

## 🛠️ Setup Instructions

### 1. Cài đặt MongoDB

#### Cách 1: MongoDB Local (Windows)

```powershell
# Download MongoDB Community Server từ:
# https://www.mongodb.com/try/download/community

# Hoặc dùng chocolatey:
choco install mongodb

# Start MongoDB service
net start MongoDB
```

#### Cách 2: MongoDB Atlas (Cloud - Free)

1. Tạo account tại https://www.mongodb.com/cloud/atlas
2. Tạo free cluster
3. Lấy connection string

### 2. Clone và Setup Project

```powershell
cd Week7\auth-demo

# Tạo virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Cấu hình Environment

```powershell
# Copy file .env.example thành .env
Copy-Item .env.example .env

# Sửa .env với thông tin MongoDB của bạn
```

File `.env`:

```env
# JWT Configuration
SECRET_KEY=your-secret-key-change-in-production
REFRESH_SECRET_KEY=your-refresh-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# MongoDB Configuration (Local)
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=product_api

# MongoDB Configuration (Atlas)
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
# MONGODB_DATABASE=product_api

# Server Configuration
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000
```

### 4. Chạy Server

#### Option A: Docker (Recommended - Dễ nhất!)

```powershell
# Start tất cả services (API + MongoDB)
docker-compose up -d

# Xem logs
docker-compose logs -f

# Stop
docker-compose down
```

#### Option B: Local Python

```powershell
# Cần MongoDB đang chạy
net start MongoDB

# Chạy backend
python run.py
```

Server sẽ chạy tại: http://localhost:5000

## 📚 API Documentation

### Swagger UI

Truy cập: http://localhost:5000/docs

### Endpoints

#### Authentication

- `POST /auth/register` - Đăng ký user mới
- `POST /auth/login` - Đăng nhập
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Đăng xuất
- `GET /auth/me` - Lấy thông tin user hiện tại
- `POST /auth/change-password` - Đổi mật khẩu

#### Products

- `GET /api/products` - Lấy danh sách products (có filters)
- `GET /api/products/{id}` - Lấy product theo ID
- `POST /api/products` - Tạo product mới (cần auth)
- `PUT /api/products/{id}` - Cập nhật product (owner/admin)
- `DELETE /api/products/{id}` - Xóa product (owner/admin)

#### Other

- `GET /` - API info
- `GET /health` - Health check
- `GET /openapi.yaml` - OpenAPI spec

## 🧪 Testing với PowerShell

### 1. Register User

```powershell
$body = @{
    username = "testuser"
    password = "Test123456"
    email = "test@example.com"
    full_name = "Test User"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/auth/register" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### 2. Login

```powershell
$body = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5000/auth/login" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$token = $response.access_token
echo "Access Token: $token"
```

### 3. Get Products

```powershell
# Public endpoint - không cần token
Invoke-RestMethod -Uri "http://localhost:5000/api/products"

# Với filters
Invoke-RestMethod -Uri "http://localhost:5000/api/products?category=Electronics&min_price=500"
```

### 4. Create Product (cần auth)

```powershell
$headers = @{
    "Authorization" = "Bearer $token"
}

$body = @{
    name = "MacBook Pro"
    description = "Apple MacBook Pro 16-inch"
    price = 2499.99
    category = "Electronics"
    stock = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/products" `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $body
```

### 5. Health Check

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/health"
```

## 📁 Project Structure

```
Week7/auth-demo/
├── app/                       # Application package
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Configuration
│   ├── routes/               # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication routes
│   │   └── products.py       # Product CRUD routes
│   ├── models/               # Data models
│   │   ├── __init__.py
│   │   └── schemas.py        # Pydantic schemas
│   ├── database/             # Database layer
│   │   ├── __init__.py
│   │   └── connection.py     # MongoDB connection
│   └── utils/                # Utilities
│       ├── __init__.py
│       └── auth.py           # JWT helpers
├── run.py                    # Application entry point
├── openapi.yaml              # OpenAPI 3.0 specification
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── docker-compose.yml        # Docker orchestration
├── Dockerfile               # Container image
└── README.md                # This file
```

## 🗄️ MongoDB Collections

### users

```javascript
{
  _id: ObjectId,
  username: String (unique),
  password: String (hashed),
  email: String (unique),
  full_name: String,
  role: String ("admin" | "user"),
  is_active: Boolean,
  created_at: DateTime
}
```

### products

```javascript
{
  _id: ObjectId,
  name: String,
  description: String,
  price: Number,
  category: String,
  stock: Number,
  created_by: String (user_id),
  created_at: DateTime,
  updated_at: DateTime
}
```

### refresh_tokens

```javascript
{
  _id: ObjectId,
  jti: String (unique),
  user_id: String,
  created_at: DateTime,
  expires_at: DateTime,
  last_used: DateTime
}
```

## 🔐 Default Test Accounts

```
Admin:
  username: admin
  password: admin123

User:
  username: user1
  password: user123
```

## 🎯 MongoDB Query Examples

```powershell
# Kết nối MongoDB
mongosh

# Switch database
use product_api

# Xem collections
show collections

# Xem users
db.users.find().pretty()

# Xem products
db.products.find().pretty()

# Tìm products theo category
db.products.find({ category: "Electronics" })

# Tìm products theo price range
db.products.find({ price: { $gte: 500, $lte: 1500 } })

# Count documents
db.products.countDocuments()
db.users.countDocuments()
```

## 🚀 Swagger Codegen - Generate Client Code

Sử dụng OpenAPI Generator để generate client libraries từ OpenAPI spec:

```powershell
# Install OpenAPI Generator
npm install -g @openapitools/openapi-generator-cli

# Generate TypeScript client
npx @openapitools/openapi-generator-cli generate `
    -i openapi.yaml `
    -g typescript-fetch `
    -o ./generated/typescript-client

# Generate Python client
npx @openapitools/openapi-generator-cli generate `
    -i openapi.yaml `
    -g python `
    -o ./generated/python-client `
    --additional-properties packageName=product_api_client

# Generate Java client
npx @openapitools/openapi-generator-cli generate `
    -i openapi.yaml `
    -g java `
    -o ./generated/java-client
```

## 📝 Notes

- Access tokens expire sau 60 phút (configurable)
- Refresh tokens expire sau 7 ngày (configurable)
- Token rotation: mỗi lần refresh, cả access và refresh token đều được tạo mới
- MongoDB indexes được tạo tự động cho performance
- Sample data được seed tự động khi database trống

## 🐛 Troubleshooting

### MongoDB Connection Error

```
Error: Failed to connect to MongoDB
```

**Solution:**

- Kiểm tra MongoDB service đang chạy: `net start MongoDB`
- Kiểm tra MONGODB_URI trong .env file
- Với Atlas: check IP whitelist và credentials

### Import Error

```
ModuleNotFoundError: No module named 'pymongo'
```

**Solution:**

```powershell
pip install -r requirements.txt
```

### Port Already in Use

```
OSError: [WinError 10048] Only one usage of each socket address
```

**Solution:**

```powershell
# Tìm process đang dùng port 5000
netstat -ano | findstr :5000

# Kill process
taskkill /PID <process_id> /F

# Hoặc đổi port trong .env
PORT=5001
```

## 📞 Support

Nếu gặp vấn đề, check:

1. MongoDB đang chạy
2. Dependencies đã install đầy đủ
3. .env file được cấu hình đúng
4. Virtual environment đã activate

---

Made with ❤️ using Flask + MongoDB + OpenAPI
