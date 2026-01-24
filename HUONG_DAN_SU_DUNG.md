# Hướng Dẫn Chạy Hệ Thống Trading Bot

## Tổng Quan Hệ Thống

Hệ thống bao gồm 2 process chạy độc lập:

1. **Telegram Bot** - Nhận lệnh từ user, tạo trade command, gửi vào queue
2. **Trade Engine Worker** - Monitor queue, thực thi lệnh trong MT5, cập nhật database

```
┌──────────────┐         ┌───────────┐         ┌──────────────────┐
│ Telegram Bot │────────>│  Queue/   │────────>│ Trade Engine     │
│              │ enqueue │  *.json   │ dequeue │ Worker + MT5     │
└──────────────┘         └───────────┘         └──────────────────┘
```

## Yêu Cầu

### 1. Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. MetaTrader 5

- Cài đặt MT5
- Đăng nhập vào tài khoản trading
- Đảm bảo MT5 đang chạy và đã login

### 3. Telegram Bot Token

Tạo bot qua [@BotFather](https://t.me/botfather) và lấy token.

## Cấu Hình

### Environment Variables

Tạo file `.env`:

```bash
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token_here

# MT5 Connection (optional - có thể login manual trong MT5)
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=broker-server

# Queue Settings (optional)
QUEUE_DIR=queue
DB_PATH=trading_bot.db
POLL_INTERVAL=1.0
```

**Lưu ý:** Nếu MT5 đã login sẵn, không cần set `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`.

## Khởi Động Hệ Thống

### Bước 1: Khởi động MT5

```bash
# Mở MetaTrader 5 và đăng nhập tài khoản
```

### Bước 2: Khởi động Telegram Bot

```bash
# Terminal 1
export BOT_TOKEN="your_bot_token"
python3 bot/telegram_bot.py
```

Output:

```
INFO - Bot started
INFO - Start polling
```

### Bước 3: Khởi động Trade Engine Worker

```bash
# Terminal 2
python3 engine/trade_engine_worker.py
```

Output:

```
============================================================
Trade Engine Worker Starting
============================================================
INFO - Database connected
INFO - Connected to MT5 - Account: 12345678, Balance: 10000.0 USD
INFO - Worker started - Polling interval: 1.0s
INFO - Monitoring queue: /path/to/queue
INFO - Press Ctrl+C to stop
------------------------------------------------------------
```

## Sử Dụng Bot

### 1. Khởi động bot trong Telegram

```
/start
```

### 2. Đặt lệnh LIMIT BUY

```
/limitbuy
```

Bot sẽ hỏi lần lượt:

1. Symbol (VD: XAU)
2. Entry price (VD: 2650)
3. Stop Loss (VD: 2640)
4. Take Profit (VD: 2670)
5. Emotion (chọn từ buttons)
6. Setup (chọn từ danh sách)
7. Chart URL (hoặc skip)
8. Confirm

### 3. Đặt lệnh LIMIT SELL

```
/limitsell
```

Tương tự như limit buy.

## Luồng Xử Lý

1. **User gửi lệnh** → Bot tạo trade command
2. **Bot enqueue** → Ghi file JSON vào `queue/`
3. **Worker nhận** → Đọc file từ queue
4. **Worker thực thi** → Gọi MT5 API
5. **MT5 đặt lệnh** → Trả về ticket number
6. **Worker cập nhật** → Ghi kết quả vào database
7. **User nhận thông báo** → Bot hiển thị ticket

## Ví Dụ Queue File

File: `queue/20260124_153045_a1b2c3d4.json`

```json
{
  "queue_id": "20260124_153045_a1b2c3d4",
  "queued_at": "2026-01-24T15:30:45.123456",
  "status": "pending",
  "command": {
    "trade_id": 123,
    "user_id": 1,
    "account_id": 1,
    "order_type": "LIMIT_BUY",
    "symbol": "XAUUSD",
    "entry_price": 2650.0,
    "sl_price": 2640.0,
    "tp_price": 2670.0,
    "volume": 0.1,
    "risk_usd": 100.0,
    "emotion": "calm",
    "setup_code": "FZ1",
    "chart_url": null,
    "timestamp": "2026-01-24T15:30:45.123456Z"
  }
}
```

## Monitor Hệ Thống

### Xem Queue

```bash
# Đếm số lệnh pending
ls -1 queue/*.json 2>/dev/null | wc -l

# Xem file mới nhất
ls -t queue/*.json 2>/dev/null | head -1 | xargs cat | jq .

# Monitor real-time
watch -n 1 'ls -lh queue/ 2>/dev/null | tail -10'
```

### Xem Logs

```bash
# Bot logs (Terminal 1)
# Worker logs (Terminal 2)

# Hoặc redirect vào file
python3 engine/trade_engine_worker.py >> worker.log 2>&1 &
tail -f worker.log
```

### Kiểm tra Database

```bash
sqlite3 trading_bot.db

-- Xem trades gần đây
SELECT id, symbol, order_type, status, mt5_ticket, created_at
FROM trades
ORDER BY created_at DESC
LIMIT 10;

-- Xem trades đang pending
SELECT * FROM trades WHERE status = 'pending';

-- Xem trades đã filled
SELECT * FROM trades WHERE status = 'filled';
```

## Troubleshooting

### Worker không connect được MT5

**Lỗi:** `Failed to connect to MT5`

**Giải pháp:**

1. Đảm bảo MT5 đang chạy
2. Đảm bảo đã login vào tài khoản
3. Nếu dùng env vars, check `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`

### Lệnh không được thực thi

**Kiểm tra:**

1. Worker có đang chạy không?
2. Xem queue có file pending không?
3. Check worker logs xem có lỗi gì

```bash
# Xem pending commands
ls -l queue/

# Manual dequeue để test
python3 -c "
from engine.command_queue import CommandQueue
queue = CommandQueue()
pending = queue.list_pending()
print(f'Pending: {pending}')
if pending:
    cmd = queue.dequeue(pending[0])
    print(cmd)
"
```

### Symbol không tồn tại

**Lỗi:** `Symbol XAUUSD not found in MT5`

**Giải pháp:**

1. Kiểm tra symbol name đúng chưa
2. Add symbol vào Market Watch trong MT5
3. Kiểm tra prefix/suffix trong settings

### Volume calculation lỗi

**Kiểm tra:**

1. Risk amount có hợp lý không?
2. Stop loss distance có quá nhỏ không?
3. Check broker min/max volume

## Dừng Hệ Thống

### Dừng Worker (Graceful)

```bash
# Nhấn Ctrl+C trong terminal worker
# Hoặc
pkill -SIGTERM -f trade_engine_worker.py
```

Worker sẽ:

1. Đợi xử lý xong lệnh hiện tại
2. Ngắt kết nối MT5
3. Đóng database
4. Thoát

### Dừng Bot

```bash
# Nhấn Ctrl+C trong terminal bot
```

### Xóa Queue (Emergency)

```bash
# XÓA TẤT CẢ pending commands
rm -f queue/*.json

# Hoặc dùng code
python3 -c "
from engine.command_queue import CommandQueue
queue = CommandQueue()
queue.clear_all()
print('Queue cleared')
"
```

## Production Deployment

### Chạy như Service (systemd)

```bash
# /etc/systemd/system/trading-bot.service
[Unit]
Description=Telegram Trading Bot
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/path/to/bot
Environment="BOT_TOKEN=your_token"
ExecStart=/usr/bin/python3 bot/telegram_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# /etc/systemd/system/trade-engine.service
[Unit]
Description=Trade Engine Worker
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 engine/trade_engine_worker.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable và start:

```bash
sudo systemctl enable trading-bot trade-engine
sudo systemctl start trading-bot trade-engine
sudo systemctl status trading-bot trade-engine
```

### Chạy với Docker (Future)

```dockerfile
# Dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "engine/trade_engine_worker.py"]
```

## Backup & Recovery

### Backup Database

```bash
# Backup hàng ngày
cp trading_bot.db trading_bot_$(date +%Y%m%d).db

# Hoặc dùng sqlite dump
sqlite3 trading_bot.db .dump > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
# Từ backup file
cp trading_bot_20260124.db trading_bot.db

# Từ SQL dump
sqlite3 trading_bot.db < backup_20260124.sql
```

## Câu Hỏi Thường Gặp

**Q: Có thể chạy nhiều worker không?**
A: Có, nhưng cần cẩn thận với race condition. Nên dùng 1 worker cho đơn giản.

**Q: Queue file bị mất thì sao?**
A: Trade vẫn có trong database với status 'pending', có thể retry manual.

**Q: Làm sao biết lệnh đã vào MT5?**
A: Check database field `mt5_ticket` và `status = 'filled'`.

**Q: Worker crash giữa chừng?**
A: Pending commands vẫn trong queue, khởi động lại worker sẽ xử lý tiếp.

---

**Cần hỗ trợ?** Check logs và error messages, hoặc xem file `QUEUE_SYSTEM.md` để hiểu chi tiết hơn.
