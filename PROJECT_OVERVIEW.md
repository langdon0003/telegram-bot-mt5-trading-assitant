# Project Overview - Telegram MT5 Trading Assistant

## 📋 Project Summary

A production-grade Telegram bot that enables manual trading into MetaTrader 5 with strict risk management, trade validation, and psychological journaling.

**Key Feature**: This is NOT an auto-trading or signal bot. It's a disciplined trading assistant that enforces risk rules and logs your trading psychology.

## 🎯 Core Requirements Met

✅ **Separation of Concerns**: Bot and Trade Engine are completely separate
✅ **Risk Management**: Fixed USD or % balance risk with volume calculation
✅ **Trade Validation**: SL position enforced (BUY: SL < entry, SELL: SL > entry)
✅ **Psychology Tracking**: Mandatory emotion selection before each trade
✅ **Setup Management**: User-defined trade setups with quick selection
✅ **Symbol Resolution**: Dynamic building (prefix + base + "USD" + suffix)
✅ **Database Schema**: SQLite with proper foreign keys and constraints
✅ **TDD Approach**: 42 tests written BEFORE implementation

## 📁 Project Structure

```
telegram-bot-mt5-trading-assitant/
│
├── bot/                                 # Telegram Bot (NEVER talks to MT5 directly)
│   ├── __init__.py
│   ├── telegram_bot.py                  # Main bot with conversation flow
│   └── trade_command_builder.py         # Builds JSON trade commands
│
├── engine/                              # Trade Engine (MT5 interaction)
│   ├── __init__.py
│   ├── mt5_adapter.py                   # MT5 API wrapper & trade execution
│   ├── risk_calculator.py               # Volume calculation from risk
│   ├── symbol_resolver.py               # Dynamic symbol building
│   └── trade_validator.py               # SL validation & R:R calculation
│
├── database/                            # Database layer
│   ├── schema.sql                       # SQLite schema (5 tables)
│   └── db_manager.py                    # Database operations
│
├── tests/                               # TDD test suite (42 tests)
│   ├── __init__.py
│   ├── test_risk_calculator.py          # 9 tests
│   ├── test_symbol_resolver.py          # 9 tests
│   ├── test_trade_validator.py          # 13 tests
│   └── test_trade_command.py            # 11 tests
│
├── README.md                            # User documentation
├── TDD_SUMMARY.md                       # TDD workflow documentation
├── PROJECT_OVERVIEW.md                  # This file
├── requirements.txt                     # Python dependencies
├── .env.example                         # Environment variables template
├── .gitignore                           # Git ignore rules
└── example_trade_command.json           # Sample trade command JSON
```

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         User (Telegram)                       │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT LAYER                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Conversation Handler (State Machine)                  │  │
│  │  - /limitbuy, /limitsell commands                     │  │
│  │  - Symbol → Entry → SL → TP → Emotion → Setup → URL  │  │
│  │  - Validation & Preview                               │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Components                                            │  │
│  │  - SymbolResolver (build MT5 symbol)                  │  │
│  │  - TradeValidator (validate SL position)              │  │
│  │  - RiskCalculator (calculate volume)                  │  │
│  │  - TradeCommandBuilder (build JSON)                   │  │
│  └────────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────┘
                         │ JSON Trade Command
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                   TRADE ENGINE LAYER                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  MT5 Adapter                                           │  │
│  │  - Connect to MT5                                      │  │
│  │  - Get symbol info (pip value, min/max volume)        │  │
│  │  - Recalculate volume with actual MT5 data            │  │
│  │  - Validate trade parameters                          │  │
│  │  - Place LIMIT order                                  │  │
│  │  - Return execution result                            │  │
│  └────────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                      MetaTrader 5                             │
│  - Order execution                                            │
│  - Symbol information                                         │
│  - Account information                                        │
└──────────────────────────────────────────────────────────────┘

                         ┌─────────────────┐
                         │  SQLite Database │
                         │  - Users         │
                         │  - Settings      │
                         │  - Setups        │
                         │  - Trades        │
                         │  - Accounts      │
                         └─────────────────┘
```

## 📊 Database Schema

### Tables

1. **users** - Telegram users
   - id, telegram_id, username, first_name, last_name

2. **user_settings** - Per-user configuration
   - default_symbol_base (XAU, EUR, GBP, etc.)
   - symbol_prefix, symbol_suffix
   - risk_type (fixed_usd | percent)
   - risk_value
   - default_account_id

3. **accounts** - MT5 trading accounts
   - account_number, broker_name, is_active

4. **setups** - User-defined trade setups
   - setup_code (e.g., "FZ1", "TLP1")
   - setup_name, description

5. **trades** - Complete trade journal
   - Trade params: symbol, order_type, entry, sl, tp, volume
   - Risk: risk_usd, rr
   - Psychology: emotion, setup_code, chart_url
   - Execution: mt5_ticket, mt5_open_price, mt5_close_price, mt5_profit
   - Status: pending, filled, closed, cancelled, failed

## 🔄 Trade Flow (User Experience)

```
1. User: /limitbuy
   Bot: "Enter symbol base (default: XAU):"

