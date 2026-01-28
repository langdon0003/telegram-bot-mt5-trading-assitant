# Multiple MT5 Instances - Configuration Guide

## Problem

**MetaTrader5 Python API connects to ONLY ONE terminal at a time.**

When you have **multiple MT5 terminals open** (e.g., 3 different brokers):
- ❌ Bot connects to the **first terminal found**
- ❌ Cannot control which terminal it connects to
- ❌ May place orders on the **wrong account**
- ❌ Unpredictable behavior

## Risk

```
You have 3 MT5 terminals open:
1. ICMarkets - Account 12345 (Real - $10,000)
2. XM - Account 67890 (Demo - $1,000)
3. Exness - Account 11111 (Real - $50,000)

Bot may connect to ANY of these!
→ Orders may go to wrong account
→ SERIOUS FINANCIAL RISK
```

## Solution

### Option 1: Close Other Terminals (Recommended)

**✅ Best practice: Only open the MT5 terminal you want to trade with.**

```
1. Close ALL MT5 terminals
2. Open ONLY the one you want to use
3. Login to correct account
4. Start bot
```

This is the **safest and simplest** solution.

### Option 2: Specify MT5 Path

If you MUST keep multiple MT5 terminals open, specify which one to use:

**Step 1: Find MT5 Terminal Path**

Common paths:
```
C:\Program Files\MetaTrader 5\terminal64.exe
C:\Program Files\ICMarkets - MetaTrader 5\terminal64.exe
C:\Program Files\XM Global MT5\terminal64.exe
C:\Program Files\Exness\terminal64.exe
```

**Step 2: Configure .env**

Add `MT5_PATH` to your `.env` file:

```ini
# .env file

# Specify FULL path to the MT5 terminal you want to use
MT5_PATH=C:\Program Files\ICMarkets - MetaTrader 5\terminal64.exe

# Also specify account for verification
MT5_LOGIN=12345
MT5_PASSWORD=yourpassword
MT5_SERVER=ICMarkets-Demo01
```

**Step 3: Restart Bot**

```bash
# Stop bot (Ctrl+C)
# Start bot
python run_bot.py
```

Bot will now connect to the specific terminal!

## Verification

After starting bot, check logs:

### ✅ Good - Correct account:

```
INFO - Initializing MT5 with specific path: C:\Program Files\ICMarkets\terminal64.exe
INFO - MT5 initialized successfully
INFO - ✅ MT5 logged in successfully with account 12345
INFO - ✅ Connected to account: 12345
INFO -    Server: ICMarkets-Demo01
INFO -    Balance: $10000.00
INFO - MT5 connected successfully
```

### ⚠️ Warning - Wrong account:

```
INFO - MT5 initialized successfully
INFO - ✅ MT5 logged in successfully with account 12345
WARNING - ============================================================
WARNING - ⚠️  WARNING: Connected to different account!
WARNING -    Expected: 12345
WARNING -    Got: 67890
WARNING - ============================================================
WARNING - If you have multiple MT5 terminals open,
WARNING - set MT5_PATH in .env to specify which terminal to use
```

**Action:** Set `MT5_PATH` in `.env` file!

## How It Works

### Without MT5_PATH (Unpredictable):

```python
mt5.initialize()  # Connects to FIRST terminal found
# Could be ANY of your open terminals!
```

### With MT5_PATH (Controlled):

```python
mt5.initialize(path="C:\\Program Files\\ICMarkets\\terminal64.exe")
# Connects to SPECIFIC terminal
# You control which account is used
```

### Account Verification:

After connection, bot checks:
```python
account_info = mt5.account_info()
if account_info.login != expected_login:
    # WARNING: Connected to wrong account!
```

## Testing

### Test 1: Single Terminal (Should Work)

```bash
# Close all MT5 terminals
# Open ONLY one MT5 terminal
# Start bot
python run_bot.py

# Check logs - should connect successfully
```

### Test 2: Multiple Terminals Without Path (Will Warn)

```bash
# Open 3 MT5 terminals
# DON'T set MT5_PATH in .env
# Start bot
python run_bot.py

# Check logs - may connect to wrong account
# You'll see warning if account doesn't match
```

### Test 3: Multiple Terminals With Path (Should Work)

```bash
# Open 3 MT5 terminals
# Set MT5_PATH in .env
# Start bot
python run_bot.py

# Check logs - should connect to correct terminal
# No warning if account matches
```

## Best Practices

### ✅ DO:

1. **Use only ONE MT5 terminal** while bot is running
2. **Set MT5_PATH** if you must use multiple terminals
3. **Verify account** in logs after bot starts
4. **Set MT5_LOGIN** for verification
5. **Test with demo account** first

