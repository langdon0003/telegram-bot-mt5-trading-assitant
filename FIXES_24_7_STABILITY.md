# Các Bản Sửa Để Bot Chạy Ổn Định 24/7

## 🎯 MỤC TIÊU

Sửa tất cả vấn đề critical và high để bot có thể chạy liên tục 24/7 mà không bị treo, lag, hoặc crash.

---

## 1. FIX DATABASE CONNECTION LEAKS 🔴 CRITICAL

### Vấn đề:

`setup_commands.py` tạo DatabaseManager mới mỗi lần gọi function, gây leaks.

### Giải pháp:

#### A. Dùng shared database từ bot_data

**Sửa `bot/setup_commands.py`:**

```python
# BEFORE (❌ Wrong)
from database.db_manager import DatabaseManager

async def addsetup_save(update, context):
    db = DatabaseManager()
    db.connect()
    user = db.get_user_by_telegram_id(telegram_id)
    db.close()

# AFTER (✅ Correct)
async def addsetup_save(update, context):
    # Get shared DB instance from bot_data
    db = context.application.bot_data['db']
    user = db.get_user_by_telegram_id(telegram_id)
    # NO db.close() - connection is managed by main bot
```

**Áp dụng cho TẤT CẢ functions trong:**

- `bot/setup_commands.py` (8 chỗ)
- `bot/settings_commands.py` (5 chỗ)
- `bot/order_commands.py` (nếu có)

---

## 2. FIX SQLITE THREAD-SAFETY ⚠️ HIGH

### Vấn đề:

SQLite connection được share giữa nhiều async handlers, không thread-safe.

### Giải pháp: Connection Pooling

**Sửa `database/db_manager.py`:**

```python
import sqlite3
import threading
from pathlib import Path

class DatabaseManager:
    """Thread-safe database manager with connection pooling"""

    def __init__(self, db_path: str = "trading_bot.db"):
        self.db_path = db_path
        self._local = threading.local()

    def connect(self):
        """Get or create thread-local connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # Allow multi-thread
                timeout=30.0  # Wait up to 30s for lock
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    @property
    def conn(self):
        """Get current thread's connection"""
        return self.connect()

    def close(self):
        """Close current thread's connection"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
```

**Lợi ích:**

- Mỗi thread có connection riêng
- Không race condition
- Thread-safe hoàn toàn
- Timeout 30s tránh deadlock

---

## 3. ADD MT5 HEALTH CHECK ⚠️ HIGH

### Vấn đề:

MT5 disconnect mà bot không biết, không tự reconnect.

### Giải pháp: Background Health Check

**Sửa `bot/telegram_bot.py`:**

```python
from telegram.ext import Application
import asyncio

class TradingBot:
    def __init__(self, token: str, db_path: str = "trading_bot.db"):
        # ... existing code ...
        self._health_check_task = None

    async def mt5_health_check(self):
        """Background task to check MT5 connection every 60 seconds"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                if not self.mt5_adapter.is_connected():
                    logger.warning("🔴 MT5 disconnected! Attempting to reconnect...")

                    if self.mt5_adapter.connect():
                        logger.info("✅ MT5 reconnected successfully")
                    else:
                        logger.error("❌ MT5 reconnect failed")
                        # Optional: Send alert to admin

            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def start_health_check(self, application):
        """Start health check task"""
        self._health_check_task = asyncio.create_task(self.mt5_health_check())
        logger.info("✅ MT5 health check started")

    def run(self):
        app = Application.builder().token(self.token).post_init(self.setup_bot_menu).build()

        # Start health check
        app.post_init(self.start_health_check)

        # ... rest of existing code ...
```

**Lợi ích:**

- Auto-detect MT5 disconnect
- Auto-reconnect
- Giảm failed trades
- Không cần manual restart

---

## 4. ADD POLLING ERROR RECOVERY ⚠️ MEDIUM

### Vấn đề:

Network timeout → Bot crash và stop.

### Giải pháp: Retry Loop

**Sửa `run_bot.py`:**

```python
if __name__ == "__main__":
    # ... existing setup code ...

    print(f"🤖 Starting Telegram Trading Bot...")

    # Infinite retry loop
    retry_count = 0
    max_retries = 5

    while True:
        try:
            # Create and run bot
            bot = TradingBot(token=BOT_TOKEN, db_path=DB_PATH)

            logger.info("Starting bot...")
            bot.run()

            # If we get here, bot stopped gracefully
            break

        except KeyboardInterrupt:
            print("\n👋 Bot stopped by user")
            break

        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Bot error (attempt {retry_count}/{max_retries}): {e}")

            if retry_count >= max_retries:
                logger.critical("Max retries reached. Exiting.")
                break

            # Exponential backoff
            wait_time = min(2 ** retry_count, 300)  # Max 5 minutes
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
```

**Hoặc tốt hơn, dùng `run_polling()` với parameters:**

```python
def run(self):
    app = Application.builder().token(self.token).post_init(self.setup_bot_menu).build()

    # ... handlers ...

    logger.info("Bot started")

    # Run with auto-recovery
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        close_loop=False,
        stop_signals=None,  # Handle stop signals manually
        # Network timeouts
        pool_timeout=30,
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
    )
```

**Lợi ích:**

- Auto-retry khi network error
- Exponential backoff
- Không cần manual restart
- Bot chạy liên tục

---

## 5. ADD LOG ROTATION ⚠️ MEDIUM

### Vấn đề:

Log file tăng vô hạn, đầy disk.

