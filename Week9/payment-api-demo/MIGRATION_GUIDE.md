# Migration Guide - Payment API V1 → V2

## 📋 Tổng quan

Hướng dẫn chuyển đổi từ Payment API V1 sang V2. Migration đơn giản vì V2 **backward compatible** với V1.

---

## ⏰ Timeline

| Thời điểm      | Sự kiện                 |
| -------------- | ----------------------- |
| **2024-06-01** | Deprecation notice      |
| **2024-12-01** | V1 deprecated (6 tháng) |
| **2025-06-01** | V1 shutdown (12 tháng)  |

**⚠️ Deadline:** Hoàn thành migration trước **2025-06-01**

---

## 🔄 Thay đổi chính

### 1. Base URL

**V1:**

```
/api/v1/payments
```

**V2:**

```
/api/v2/payments
```

### 2. Endpoints mới (V2 only)

- `PATCH /api/v2/payments/{id}` - Update payment
- `GET /api/v2/payments` - List payments với filtering

### 3. Fields mới trong Response

V2 response có thêm các fields (optional):

- `description` - Mô tả payment
- `metadata` - Thông tin bổ sung
- `updated_at` - Thời gian cập nhật
- `version` - API version

---

## ⚠️ Breaking Changes

### **KHÔNG CÓ BREAKING CHANGES**

V2 được thiết kế để backward compatible:

- ✅ Tất cả V1 requests hoạt động với V2
- ✅ V2 response bao gồm tất cả V1 fields
- ✅ Optional fields mới không bắt buộc

**Migration đơn giản:** Chỉ cần đổi URL từ `/api/v1/` sang `/api/v2/`

---

## 📝 Code Examples

### Example 1: Create Payment

**V1:**

```python
import requests

response = requests.post(
    'http://localhost:5000/api/v1/payments',
    json={
        'amount': 100.00,
        'currency': 'USD',
        'source': 'card_123456'
    }
)
```

**V2 (minimal change):**

```python
import requests

response = requests.post(
    'http://localhost:5000/api/v2/payments',  # Chỉ đổi URL
    json={
        'amount': 100.00,
        'currency': 'USD',
        'source': 'card_123456'
    }
)
```

**V2 (với tính năng mới):**

```python
response = requests.post(
    'http://localhost:5000/api/v2/payments',
    json={
        'amount': 100.00,
        'currency': 'USD',
        'source': 'card_123456',
        'description': 'Payment for order #123',  # NEW - optional
        'metadata': {                               # NEW - optional
            'order_id': '123',
            'customer_id': '456'
        }
    }
)
```

### Example 2: Get Payment

**V1:**

```python
response = requests.get(f'http://localhost:5000/api/v1/payments/{payment_id}')
data = response.json()
# data chỉ có: id, amount, currency, source, status, created_at
```

**V2:**

```python
response = requests.get(f'http://localhost:5000/api/v2/payments/{payment_id}')
data = response.json()
# data có thêm: description, metadata, updated_at, version
# Code cũ vẫn hoạt động nếu chỉ đọc các fields V1
```

### Example 3: Update Payment (V2 only)

**V1:** ❌ Không hỗ trợ

**V2:**

```python
response = requests.patch(
    f'http://localhost:5000/api/v2/payments/{payment_id}',
    json={
        'status': 'completed',
        'metadata': {
            'processed_by': 'system'
        }
    }
)
```

### Example 4: List Payments (V2 only)

**V1:** ❌ Không hỗ trợ

**V2:**

```python
response = requests.get(
    'http://localhost:5000/api/v2/payments',
    params={
        'status': 'pending',
        'currency': 'USD',
        'limit': 10,
        'offset': 0
    }
)
data = response.json()
# data.payments - danh sách payments
# data.total - tổng số
# data.limit, data.offset - pagination
```

---

## 📊 Side-by-Side Comparison

### Request Body

| Field         | V1          | V2          | Notes         |
| ------------- | ----------- | ----------- | ------------- |
| `amount`      | ✅ Required | ✅ Required | Giống nhau    |
| `source`      | ✅ Required | ✅ Required | Giống nhau    |
| `currency`    | ⚪ Optional | ⚪ Optional | Giống nhau    |
| `description` | ❌          | ⚪ Optional | **NEW in V2** |
| `metadata`    | ❌          | ⚪ Optional | **NEW in V2** |

