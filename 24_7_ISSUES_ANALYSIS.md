# Phân Tích Vấn Đề Chạy 24/7 - Telegram Trading Bot

## 🔴 CÁC VẤN ĐỀ NGHIÊM TRỌNG

### 1. **DATABASE CONNECTION LEAKS** ❌ CRITICAL

**File:** `bot/setup_commands.py`

**Vấn đề:**

- Mỗi lần gọi function, tạo một DatabaseManager() mới và connect()
- Không dùng connection pool
- Tạo nhiều connections không cần thiết

**Code có vấn đề:**

```python
# Lines 90-97 và nhiều nơi khác
db = DatabaseManager()
db.connect()
user = db.get_user_by_telegram_id(telegram_id)
# ...
db.close()  # Đôi khi quên close
```

**Hậu quả khi chạy 24/7:**

- Sau vài giờ/ngày: Database connections tăng dần
- Memory leak: Mỗi connection giữ memory
- Sau 1-2 ngày: "Too many connections" error
- Bot bị treo, không thể query database

**Mức độ nghiêm trọng:** 🔴 **CRITICAL**

---

### 2. **SQLITE CONNECTION KHÔNG THREAD-SAFE** ⚠️ HIGH

**File:** `bot/telegram_bot.py`, `database/db_manager.py`

**Vấn đề:**

```python
# telegram_bot.py line 84
self.db.connect()
self.db.initialize_schema()
```

- Bot tạo 1 connection duy nhất khi khởi động
- Telegram bot chạy async với nhiều handlers đồng thời
- Multiple threads/async tasks cùng dùng 1 SQLite connection
- SQLite không thread-safe theo mặc định

**Hậu quả:**

- Database locked errors
- Race conditions
- Data corruption có thể xảy ra
- Bot lag hoặc crash khi nhiều users cùng trade

**Mức độ nghiêm trọng:** ⚠️ **HIGH**

---

### 3. **MT5 CONNECTION KHÔNG ĐƯỢC HEALTH CHECK** ⚠️ HIGH

**File:** `engine/mt5_adapter.py`

**Vấn đề:**

- Kết nối MT5 một lần khi cần
- Không có background health check
- Nếu MT5 disconnect (restart, network issue), bot không biết

**Code:**

```python
# Line 821-823 - Chỉ check khi execute trade
if not self.mt5_adapter.connect():
    raise Exception("Failed to connect to MT5...")
```

**Hậu quả:**

- MT5 restart → Bot vẫn nghĩ đang connected
- User gửi lệnh → Failed
- Không tự động reconnect
- Phải manual /reconnectmt5

**Mức độ nghiêm trọng:** ⚠️ **HIGH**

---

### 4. **TELEGRAM POLLING KHÔNG CÓ ERROR RECOVERY** ⚠️ MEDIUM

**File:** `bot/telegram_bot.py` line 221

**Code:**

```python
app.run_polling()
```

**Vấn đề:**

- Không có try/except wrapper
- Network timeout → Bot crash
- Telegram API issues → Bot stop
- Không tự động retry

**Hậu quả:**

- Bot stop khi mất mạng tạm thời
- Cần manual restart
- Downtime không cần thiết

**Mức độ nghiêm trọng:** ⚠️ **MEDIUM**

---

### 5. **LOGGING KHÔNG ROTATION** ⚠️ MEDIUM

**File:** `bot/telegram_bot.py`, `engine/mt5_adapter.py`

**Code:**

```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
```

**Vấn đề:**

- Log ra console, không ra file
- Nếu log ra file → File sẽ tăng vô hạn
- Không có log rotation

**Hậu quả sau 1 tháng:**

- Log file 10+ GB
- Đầy disk
- Bot crash vì không ghi được log

**Mức độ nghiêm trọng:** ⚠️ **MEDIUM**

---

### 6. **MEMORY LEAK TRONG CONTEXT.USER_DATA** ⚠️ LOW-MEDIUM

**File:** `bot/telegram_bot.py`

**Vấn đề:**