### ❌ DON'T:

1. **Run bot** with multiple terminals without MT5_PATH
2. **Assume** bot connects to the right account
3. **Skip** log verification
4. **Use bot** on live account without testing
5. **Open/close terminals** while bot is running

## Troubleshooting

### Problem: Bot connects to wrong account

**Solution:**
1. Set `MT5_PATH` in `.env`
2. Set `MT5_LOGIN` for verification
3. Restart bot
4. Check logs

### Problem: "MT5 initialize failed"

**Possible causes:**
- Wrong path to terminal64.exe
- Terminal not running
- Permission issues

**Solution:**
1. Verify path is correct
2. Terminal is open and running
3. Try with administrator privileges

### Problem: "Connected to different account" warning

**Cause:** Bot connected to different terminal than expected

**Solution:**
1. Close unwanted terminals
2. OR set correct MT5_PATH
3. Restart bot

### Problem: Multiple terminals cause IPC timeout

**Cause:** Multiple terminals conflict

**Solution:**
1. Close extra terminals
2. Use ONLY one terminal per bot instance
3. Restart both terminal and bot

## Technical Details

### MetaTrader5 API Limitation

```python
# Python MetaTrader5 API limitation:
# Can only connect to ONE terminal at a time
# Without path: connects to FIRST terminal found
# Order is unpredictable!

mt5.initialize()  # Connects to first terminal
# No way to specify which terminal without path parameter
```

### Path Parameter

```python
# Solution: Specify terminal path
mt5.initialize(path="C:\\path\\to\\terminal64.exe")
# Now connects to SPECIFIC terminal
# Full control over which account
```

### Process Detection

When you open multiple MT5 terminals:
```
Process ID 1234: terminal64.exe (ICMarkets)
Process ID 5678: terminal64.exe (XM)
Process ID 9012: terminal64.exe (Exness)
```

Without path, API picks one randomly (usually first by PID).
With path, API connects to exact process.

## Environment Variables

```ini
# Required for account verification
MT5_LOGIN=12345

# Required ONLY with multiple terminals
MT5_PATH=C:\Program Files\Broker\terminal64.exe

# Optional for auto-login
MT5_PASSWORD=yourpassword
MT5_SERVER=BrokerServer-Demo01
```

## FAQ

**Q: Can I run bot with multiple MT5 terminals open?**
A: Yes, but you MUST set MT5_PATH to specify which terminal.

**Q: What happens if I don't set MT5_PATH with multiple terminals?**
A: Bot connects to first terminal found (unpredictable). May trade wrong account!

**Q: Can I switch between accounts without restarting?**
A: No. Change MT5_PATH in .env and restart bot.

**Q: Will bot warn me if it connects to wrong account?**
A: Yes! Check logs for warning message.

**Q: Is it safe to use multiple terminals?**
A: Only if you set MT5_PATH correctly and verify logs.

**Q: What's the safest setup?**
A: ONE terminal, ONE account, NO MT5_PATH needed.

## Summary

| Scenario | MT5_PATH | Safe? | Notes |
|----------|----------|-------|-------|
| 1 terminal open | Not needed | ✅ Yes | Safest setup |
| Multiple terminals, no path | Not set | ❌ NO | Unpredictable! |
| Multiple terminals, path set | Set correctly | ✅ Yes | Verify logs |
| Multiple terminals, wrong path | Wrong path | ❌ NO | Will fail |

**Recommendation: Use only ONE MT5 terminal while bot runs.**

## Example .env Configurations

### Safe Setup (One Terminal):

```ini
TELEGRAM_BOT_TOKEN=your_token
MT5_LOGIN=12345
MT5_PASSWORD=password
MT5_SERVER=Broker-Demo01
# MT5_PATH not needed - only one terminal open
```

### Multi-Terminal Setup (Advanced):

```ini
TELEGRAM_BOT_TOKEN=your_token
MT5_LOGIN=12345
MT5_PASSWORD=password
MT5_SERVER=ICMarkets-Demo01

# CRITICAL: Specify which terminal to use
MT5_PATH=C:\Program Files\ICMarkets - MetaTrader 5\terminal64.exe
```

## Warning Signs

Watch for these in logs:

```
⚠️  WARNING: Connected to different account!
⚠️  No credentials provided, using existing MT5 session
⚠️  Failed with path: [path]
```

If you see these, **STOP** and fix configuration!

## Support

If you're still having issues:

1. Check logs for warnings
2. Verify MT5_PATH is correct
3. Test with one terminal only
4. Check [TROUBLESHOOTING_IPC_TIMEOUT.md](TROUBLESHOOTING_IPC_TIMEOUT.md)

**Stay safe: When in doubt, use ONE terminal!**