2. User: XAU
   Bot: "Symbol: XAUUSD. Enter entry price:"

3. User: 2000
   Bot: "Entry: 2000. Enter stop loss (must be < 2000):"

4. User: 1995
   Bot: "Stop Loss: 1995. Enter take profit:"

5. User: 2015
   Bot: "📊 Trade Preview
        Symbol: XAUUSD
        Type: LIMIT_BUY
        Entry: 2000
        SL: 1995
        TP: 2015

        💰 Risk: $50
        📦 Volume: 10.0 lots
        📈 R:R: 3.0

        How are you feeling?"
   [Inline buttons: Calm | Confident | FOMO | Stressed | Revenge]

6. User: [Clicks "Calm"]
   Bot: "Emotion: calm. Select your setup:"
   [Inline buttons: FZ1 | FZ2 | TLP1 | TLP2 | ...]

7. User: [Clicks "FZ1"]
   Bot: "Setup: FZ1. Enter TradingView chart URL (or type 'skip'):"

8. User: https://www.tradingview.com/x/abc123/
   Bot: "📋 Final Confirmation
        Symbol: XAUUSD
        Type: LIMIT_BUY
        Entry: 2000
        SL: 1995
        TP: 2015
        Volume: 10.0 lots
        Risk: $50
        R:R: 3.0
        Emotion: calm
        Setup: FZ1
        Chart: https://www.tradingview.com/x/abc123/

        Execute this trade?"
   [Inline buttons: ✅ Confirm | ❌ Cancel]

9. User: [Clicks "✅ Confirm"]
   Bot: "✅ Trade command sent!
        Trade ID: 42
        Waiting for MT5 execution..."

10. Trade Engine executes in MT5 (separate process)
    Bot: "🎯 Trade executed!
         Ticket: 123456789
         Entry: 2000.00
         Volume: 10.0 lots"
```

## 🧪 TDD Approach

### Test-Driven Development Flow

```
PHASE 1: Define Behavior
├─ Risk Calculator: Volume from risk parameters
├─ Symbol Resolver: Build symbol from components
├─ Trade Validator: SL position validation
└─ Trade Command: JSON structure validation

PHASE 2: Write Tests BEFORE Implementation
├─ test_risk_calculator.py (9 tests)
├─ test_symbol_resolver.py (9 tests)
├─ test_trade_validator.py (13 tests)
└─ test_trade_command.py (11 tests)
Total: 42 tests

PHASE 3: Run Tests (All Fail - Expected!)
└─ ModuleNotFoundError: Implementation doesn't exist yet

PHASE 4: Write MINIMAL Implementation
├─ risk_calculator.py
├─ symbol_resolver.py
├─ trade_validator.py
└─ trade_command_builder.py

PHASE 5: Run Tests Again
└─ All 42 tests pass! ✅
```

### Test Coverage

- **Risk Calculator**: 9 tests
  - Fixed USD risk, percent risk, min/max volume, step size, edge cases

- **Symbol Resolver**: 9 tests
  - Prefix only, suffix only, both, neither, case preservation, validation

- **Trade Validator**: 13 tests
  - BUY SL validation, SELL SL validation, R:R calculation, full validation

- **Trade Command**: 11 tests
  - JSON structure, validation (emotion, order_type, volume, risk), serialization

## 🔑 Key Features

### 1. Risk Management
```python
# Fixed USD risk
risk_usd = 100.0
volume = risk_calculator.calculate_volume(
    risk_usd=100.0,
    entry_price=2000.0,
    sl_price=1995.0,
    pip_value=1.0,
    tick_size=0.01,
    volume_step=0.01
)
# Result: 10.0 lots (100 / (5 * 1.0) = 20, rounded to 10.0)

# Percent balance risk
balance = 10000.0
risk_percent = 0.01  # 1%
risk_usd = balance * risk_percent  # $100
```

### 2. Symbol Resolution
```python
# Example 1: Standard symbol
symbol = resolver.resolve(base="XAU", prefix="", suffix="")
# Result: "XAUUSD"

