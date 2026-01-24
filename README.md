# Telegram MT5 Trading Assistant

Production-grade Telegram bot for manual trading into MetaTrader 5.

## Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  Telegram Bot   │         │  Trade Engine   │
│  (Python)       │────────▶│  (MT5 Adapter)  │
│                 │  JSON   │                 │
│  - Conversation │         │  - MT5 API      │
│  - Validation   │         │  - Execution    │
│  - Risk Calc    │         │  - Risk Calc    │
└─────────────────┘         └─────────────────┘
        │                            │
        ▼                            ▼
┌─────────────────────────────────────────────┐
│           SQLite Database                   │
│  - Users, Settings, Setups, Trades         │
└─────────────────────────────────────────────┘
```

## Features

- **Manual Trading**: NOT an auto-trading or signal bot
- **Risk Management**: Fixed USD or % balance risk
- **Trade Validation**: SL position enforced (BUY: SL < entry, SELL: SL > entry)
- **Psychology Tracking**: Emotion selection before each trade
- **Trade Journal**: Complete logging with setups, emotions, charts
- **Symbol Resolution**: Dynamic symbol building (prefix + base + suffix)

## Project Structure

```
telegram-bot-mt5-trading-assitant/
├── bot/
│   ├── telegram_bot.py          # Main Telegram bot with conversation flow
│   └── trade_command_builder.py # Builds JSON trade commands
├── engine/
│   ├── mt5_adapter.py           # MT5 Trade Engine
│   ├── risk_calculator.py       # Volume calculation
│   ├── symbol_resolver.py       # Symbol building
│   └── trade_validator.py       # Trade validation
├── database/
│   ├── schema.sql               # Database schema
│   └── db_manager.py            # Database operations
├── tests/
│   ├── test_risk_calculator.py  # TDD tests
│   ├── test_symbol_resolver.py
│   ├── test_trade_validator.py
│   └── test_trade_command.py
└── requirements.txt
```

## Installation

1. **Clone repository:**

```bash
git clone <repository-url>
cd telegram-bot-mt5-trading-assitant
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure environment:**

```bash
# Copy example config
cp .env.example .env

# Edit .env and add your bot token
nano .env
```

4. **Initialize database:**

```bash
python -c "from database.db_manager import DatabaseManager; db = DatabaseManager(); db.connect(); db.initialize_schema()"
```

## Quick Start

### Step 1: Start MetaTrader 5

Open MT5 and login to your trading account.

### Step 2: Start Telegram Bot

```bash
# Terminal 1
python3 run_bot.py
```

### Step 3: Start Trade Engine Worker

```bash
# Terminal 2
python3 run_worker.py
```

### Step 4: Use Bot in Telegram

1. Find your bot and send `/start`
2. Use `/limitbuy` or `/limitsell` to place orders
3. Bot will queue commands → Worker executes in MT5

## Detailed Usage

See [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md) for complete guide in Vietnamese.

### Run Telegram Bot (Old Method)

```bash
export BOT_TOKEN="your_token"
python bot/telegram_bot.py
```

### Run Trade Engine Worker (Old Method)

```bash
python engine/trade_engine_worker.py
```

### Telegram Commands

- `/start` - Initialize bot
- `/limitbuy` - Place LIMIT BUY order
- `/limitsell` - Place LIMIT SELL order
- `/settings` - View/change settings
- `/setups` - Manage trade setups
- `/cancel` - Cancel current operation

## Trade Flow

1. `/limitbuy` or `/limitsell`
2. Enter symbol (default: XAU)
3. Enter entry price
4. Enter stop loss (validated: BUY SL < entry, SELL SL > entry)
5. Enter take profit
6. Preview (risk, volume, R:R)
7. Select emotion (calm, confident, fomo, stressed, revenge)
8. Select setup (quick choice)
9. Enter TradingView chart URL (optional)
10. Confirm or cancel
11. Trade sent to MT5

## User Configuration

Per-user settings stored in database:

- `default_symbol_base` (default: XAU)
- `symbol_prefix` (e.g., "BROKER.")
- `symbol_suffix` (e.g., "m", ".pro")
- `default_order_type` (LIMIT by default)
- `risk_type` (fixed_usd | percent)
- `risk_value` (e.g., 100 or 0.5)
- `default_account_id`

## Symbol Resolution

Symbol = `prefix` + `base` + "USD" + `suffix`

Examples:

- base=XAU, prefix="", suffix="" → XAUUSD
- base=XAU, prefix="BROKER.", suffix="m" → BROKER.XAUUSDm
- base=EUR, prefix="", suffix=".a" → EURUSD.a

## Risk & Volume Calculation

Formula:

```
Volume = Risk USD / (Stop Distance × Pip Value)
```

Then rounded to broker's volume step and enforced min/max limits.

## Database Schema

### Tables

- `users` - Telegram users
- `user_settings` - Per-user configuration
- `accounts` - MT5 trading accounts
- `setups` - User-defined trade setups
- `trades` - Complete trade journal

### Trades Table Fields

- Trade parameters: symbol, order_type, entry, sl, tp, volume
- Risk management: risk_usd, rr
- Psychology: emotion, setup_code, chart_url
- MT5 execution: mt5_ticket, mt5_open_price, mt5_close_price, mt5_profit
- Status: pending, filled, closed, cancelled, failed

## TDD Approach

This project follows strict Test-Driven Development:

1. ✅ Tests written BEFORE implementation
2. ✅ Tests define behavior
3. ✅ Implementation satisfies tests
4. ✅ No code without tests

Run tests:

```bash
pytest tests/ -v
```

## Security

- Never store bot token in code (use environment variables)
- Database uses foreign keys and constraints
- Trade validation prevents invalid orders
- Emotion and order_type are validated via CHECK constraints

## Future Enhancements

- [ ] Queue system between Bot and Trade Engine (Redis/RabbitMQ)
- [ ] REST API for Trade Engine
- [ ] Web dashboard for trade analytics
- [ ] Multi-account support
- [ ] Trade modification commands
- [ ] Position monitoring and alerts
- [ ] Backtesting integration

## License

Proprietary - All rights reserved
