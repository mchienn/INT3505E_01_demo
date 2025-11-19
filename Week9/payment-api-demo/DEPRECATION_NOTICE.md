# ⚠️ Deprecation Notice - Payment API V1

## Thông báo chính thức

**Payment API Version 1 (V1) sẽ bị deprecated và ngừng hỗ trợ.**

Chúng tôi thông báo rằng **Payment API v1** (`/api/v1/payments`) sẽ bị deprecated và sẽ ngừng hoạt động trong tương lai. Tất cả clients sử dụng V1 được khuyến khích migrate sang **Payment API v2** (`/api/v2/payments`) càng sớm càng tốt.

---

## 📅 Timeline

| Ngày           | Sự kiện                                                | Trạng thái       |
| -------------- | ------------------------------------------------------ | ---------------- |
| **2024-01-01** | V2 API được release                                    | ✅ Đã hoàn thành |
| **2024-06-01** | Deprecation notice được gửi                            | ✅ Hiện tại      |
| **2024-12-01** | V1 API bị deprecated (6 tháng sau notice)              | ⏳ Sắp tới       |
| **2025-06-01** | V1 API ngừng hoạt động hoàn toàn (12 tháng sau notice) | ⏳ Tương lai     |

### Trạng thái hiện tại: **Deprecated - Migration Period**

V1 API vẫn hoạt động nhưng **không còn được maintain** và sẽ bị shutdown trong tương lai.

---

## 🎯 Lý do Deprecation

1. **V2 API cung cấp tính năng tốt hơn:**

   - Hỗ trợ `description` và `metadata` fields
   - Endpoint `PATCH` để update payment
   - Endpoint `GET /api/v2/payments` để list với filtering
   - Response format enriched với `updated_at` và `version`

2. **Maintenance overhead:**

   - Duy trì 2 versions tăng chi phí development và testing
   - V1 không còn được cải tiến

3. **API consistency:**
   - Tập trung vào V2 để đảm bảo chất lượng và tính nhất quán

---

## 🔄 Migration Guide

### Bước 1: Cập nhật Base URL

**Trước (V1):**

```http
POST /api/v1/payments
GET /api/v1/payments/{id}
```

**Sau (V2):**

```http
POST /api/v2/payments
GET /api/v2/payments/{id}
PATCH /api/v2/payments/{id}  # NEW
GET /api/v2/payments          # NEW
```

### Bước 2: Cập nhật Request Body

**V1 Request:**

```json
{
  "amount": 100.0,
  "currency": "USD",
  "source": "card_123456"
}
```

**V2 Request (tương thích - chỉ cần đổi URL):**

```json
{
  "amount": 100.0,
  "currency": "USD",
  "source": "card_123456"
}
```

**V2 Request (với tính năng mới - optional):**

```json
{
  "amount": 100.0,
  "currency": "USD",
  "source": "card_123456",
  "description": "Payment for order #123", // NEW - optional
  "metadata": {
    // NEW - optional
    "order_id": "123",
    "customer_id": "456"
  }
}
```

### Bước 3: Cập nhật Response Handling

**V1 Response:**

```json
{
  "id": "uuid",
  "amount": 100.0,
  "currency": "USD",
  "source": "card_123456",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00"
}
```

**V2 Response (enriched):**

```json
{
  "id": "uuid",
  "amount": 100.0,
  "currency": "USD",
  "source": "card_123456",
  "description": null, // NEW
  "metadata": {}, // NEW
  "status": "pending",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00", // NEW
  "version": "v2" // NEW
}
```

**Lưu ý:** V2 response có thêm các fields mới. Code cũ vẫn hoạt động nếu chỉ đọc các fields V1.

### Bước 4: Sử dụng tính năng mới (Optional)

**Update Payment (V2 only):**

```http
PATCH /api/v2/payments/{id}
Content-Type: application/json

{
  "status": "completed",
  "metadata": {
    "processed_by": "system"
  }
}
```

**List Payments (V2 only):**

```http
GET /api/v2/payments?status=pending&currency=USD&limit=10&offset=0
```

---

## ⚠️ Breaking Changes

### Không có Breaking Changes!

V2 API được thiết kế để **backward compatible** với V1:

- ✅ Tất cả V1 requests đều hoạt động với V2
- ✅ V2 response bao gồm tất cả V1 fields
- ✅ Optional fields mới không bắt buộc

**Migration path đơn giản:** Chỉ cần đổi URL từ `/api/v1/` sang `/api/v2/`

---

## 📋 Migration Checklist

- [ ] Cập nhật base URL từ `/api/v1/` sang `/api/v2/`
- [ ] Test tất cả endpoints với V2
- [ ] Cập nhật response parsing (nếu cần handle các fields mới)
- [ ] Cập nhật documentation và code comments
- [ ] Deploy và monitor
- [ ] Xóa code liên quan đến V1 (sau khi đã migrate xong)