- Conversation handler lưu data trong context.user_data
- Nếu user không hoàn thành conversation → Data không clear
- Tích lũy theo thời gian

**Code:**

```python
context.user_data['order_type'] = 'LIMIT_BUY'
context.user_data['symbol'] = symbol
# ... nhiều fields khác
```

**Hậu quả:**

- Sau vài ngày: Memory tăng dần
- 1000 incomplete conversations = memory leak
- Bot chậm lại

**Mức độ nghiêm trọng:** ⚠️ **LOW-MEDIUM**

---

## ✅ ĐIỂM TỐT

1. ✅ **Conversation Handler**: Dùng ConversationHandler tốt, có fallback
2. ✅ **MT5 Retry Logic**: Có retry khi initialize MT5 (3 attempts)
3. ✅ **Async/Await**: Dùng async đúng cách
4. ✅ **Error Handling**: Có try/except ở nhiều chỗ

---

## 📊 ĐÁNH GIÁ TỔNG QUAN

### Khả năng chạy 24/7:

- ❌ **KHÔNG ỔN ĐỊNH** với setup hiện tại
- 🕐 **Thời gian trước khi gặp vấn đề:** 12-48 giờ
- 🔥 **Vấn đề chính:** Database connection leaks

### Kịch bản có thể xảy ra:

1. **6-12 giờ đầu:** Bot chạy OK
2. **12-24 giờ:** Database connections tích lũy, bắt đầu lag
3. **24-48 giờ:** "Too many connections", bot bị treo
4. **Khi MT5 restart:** Bot không tự reconnect, lệnh fail
5. **Sau 1 tuần:** Log file lớn (nếu log ra file)

---

## 🎯 ƯU TIÊN SỬA

| #   | Vấn đề                    | Mức độ      | Ước tính thời gian | Bắt buộc |
| --- | ------------------------- | ----------- | ------------------ | -------- |
| 1   | Database Connection Leaks | 🔴 CRITICAL | 2-3 giờ            | ✅ CẦN   |
| 2   | SQLite Thread-Safety      | ⚠️ HIGH     | 3-4 giờ            | ✅ CẦN   |
| 3   | MT5 Health Check          | ⚠️ HIGH     | 2 giờ              | ✅ CẦN   |
| 4   | Polling Error Recovery    | ⚠️ MEDIUM   | 1 giờ              | ✅ NÊN   |
| 5   | Logging Rotation          | ⚠️ MEDIUM   | 30 phút            | ✅ NÊN   |
| 6   | Memory Leak Context       | ⚠️ LOW      | 1 giờ              | Tùy chọn |

**Tổng thời gian ước tính:** 9-11 giờ để fix hết

---

## 📋 KHUYẾN NGHỊ

### Cấp bách (Fix ngay):

1. Fix database connection leaks
2. Implement connection pooling
3. Add MT5 health check

### Quan trọng (Fix trong tuần):

4. Add polling error recovery
5. Implement log rotation
6. Add monitoring/alerting

### Nên có (Nice to have):

7. Add resource usage monitoring
8. Implement graceful shutdown
9. Add automated health checks
10. Setup supervisor/systemd for auto-restart

---

## 🔍 CÁCH KIỂM TRA

### Test Database Leaks:

```python
# Chạy script này trong 1 giờ
import time
import psutil
import os

process = psutil.Process(os.getpid())

while True:
    mem_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory: {mem_mb:.2f} MB")
    time.sleep(60)  # Check every minute
```

### Monitor SQLite Connections:

```sql
-- Check số lượng connections
.shell ps aux | grep "telegram_bot"
```

### Check MT5 Status:

```bash
# Restart MT5 trong khi bot đang chạy
# Thử trade → Sẽ fail nếu không có auto-reconnect
```

---

## 📝 GHI CHÚ

Các vấn đề này rất phổ biến khi chạy Python bot 24/7. Hầu hết các bot production đều cần:

- Connection pooling
- Health checks
- Log rotation
- Error recovery
- Monitoring

File này sẽ được theo dõi bởi `FIXES_IMPLEMENTATION.md` khi bắt đầu sửa.