### Giải pháp: RotatingFileHandler

**Sửa `bot/telegram_bot.py` và `engine/mt5_adapter.py`:**

```python
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    """Configure logging with rotation"""

    # Create logs directory
    os.makedirs("logs", exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File handler with rotation (10 MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(
        'logs/bot.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

# Call at start of run_bot.py
setup_logging()
```

**Lợi ích:**

- Log file max 10 MB
- Auto-rotate khi đầy
- Giữ 5 backups (50 MB total)
- Không đầy disk

---

## 6. FIX MEMORY LEAK IN CONTEXT.USER_DATA ⚠️ LOW

### Vấn đề:

Incomplete conversations giữ data mãi mãi.

### Giải pháp: Timeout và Cleanup

**Sửa conversation handlers:**

```python
limitbuy_handler = ConversationHandler(
    entry_points=[CommandHandler("limitbuy", self.limitbuy_start)],
    states={
        # ... existing states ...
    },
    fallbacks=[CommandHandler("cancel", self.cancel)],
    per_message=False,
    conversation_timeout=600,  # 10 minutes timeout
    name="limitbuy_conversation",
    persistent=False
)
```

**Add cleanup function:**

```python
async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation and cleanup"""

    # Clear all user_data
    context.user_data.clear()

    await update.message.reply_text(
        "❌ Operation cancelled.\n"
        "All data cleared."
    )

    return ConversationHandler.END
```

**Lợi ích:**

- Auto-timeout sau 10 phút
- Clear data khi cancel
- Không memory leak
- Better UX

---

## 7. ADD GRACEFUL SHUTDOWN (BONUS)

### Giải pháp: Cleanup on Exit

**Sửa `bot/telegram_bot.py`:**

```python
import signal
import sys

class TradingBot:
    def __init__(self, token: str, db_path: str = "trading_bot.db"):
        # ... existing code ...

        # Register shutdown handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")

        # Cleanup
        if self.mt5_adapter.connected:
            self.mt5_adapter.disconnect()

        if self.db.conn:
            self.db.close()

        logger.info("Cleanup complete, exiting...")
        sys.exit(0)
```

---

## 📋 CHECKLIST TRIỂN KHAI

### Phase 1: Critical Fixes (Làm ngay)

- [ ] Fix database connection leaks trong `setup_commands.py`
- [ ] Fix database connection leaks trong `settings_commands.py`
- [ ] Implement thread-safe database manager
- [ ] Test với nhiều users cùng lúc

### Phase 2: Important Fixes (Trong tuần)

- [ ] Add MT5 health check background task
- [ ] Test MT5 auto-reconnect
- [ ] Add polling error recovery
- [ ] Implement log rotation
- [ ] Test chạy 48 giờ liên tục

### Phase 3: Nice to Have

- [ ] Fix context.user_data memory leak
- [ ] Add graceful shutdown
- [ ] Add monitoring dashboard
- [ ] Setup systemd service (Linux) hoặc NSSM (Windows)

---

## 🧪 TESTING PLAN

### Test 1: Database Stress Test

```python
# Spam 100 commands trong 1 phút
for i in range(100):
    /addsetup
    /cancel
# Check memory usage
```

### Test 2: MT5 Disconnect Test

```
1. Start bot
2. Restart MT5
3. Wait 1 minute (health check)
4. Try /limitbuy
5. Should work (auto-reconnected)
```

### Test 3: 24h Endurance Test

```
1. Start bot
2. Monitor với htop/Task Manager
3. Check sau 6h, 12h, 24h
4. Memory không tăng
5. Bot vẫn responsive
```

### Test 4: Network Failure Test

```
1. Start bot
2. Disconnect internet 5 minutes
3. Reconnect internet
4. Bot should auto-recover
```

---

## 📊 KẾT QUẢ MONG ĐỢI

Sau khi áp dụng tất cả fixes:

| Metric             | Before | After    |
| ------------------ | ------ | -------- |
| Uptime             | 12-24h | 7+ days  |
| Memory leak        | ✅ Yes | ❌ No    |
| DB errors          | Có     | Không    |
| MT5 auto-reconnect | Không  | Có       |
| Crash recovery     | Manual | Auto     |
| Log size           | Vô hạn | Max 50MB |

---

## 🚀 PRODUCTION DEPLOYMENT

### Linux (Recommended):

```bash
# Create systemd service
sudo nano /etc/systemd/system/trading-bot.service
```

```ini
[Unit]
Description=Telegram Trading Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 run_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo systemctl status trading-bot
```

### Windows:

```powershell
# Use NSSM (Non-Sucking Service Manager)
nssm install TradingBot "C:\Python\python.exe" "C:\path\to\run_bot.py"
nssm set TradingBot AppDirectory "C:\path\to\bot"
nssm start TradingBot
```

---

## 📞 MONITORING & ALERTS

Cân nhắc thêm:

1. **Health endpoint**: HTTP server để check bot alive
2. **Telegram alerts**: Gửi message cho admin khi có lỗi
3. **Prometheus metrics**: Track performance
4. **Grafana dashboard**: Visualize metrics

Example alert:

```python
async def send_alert(message: str):
    """Send alert to admin"""
    ADMIN_CHAT_ID = os.getenv("ADMIN_TELEGRAM_ID")
    if ADMIN_CHAT_ID:
        await bot.send_message(ADMIN_CHAT_ID, f"🚨 ALERT: {message}")
```

Bạn muốn tôi implement những fix nào trước?