---

## 🔍 Testing

### Test V2 API trước khi migrate:

```bash
# Test create payment
curl -X POST http://localhost:5000/api/v2/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "currency": "USD", "source": "card_test"}'

# Test get payment
curl http://localhost:5000/api/v2/payments/{payment_id}

# Test update payment (V2 only)
curl -X PATCH http://localhost:5000/api/v2/payments/{payment_id} \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'

# Test list payments (V2 only)
curl "http://localhost:5000/api/v2/payments?status=pending&limit=10"
```

### Sử dụng Swagger UI:

- **V2 Documentation:** http://localhost:5000/docs/v2
- **Test trực tiếp:** Click "Try it out" trong Swagger UI

---

## 📞 Support

### Trong thời gian migration:

- ✅ V1 API vẫn hoạt động bình thường
- ✅ V2 API đã sẵn sàng sử dụng
- ✅ Cả 2 versions cùng tồn tại trong migration period

### Sau khi V1 bị shutdown:

- ❌ V1 endpoints sẽ trả về `410 Gone` hoặc redirect sang V2
- ✅ Chỉ V2 API hoạt động

### Cần hỗ trợ?

- Xem documentation: http://localhost:5000/docs/v2
- Xem OpenAPI spec: http://localhost:5000/openapi/v2.yaml
- Test với Swagger UI: http://localhost:5000/docs/v2

---

## 📊 So sánh V1 vs V2

| Tính năng                  | V1          | V2            |
| -------------------------- | ----------- | ------------- |
| **Endpoints**              | 2 endpoints | 4 endpoints   |
| **POST /payments**         | ✅          | ✅ (enhanced) |
| **GET /payments/{id}**     | ✅          | ✅ (enhanced) |
| **PATCH /payments/{id}**   | ❌          | ✅ NEW        |
| **GET /payments** (list)   | ❌          | ✅ NEW        |
| **Description field**      | ❌          | ✅            |
| **Metadata field**         | ❌          | ✅            |
| **Updated_at timestamp**   | ❌          | ✅            |
| **Version field**          | ❌          | ✅            |
| **Filtering & Pagination** | ❌          | ✅            |

---

## 🚨 Action Required

### Ngay lập tức:

1. **Review codebase** - Tìm tất cả nơi sử dụng `/api/v1/payments`
2. **Plan migration** - Lên kế hoạch migrate sang V2
3. **Test V2** - Test V2 API trong môi trường staging

### Trước 2024-12-01 (6 tháng):

1. **Complete migration** - Hoàn thành migrate tất cả clients
2. **Remove V1 code** - Xóa code liên quan đến V1
3. **Update documentation** - Cập nhật docs chỉ còn V2

### Sau 2025-06-01:

- V1 API sẽ **không còn hoạt động**
- Tất cả requests đến V1 sẽ trả về error

---

## 📝 Examples

### Example 1: Simple Migration (Minimal Change)

**Before (V1):**

```python
response = requests.post(
    'http://localhost:5000/api/v1/payments',
    json={'amount': 100, 'source': 'card_123'}
)
```

**After (V2):**

```python
response = requests.post(
    'http://localhost:5000/api/v2/payments',  # Chỉ đổi URL
    json={'amount': 100, 'source': 'card_123'}
)
```

### Example 2: Using New Features

**V2 với description và metadata:**

```python
response = requests.post(
    'http://localhost:5000/api/v2/payments',
    json={
        'amount': 100,
        'source': 'card_123',
        'description': 'Payment for order #123',  # NEW
        'metadata': {'order_id': '123'}            # NEW
    }
)
```

### Example 3: Update Payment (V2 only)

```python
response = requests.patch(
    f'http://localhost:5000/api/v2/payments/{payment_id}',
    json={
        'status': 'completed',
        'metadata': {'processed_by': 'system'}
    }
)
```

---

## ✅ Benefits của V2

1. **Tính năng phong phú hơn:**

   - Description và metadata cho flexible use cases
   - Update endpoint để thay đổi payment
   - List endpoint với filtering

2. **Better observability:**

   - `updated_at` timestamp
   - `version` field để track

3. **Future-proof:**
   - V2 sẽ tiếp tục được maintain và cải tiến
   - V1 sẽ bị shutdown

---

## 📚 Resources

- **V2 API Documentation:** http://localhost:5000/docs/v2
- **V2 OpenAPI Spec:** http://localhost:5000/openapi/v2.yaml
- **Migration Examples:** Xem phần Examples ở trên
- **Integration Tests:** `test_integration.py`
- **Load Tests:** `k6_test_v2.js`

---

## ⏰ Deadline

**⚠️ QUAN TRỌNG:** V1 API sẽ ngừng hoạt động vào **2025-06-01**.

Hãy hoàn thành migration trước deadline để tránh service interruption.

---

_Last updated: 2024-06-01_