### Response Body

| Field         | V1  | V2  | Notes         |
| ------------- | --- | --- | ------------- |
| `id`          | ✅  | ✅  | Giống nhau    |
| `amount`      | ✅  | ✅  | Giống nhau    |
| `currency`    | ✅  | ✅  | Giống nhau    |
| `source`      | ✅  | ✅  | Giống nhau    |
| `status`      | ✅  | ✅  | Giống nhau    |
| `created_at`  | ✅  | ✅  | Giống nhau    |
| `description` | ❌  | ⚪  | **NEW in V2** |
| `metadata`    | ❌  | ⚪  | **NEW in V2** |
| `updated_at`  | ❌  | ⚪  | **NEW in V2** |
| `version`     | ❌  | ⚪  | **NEW in V2** |

### Endpoints

| Endpoint               | V1  | V2            |
| ---------------------- | --- | ------------- |
| `POST /payments`       | ✅  | ✅ (enhanced) |
| `GET /payments/{id}`   | ✅  | ✅ (enhanced) |
| `PATCH /payments/{id}` | ❌  | ✅ **NEW**    |
| `GET /payments`        | ❌  | ✅ **NEW**    |

---

## 🔧 Migration Steps

### Bước 1: Cập nhật Base URL

Tìm và thay thế tất cả `/api/v1/` thành `/api/v2/`:

```python
# Before
BASE_URL = 'http://localhost:5000/api/v1/payments'

# After
BASE_URL = 'http://localhost:5000/api/v2/payments'
```

### Bước 2: Test với V2

Test tất cả endpoints với V2 để đảm bảo hoạt động:

```bash
# Test create
curl -X POST http://localhost:5000/api/v2/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "source": "card_test"}'

# Test get
curl http://localhost:5000/api/v2/payments/{payment_id}
```

### Bước 3: Cập nhật Response Parsing (nếu cần)

Nếu code cũ chỉ đọc V1 fields, không cần thay đổi. Nếu muốn dùng fields mới:

```python
# V1 code (vẫn hoạt động với V2)
data = response.json()
payment_id = data['id']
amount = data['amount']

# V2 code (sử dụng fields mới)
data = response.json()
description = data.get('description')  # Có thể None
metadata = data.get('metadata', {})    # Có thể {}
```

### Bước 4: Deploy và Monitor

1. Deploy code mới
2. Monitor logs và errors
3. Verify tất cả requests thành công

---

## ❌ Common Errors & Fixes

### Error 1: 404 Not Found

**Nguyên nhân:** Vẫn đang gọi `/api/v1/` sau khi V1 bị shutdown

**Fix:**

```python
# Wrong
url = 'http://localhost:5000/api/v1/payments'

# Correct
url = 'http://localhost:5000/api/v2/payments'
```

### Error 2: Response parsing fails

**Nguyên nhân:** Code expect V1 shape nhưng nhận V2 response

**Fix:**

```python
# V1 code (expect chỉ có V1 fields)
data = response.json()
# data['description']  # ❌ Error nếu dùng V1

# V2 code (handle optional fields)
data = response.json()
description = data.get('description')  # ✅ Safe với .get()
```

### Error 3: Missing fields

**Nguyên nhân:** Code cũ expect fields không có trong V1

**Fix:**

```python
# Wrong (assume fields luôn có)
description = data['description']

# Correct (check hoặc dùng default)
description = data.get('description', '')  # Default empty string
metadata = data.get('metadata', {})        # Default empty dict
```

### Error 4: PATCH endpoint không tồn tại

**Nguyên nhân:** Dùng PATCH với V1 URL

**Fix:**

```python
# Wrong
requests.patch('http://localhost:5000/api/v1/payments/{id}', ...)

# Correct
requests.patch('http://localhost:5000/api/v2/payments/{id}', ...)
```

### Sử dụng Swagger UI:

- **V2 Docs:** http://localhost:5000/docs/v2
- Click "Try it out" để test trực tiếp

---

## 📚 Resources

- **V2 API Documentation:** http://localhost:5000/docs/v2
- **V2 OpenAPI Spec:** http://localhost:5000/openapi/v2.yaml
- **Deprecation Notice:** `DEPRECATION_NOTICE.md`
- **Load Tests:** `k6_test_v2.js`

_Last updated: 2024-06-01_
