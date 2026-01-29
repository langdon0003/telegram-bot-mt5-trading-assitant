# Hướng Dẫn Cấu Hình Nhiều MT5 Instance

## Giới thiệu

Khi chạy nhiều instance MT5 trên cùng một máy VPS Windows để copy trade, bạn cần chỉ định bot kết nối đến instance cụ thể nào.

## Cấu hình

### Bước 1: Tạo file .env

Tạo file `.env` trong thư mục gốc của project (nếu chưa có):

```bash
cp .env.example .env
```

### Bước 2: Cấu hình đường dẫn MT5 Terminal

Mở file `.env` và thêm đường dẫn tới terminal64.exe của instance MT5 bạn muốn kết nối:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# MT5 Configuration
MT5_LOGIN=
MT5_PASSWORD=
MT5_SERVER=

# MT5 Terminal Path - Chỉ định instance MT5 cụ thể
MT5_TERMINAL_PATH=C:\Program Files\MetaTrader 5 - 50k 510zero\terminal64.exe

# Database
DATABASE_PATH=trading_bot.db
```

### Bước 3: Lưu ý quan trọng

1. **Đường dẫn phải chính xác**: Đảm bảo đường dẫn trỏ tới file `terminal64.exe` (không phải thư mục)

2. **Dấu gạch chéo**: Trên Windows, bạn có thể dùng:
   - `C:\Program Files\MetaTrader 5 - 50k 510zero\terminal64.exe` (backslash)
   - `C:/Program Files/MetaTrader 5 - 50k 510zero/terminal64.exe` (forward slash - khuyến nghị)

3. **Dấu cách trong đường dẫn**: Không cần đặt trong dấu ngoặc kép

4. **Nếu không cấu hình**: Bot sẽ kết nối tới MT5 mặc định của hệ thống

## Ví dụ cấu hình

### Instance 1: Account 50k

```env
MT5_TERMINAL_PATH=C:\Program Files\MetaTrader 5 - 50k 510zero\terminal64.exe
```

### Instance 2: Account 100k

```env
MT5_TERMINAL_PATH=C:\Program Files\MetaTrader 5 - 100k\terminal64.exe
```

### Instance 3: Account Demo

```env
MT5_TERMINAL_PATH=D:\MT5 Instances\Demo Account\terminal64.exe
```

## Kiểm tra kết nối

Sau khi cấu hình, chạy script test để kiểm tra:

```bash
python test_mt5_connection.py
```

Bot sẽ hiển thị thông tin về instance MT5 mà nó đã kết nối:

- Account number
- Account name
- Server
- Balance
- Equity

## Chạy nhiều bot cho nhiều instance

Nếu bạn muốn chạy nhiều bot, mỗi bot cho một instance MT5:

1. Tạo nhiều thư mục project riêng biệt
2. Mỗi thư mục có file `.env` riêng với `MT5_TERMINAL_PATH` khác nhau
3. Mỗi bot cần `TELEGRAM_BOT_TOKEN` riêng
4. Chạy mỗi bot trong thư mục tương ứng

## Xử lý lỗi

### Lỗi: MT5 initialize failed

- Kiểm tra đường dẫn có chính xác không
- Đảm bảo MT5 đã được cài đặt tại đường dẫn đó
- Kiểm tra quyền truy cập file

### Lỗi: Connection timeout

- MT5 instance có thể đang bị chiếm dụng bởi process khác
- Thử đóng tất cả MT5 terminals và chạy lại
- Kiểm tra MT5 có đang chạy với quyền Administrator không

## Ghi chú kỹ thuật

Bot sử dụng `mt5.initialize(path=mt5_terminal_path)` để kết nối tới instance cụ thể thay vì instance mặc định.

Code implementation trong [engine/mt5_adapter.py](engine/mt5_adapter.py):

```python
# Read MT5 terminal path from env
mt5_terminal_path = os.getenv("MT5_TERMINAL_PATH")

# Initialize with terminal path if provided
if mt5_terminal_path:
    logger.info(f"Initializing MT5 with terminal path: {mt5_terminal_path}")
    init_result = mt5.initialize(path=mt5_terminal_path)
else:
    init_result = mt5.initialize()
```
