# Payment API - Chiến lược nâng cấp từ v1 → v2

## Mô tả

Demo này minh họa chiến lược nâng cấp API từ version 1 sang version 2, áp dụng các best practices trong API versioning.

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy ứng dụng

```bash
python app.py
```

Server sẽ chạy tại `http://localhost:5000`

## API Endpoints

### V1 API (Legacy)

#### 1. Tạo Payment
```http
POST /api/v1/payments
Content-Type: application/json

{
  "amount": 100.00,
  "currency": "USD",
  "source": "card_123456"
}
```

**Response:**
```json
{
  "id": "uuid-here",
  "amount": 100.00,
  "currency": "USD",
  "source": "card_123456",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00",
  "version": "v1"
}
```

#### 2. Lấy Payment
```http
GET /api/v1/payments/{payment_id}
```

**Response:**
```json
{
  "id": "uuid-here",
  "amount": 100.00,
  "currency": "USD",
  "source": "card_123456",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00"
}
```

### V2 API (Enhanced)

#### 1. Tạo Payment (Enhanced)
```http
POST /api/v2/payments
Content-Type: application/json

{
  "amount": 100.00,
  "currency": "USD",
  "source": "card_123456",
  "destination": "account_789",
  "description": "Payment for order #123",
  "metadata": {
    "order_id": "123",
    "customer_id": "456"
  }
}
```

**Response:**
```json
{
  "id": "uuid-here",
  "amount": 100.00,
  "currency": "USD",
  "source": "card_123456",
  "destination": "account_789",
  "description": "Payment for order #123",
  "metadata": {
    "order_id": "123",
    "customer_id": "456"
  },
  "status": "pending",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00",
  "version": "v2",
  "fee": 2.00,
  "net_amount": 98.00,
  "transaction_id": "TXN-XXXXXXXX"
}
```

#### 2. Lấy Payment (Enhanced)
```http
GET /api/v2/payments/{payment_id}
```

#### 3. Cập nhật Payment (V2 only)
```http
PATCH /api/v2/payments/{payment_id}
Content-Type: application/json

{
  "status": "completed",
  "metadata": {
    "processed_by": "system"
  }
}
```

#### 4. Liệt kê Payments (V2 only)
```http
GET /api/v2/payments?status=pending&currency=USD&limit=10&offset=0
```

### Universal Endpoint

```http
GET /api/payments/{payment_id}
X-API-Version: v1  # hoặc v2 (default: v2)
```

## Chiến lược nâng cấp v1 → v2

### 1. **Backward Compatibility (Tương thích ngược)**
- V1 endpoints vẫn hoạt động bình thường
- V1 clients không bị ảnh hưởng khi v2 được triển khai
- V1 responses giữ nguyên format

### 2. **Versioning Strategy**
- **URL-based versioning**: `/api/v1/` và `/api/v2/`
- **Header-based versioning**: `X-API-Version` header cho universal endpoints
- Cả hai phương pháp đều được hỗ trợ

### 3. **Cải tiến trong V2**

#### a. Thêm fields mới:
- `destination`: Đích đến của payment
- `description`: Mô tả payment
- `metadata`: Thông tin bổ sung dạng key-value
- `updated_at`: Thời gian cập nhật
- `fee`: Phí giao dịch
- `net_amount`: Số tiền thực nhận
- `transaction_id`: ID giao dịch

#### b. Tính năng mới:
- **PATCH endpoint**: Cho phép cập nhật payment
- **List endpoint**: Liệt kê payments với filtering và pagination
- **Enhanced validation**: Kiểm tra currency hợp lệ

#### c. Cải thiện response:
- Thông tin chi tiết hơn
- Bao gồm cả v1 fields để đảm bảo compatibility

### 4. **Migration Path (Lộ trình chuyển đổi)**

#### Phase 1: Parallel Support
- V1 và V2 cùng tồn tại
- Clients có thể chọn version phù hợp
- Không breaking changes cho V1

#### Phase 2: Gradual Migration
- Khuyến khích clients migrate sang V2
- Cung cấp documentation và migration guide
- Hỗ trợ cả hai versions trong thời gian chuyển đổi

#### Phase 3: Deprecation (Tương lai)
- Thông báo deprecation cho V1
- Đặt deadline cho việc migrate
- Sau deadline, có thể disable V1 hoặc redirect sang V2

### 5. **Best Practices được áp dụng**

✅ **URL Versioning**: Rõ ràng, dễ hiểu  
✅ **Backward Compatibility**: V1 vẫn hoạt động  
✅ **Additive Changes**: Chỉ thêm fields, không xóa  
✅ **Documentation**: README rõ ràng  
✅ **Health Check**: Endpoint để kiểm tra status  
✅ **Error Handling**: Validation và error messages rõ ràng  

## Testing

### Sử dụng curl:

```bash
# V1: Tạo payment
curl -X POST http://localhost:5000/api/v1/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "currency": "USD", "source": "card_123"}'

# V1: Lấy payment
curl http://localhost:5000/api/v1/payments/{payment_id}

# V2: Tạo payment
curl -X POST http://localhost:5000/api/v2/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "currency": "USD", "source": "card_123", "destination": "acc_456", "description": "Test payment"}'

# V2: Cập nhật payment
curl -X PATCH http://localhost:5000/api/v2/payments/{payment_id} \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'

# V2: Liệt kê payments
curl "http://localhost:5000/api/v2/payments?status=pending&limit=10"
```

## Lưu ý

- Demo này sử dụng in-memory storage, dữ liệu sẽ mất khi restart server
- Trong production, nên sử dụng database
- Nên implement authentication và authorization
- Nên thêm rate limiting và monitoring
- Nên có comprehensive test suite