# Example 2: Broker with prefix
symbol = resolver.resolve(base="XAU", prefix="BROKER.", suffix="")
# Result: "BROKER.XAUUSD"

# Example 3: Broker with suffix
symbol = resolver.resolve(base="XAU", prefix="", suffix="m")
# Result: "XAUUSDm"

# Example 4: Both
symbol = resolver.resolve(base="EUR", prefix="IC.", suffix=".pro")
# Result: "IC.EURUSD.pro"
```

### 3. Trade Validation
```python
# LIMIT BUY: SL MUST be < entry
validator.validate_sl_position(
    order_type="LIMIT_BUY",
    entry_price=2000.0,
    sl_price=1995.0  # ✅ Valid (1995 < 2000)
)

validator.validate_sl_position(
    order_type="LIMIT_BUY",
    entry_price=2000.0,
    sl_price=2005.0  # ❌ Invalid (2005 > 2000)
)

# LIMIT SELL: SL MUST be > entry
validator.validate_sl_position(
    order_type="LIMIT_SELL",
    entry_price=2000.0,
    sl_price=2005.0  # ✅ Valid (2005 > 2000)
)
```

### 4. Psychology Tracking
Every trade MUST have:
- **Emotion**: calm, confident, fomo, stressed, revenge
- **Setup**: User-defined setup code (e.g., "FZ1", "TLP1")
- **Chart URL**: Optional TradingView chart link

This enables journal analysis:
```sql
-- Which emotion has best win rate?
SELECT emotion, AVG(CASE WHEN mt5_profit > 0 THEN 1 ELSE 0 END) as win_rate
FROM trades
WHERE status = 'closed'
GROUP BY emotion;

-- Which setup performs best?
SELECT setup_code, AVG(mt5_profit) as avg_profit
FROM trades
WHERE status = 'closed'
GROUP BY setup_code;
```

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Initialize Database
```bash
python -c "from database.db_manager import DatabaseManager; db = DatabaseManager(); db.connect(); db.initialize_schema()"
```

### 4. Run Tests
```bash
pytest tests/ -v
```

### 5. Start Bot
```bash
python bot/telegram_bot.py
```

### 6. Start Trade Engine (separate terminal)
```bash
python engine/mt5_adapter.py
```

## 📈 Future Enhancements

### Phase 2 Features
- [ ] Queue system (Redis/RabbitMQ) between Bot and Engine
- [ ] REST API for Trade Engine
- [ ] Trade modification commands (/modify, /close)
- [ ] Position monitoring with alerts

### Phase 3 Features
- [ ] Web dashboard for analytics
- [ ] Multi-account support
- [ ] Risk per day/week limits
- [ ] Backtesting integration

### Phase 4 Features
- [ ] Machine learning on emotion/setup performance
- [ ] Automated journal reports (daily/weekly)
- [ ] Trade screenshot capture
- [ ] Integration with trading journals (Edgewonk, etc.)

## ⚠️ Important Notes

### Security
- NEVER commit `.env` file
- Use environment variables for secrets
- Validate all user inputs
- Use parameterized SQL queries

### Trading Discipline
- Bot enforces SL position rules
- No trade without emotion selection
- No trade without setup selection
- Risk calculated before execution

### Testing
- All core logic has unit tests
- Run tests before deployment
- Add tests for new features FIRST (TDD)

### Database
- Use foreign keys for data integrity
- Set up proper indexes for performance
- Regular backups recommended
- Can migrate to PostgreSQL easily later

## 📝 Development Workflow

When adding new features:

1. **Write test FIRST** (TDD)
2. Run test (it should fail)
3. Write MINIMAL code to pass test
4. Refactor if needed
5. Update documentation
6. Commit with clear message

Example:
```bash
# 1. Write test
vim tests/test_new_feature.py

# 2. Run test (should fail)
pytest tests/test_new_feature.py -v

# 3. Write implementation
vim bot/new_feature.py

# 4. Run test (should pass)
pytest tests/test_new_feature.py -v

# 5. Commit
git add tests/test_new_feature.py bot/new_feature.py
git commit -m "Add new feature with TDD approach"
```

## 🎓 Learning Resources

- **python-telegram-bot**: https://python-telegram-bot.org/
- **MetaTrader5 Python**: https://www.mql5.com/en/docs/python_metatrader5
- **TDD**: https://testdriven.io/
- **Risk Management**: "The Complete Guide to Position Sizing" by Van Tharp

## 📄 License

Proprietary - All rights reserved

## 👨‍💻 Author

Built with strict TDD methodology for production trading.

**Remember**: This is a trading discipline tool, not an autopilot. Every trade requires your conscious decision and emotional awareness.
