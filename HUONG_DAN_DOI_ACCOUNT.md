# Hướng dẫn đổi MT5 Account

## 2 Cách đổi account MT5:

### ✅ Cách 1: Đổi trực tiếp qua Bot (Nhanh - không cần restart)

Dùng command `/changeaccount` trong Telegram:

```
/changeaccount <login> <password> <server>
```

**Ví dụ:**
```
/changeaccount 12345678 mypassword Exness-MT5Real
```

**Ưu điểm:**
- ✅ Đổi ngay lập tức, không cần restart bot
- ✅ Tiện cho việc test nhiều account

**Nhược điểm:**
- ⚠️ Credentials chỉ tồn tại trong phiên hiện tại
- ⚠️ Khi restart bot, sẽ dùng lại credentials từ file `.env`
- ⚠️ Message chứa password sẽ bị xóa tự động (bảo mật)

---

### ✅ Cách 2: Lưu vĩnh viễn vào file .env (Khuyên dùng)

**Bước 1:** Sửa file `.env` trong thư mục gốc:

```bash
# Mở file .env và sửa:
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=Exness-MT5Real
```

**Bước 2:** Reload credentials bằng command `/reconnectmt5` trong Telegram

Bot sẽ:
1. Đọc lại file `.env`
2. Ngắt kết nối MT5 hiện tại
3. Kết nối lại với credentials mới
4. Hiển thị thông tin account mới

**Ưu điểm:**
- ✅ Lưu vĩnh viễn, không lo mất khi restart
- ✅ An toàn hơn (không gửi password qua Telegram)
- ✅ Dùng cho production

---

## Kiểm tra kết nối MT5

Dùng command `/mt5connection` để kiểm tra:
- Account hiện tại
- Balance, Equity
- Trạng thái kết nối

---

## Lưu ý quan trọng:

1. **File `.env` phải nằm ở thư mục gốc** (cùng thư mục với `run_bot.py`)

2. **Cần cài python-dotenv:**
   ```bash
   pip install python-dotenv
   ```

3. **Không commit file `.env` lên Git** (đã có trong .gitignore)

4. **Format server name:** 
   - Nếu server có khoảng trắng, ghi cả cụm: `Broker Server Name`
   - Ví dụ: `/changeaccount 12345678 pass123 Exness-MT5 Real`

---

## Troubleshooting:

### ❌ "Failed to reconnect to MT5"

**Kiểm tra:**
- MT5 có đang chạy không?
- Login, password, server có đúng không?
- Internet có kết nối không?
- Tường lửa có chặn MT5 không?

### ❌ "Could not reload .env"

**Nguyên nhân:** Chưa cài `python-dotenv`

**Giải pháp:**
```bash
pip install python-dotenv
```

### ❌ Đổi .env rồi nhưng vẫn login account cũ

**Nguyên nhân:** Chưa dùng `/reconnectmt5` để reload

**Giải pháp:** Gửi command `/reconnectmt5` trong Telegram

---

## Ví dụ thực tế:

### Scenario 1: Test tạm thời account khác

```
/changeaccount 87654321 testpass Broker-Demo
```

→ Bot sẽ đổi ngay, test xong dùng `/reconnectmt5` để quay lại account chính từ `.env`

### Scenario 2: Đổi account chính vĩnh viễn

1. Sửa file `.env`:
   ```
   MT5_LOGIN=99999999
   MT5_PASSWORD=newpass123
   MT5_SERVER=NewBroker-Real
   ```

2. Gửi command: `/reconnectmt5`

3. Kiểm tra: `/mt5connection`

→ Account mới được lưu vĩnh viễn!
