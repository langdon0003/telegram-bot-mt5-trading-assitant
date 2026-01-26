# Quick Start Guide

Get your Telegram MT5 Trading Assistant running in 5 minutes.

## Prerequisites

- Python 3.10+
- Windows VPS (for MT5)
- MetaTrader 5 installed
- Telegram account

## Step 1: Create Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Follow prompts to name your bot
4. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 2: Install Project

```bash
# Clone or download project
cd telegram-bot-mt5-trading-assitant

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# TELEGRAM_BOT_TOKEN=your_token_here
# MT5_LOGIN=your_account_number
# MT5_PASSWORD=your_password
# MT5_SERVER=your_broker_server
```

## Step 4: Initialize Database

```bash
python -c "from database.db_manager import DatabaseManager; db = DatabaseManager(); db.connect(); db.initialize_schema(); print('Database initialized!')"
```

## Step 5: Run Tests (Optional but Recommended)

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest tests/ -v

# You should see: 42 passed
```

## Step 6: Run the Bot

**Important:** Make sure MetaTrader 5 is running and logged in first!

```bash
python3 run_bot.py
```

You should see:

```
✅ Loaded .env file
🤖 Starting Telegram Trading Bot...
📊 Database: trading_bot.db
INFO - Bot started
INFO - MT5 connected successfully
```

## Step 7: Test in Telegram

1. Open Telegram
2. Search for your bot by username
3. Send `/start`
4. You should see welcome message with commands

## Step 8: Configure Your Settings

In Telegram, send:

```
/start
```

Then add your first setup:

```python
# In Python shell or create a script:
from database.db_manager import DatabaseManager

db = DatabaseManager()
db.connect()

# Get your user ID (from /start command, check logs)
user = db.get_user_by_telegram_id(YOUR_TELEGRAM_ID)

# Add setups
db.create_setup(
    user_id=user['id'],
    setup_code='FZ1',
    setup_name='Fair Value Zone 1',
    description='Entry at first FVZ'
)

db.create_setup(
    user_id=user['id'],
    setup_code='TLP1',
    setup_name='Trendline Pattern 1',
    description='Break and retest'
)

print("Setups created!")
```

## Step 9: Place Your First Trade

In Telegram:

```
/limitbuy
```

Follow the prompts:

1. Symbol: `XAU` (or press Enter for default)
2. Entry: `2000`
3. Stop Loss: `1995` (must be < 2000 for BUY)
4. Take Profit: `2015`
5. Select emotion: Click "Calm"
6. Select setup: Click "FZ1"
7. Chart URL: Paste TradingView URL or type `skip`
8. Confirm: Click "✅ Confirm"

## Step 10: Verify MT5 Connection

The bot executes trades directly in MT5. To test connection:

```bash
python test_mt5_connection.py
```

## Common Issues

### Issue: "Bot token invalid"

**Solution**: Check `.env` file, ensure token is correct (no quotes, no spaces)

### Issue: "ModuleNotFoundError: No module named 'telegram'"

**Solution**: `pip install python-telegram-bot`

### Issue: "No module named 'MetaTrader5'"

**Solution**: `pip install MetaTrader5` (Windows only)

### Issue: "Database locked"

**Solution**: Close any other connections to the database file

### Issue: "No setups configured"

**Solution**: Add setups using the Python script in Step 8

## Next Steps

### 1. Customize Risk Settings

```python
from database.db_manager import DatabaseManager

db = DatabaseManager()
db.connect()

user = db.get_user_by_telegram_id(YOUR_TELEGRAM_ID)

# Set fixed USD risk
db.update_user_settings(
    user_id=user['id'],
    risk_type='fixed_usd',
    risk_value=100.0
)

# Or set percent risk
db.update_user_settings(
    user_id=user['id'],
    risk_type='percent',
    risk_value=0.01  # 1%
)
```

### 2. Customize Symbol Settings

```python
# For broker with prefix
db.update_user_settings(
    user_id=user['id'],
    symbol_prefix='BROKER.'
)

# For broker with suffix
db.update_user_settings(
    user_id=user['id'],
    symbol_suffix='m'
)

# Both
db.update_user_settings(
    user_id=user['id'],
    symbol_prefix='IC.',
    symbol_suffix='.pro'
)
```

### 3. Add More Setups

```python
db.create_setup(user['id'], 'FZ2', 'Fair Value Zone 2')
db.create_setup(user['id'], 'TLP2', 'Trendline Pattern 2')
db.create_setup(user['id'], 'BOS', 'Break of Structure')
db.create_setup(user['id'], 'OB', 'Order Block')
```

### 4. View Your Trades

```python
# Query trades
cursor = db.conn.cursor()
cursor.execute("""
    SELECT * FROM trades
    WHERE user_id = ?
    ORDER BY created_at DESC
    LIMIT 10
""", (user['id'],))

trades = cursor.fetchall()
for trade in trades:
    print(dict(trade))
```

## Production Deployment

### 1. Use Environment Variables

Never hardcode credentials. Always use `.env` file.

### 2. Run as Service (Linux/Windows)

**Linux (systemd):**

```bash
sudo nano /etc/systemd/system/telegram-trading-bot.service
```

```ini
[Unit]
Description=Telegram Trading Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/telegram-bot-mt5-trading-assitant
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 bot/telegram_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable telegram-trading-bot
sudo systemctl start telegram-trading-bot
sudo systemctl status telegram-trading-bot
```

**Windows (Task Scheduler):**

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: Start a program
5. Program: `python.exe`
6. Arguments: `bot/telegram_bot.py`
7. Start in: `C:\path\to\project`

### 3. Logging

Add to bot code:

```python
import logging
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 4. Database Backup

```bash
# Daily backup cron job (Linux)
0 2 * * * cp /path/to/trading_bot.db /path/to/backups/trading_bot_$(date +\%Y\%m\%d).db
```

### 5. Monitor Bot

```bash
# Check if bot is running
ps aux | grep telegram_bot.py

# View logs
tail -f bot.log

# Check database size
ls -lh trading_bot.db
```

## Resources

- **Documentation**: See `README.md`
- **Architecture**: See `PROJECT_OVERVIEW.md`
- **TDD Approach**: See `TDD_SUMMARY.md`
- **Support**: Create issue on GitHub

## Tips

1. **Test on Demo Account First**: Always test with demo account before live trading
2. **Start Small**: Use small risk amounts until confident
3. **Review Trades**: Regularly analyze your emotions and setups
4. **Backup Database**: Your trade journal is valuable data
5. **Monitor Logs**: Check logs for errors or issues

## Security Checklist

- [ ] Bot token in `.env` (not in code)
- [ ] `.env` in `.gitignore`
- [ ] MT5 credentials in `.env`
- [ ] Database file permissions (not world-readable)
- [ ] Regular backups configured
- [ ] SSL/TLS for any API endpoints (future)

## Success!

You're now ready to use the Telegram MT5 Trading Assistant!

Remember: This tool enforces discipline. Every trade requires:

- ✅ Valid SL position
- ✅ Emotion awareness
- ✅ Setup selection
- ✅ Conscious confirmation

Trade with discipline. Good luck! 🚀
