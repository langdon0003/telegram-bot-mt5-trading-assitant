# Troubleshooting: MT5 IPC Timeout Error

## Lỗi thường gặp

```
ERROR:engine.mt5_adapter:MT5 initialize failed: (-10005, 'IPC timeout')
```

## Nguyên nhân

**IPC (Inter-Process Communication) timeout** xảy ra khi:

1. MT5 terminal không phản hồi trong thời gian chờ
2. Có quá nhiều connections đồng thời đến MT5
3. MT5 đang busy (đang connect/disconnect account)
4. Process Python khác đang giữ connection
5. MT5 terminal bị freeze hoặc crash

## Giải pháp nhanh

### Option 1: Sử dụng fix script (Khuyến nghị)

```bash
python fix_ipc_timeout.py
```

Script này sẽ:
- Shutdown tất cả connections
- Đợi MT5 giải phóng resources
- Retry initialize với logic thông minh
- Verify connection

### Option 2: Manual fix

**Bước 1: Đóng hoàn toàn MT5**

```
- Nhấn chuột phải vào MT5 icon ở taskbar
- Chọn "Close" hoặc "Exit"
- Đợi 10 giây
```

**Bước 2: Kill process (nếu cần)**

```
- Mở Task Manager (Ctrl+Shift+Esc)
- Tìm "terminal64.exe" hoặc "MetaTrader"
- Nhấn "End Task"
- Đợi 10 giây
```

**Bước 3: Mở lại MT5**

```
- Mở MT5
- Đợi login xong
- Đợi chart load xong
- Đợi thêm 5 giây
```

**Bước 4: Test connection**

```bash
python test_mt5_connection.py
```

**Bước 5: Chạy bot**

```bash
python run_bot.py
```

## Giải pháp nâng cao

### 1. Tăng timeout trong MT5 API

Không có cách trực tiếp, nhưng retry logic đã được implement trong code.

### 2. Đảm bảo chỉ 1 connection

```python
# Bot đã được cập nhật để:
# - Không connect ngay khi init
# - Chỉ connect khi cần thiết (lazy connection)
# - Retry với delay khi gặp lỗi
```

### 3. Check running processes

```bash
# Windows: Task Manager → Details tab
# Tìm các process:
# - terminal64.exe (MT5)
# - python.exe (Bot cũ)

# Kill process Python cũ nếu có
```

### 4. Antivirus/Firewall

```
- Thêm MT5 vào whitelist
- Thêm Python vào whitelist
- Tắt Real-time Protection tạm thời để test
```

## Phòng tránh

### 1. Đóng bot đúng cách

```bash
# Nhấn Ctrl+C để stop bot
# Đợi bot shutdown gracefully
# Không kill process trực tiếp
```

### 2. Không chạy nhiều bot cùng lúc

```
# Chỉ chạy 1 instance của run_bot.py
# Không chạy test_mt5_connection.py khi bot đang chạy
```

### 3. Đợi giữa các lần chạy

```
# Sau khi stop bot, đợi 5 giây
# Trước khi start lại bot
```

## Cải tiến đã implement

### v2.0 - IPC Timeout Fixes

✅ **Lazy Connection**
- Bot không connect MT5 ngay khi init
- Chỉ connect khi thực sự cần
- Tránh timeout khi startup

✅ **Retry Logic**
- Tự động retry 3 lần khi initialize fail
- Delay 2 giây giữa các lần retry
- Log chi tiết từng attempt

✅ **Smart Reconnect**
- Check connection health trước khi action
- Tự động reconnect khi mất kết nối
- Chỉ shutdown khi thật sự cần

✅ **Longer Delays**
- Tăng delay sau shutdown từ 1s → 2s
- Tăng delay giữa retry từ 1s → 2s
- Cho MT5 đủ thời gian cleanup

## Test sau khi fix

### 1. Test basic connection

```bash
python test_mt5_connection.py
```

Expected output:
```
1. Kiểm tra MT5 terminal...
2. Dọn dẹp connections cũ...
   ✓ Shutdown OK
3. Initialize MT5 (với retry logic)...
   Attempt 1/3... ✓ OK
   ✓ Initialize OK
...
✅ TẤT CẢ OK - Bot có thể kết nối MT5!
```

### 2. Test reconnect logic

```bash
python test_reconnect_logic.py
```

Expected:
- Connect thành công
- Detect already connected
- Không bị IPC timeout khi connect lại

### 3. Test bot startup

```bash
python run_bot.py
```

Expected:
```
✅ Loaded .env file
🤖 Starting Telegram Trading Bot...
📊 Database: trading_bot.db
INFO - Bot initialized. MT5 connection will be established when needed.
INFO - Bot started
```

Không còn lỗi IPC timeout!

## Tham khảo

- [MT5 Python API Docs](https://www.mql5.com/en/docs/integration/python_metatrader5)
- [IPC Timeout Issue #123](https://github.com/MetaQuotes/MetaTrader5-Python/issues)

## Báo lỗi

Nếu vẫn gặp IPC timeout sau khi thử tất cả:

1. Chụp screenshot error
2. Copy log đầy đủ
3. Ghi rõ:
   - MT5 version
   - Python version
   - MetaTrader5 package version (`pip show MetaTrader5`)
   - Windows version
4. Tạo issue trên GitHub
