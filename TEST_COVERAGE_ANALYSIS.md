# Test Coverage Analysis

## ✅ Files WITH Tests

### Engine Layer (3/4 - 75%)
- ✅ `engine/risk_calculator.py` → `tests/test_risk_calculator.py`
- ✅ `engine/symbol_resolver.py` → `tests/test_symbol_resolver.py`
- ✅ `engine/trade_validator.py` → `tests/test_trade_validator.py`
- ❌ `engine/mt5_adapter.py` → NO TEST (Requires MT5, hard to mock)

### Bot Commands (2/6 - 33%)
- ✅ `bot/menu_handler.py` → `tests/test_menu_handler.py`
- ✅ `bot/settings_commands.py` → `tests/test_settings_commands.py`
- ❌ `bot/setup_commands.py` → NO TEST
- ❌ `bot/order_commands.py` → NO TEST
- ❌ `bot/modify_order_commands.py` → NO TEST (NEW FEATURE)
- ❌ `bot/position_commands.py` → NO TEST (NEW FEATURE)

### Bot Utilities (1/3 - 33%)
- ✅ `bot/trade_command_builder.py` → `tests/test_trade_command.py`
- ❌ `bot/conversation_utils.py` → NO TEST (NEW UTILITY)
- ❌ `bot/telegram_bot.py` → NO TEST (Integration level)

### Database Layer (0/1 - 0%)
- ❌ `database/db_manager.py` → NO TEST

---

## 📊 Overall Coverage: ~37% (6/16 testable files)

---

## ❌ CRITICAL Missing Tests (High Priority)

### 1. **bot/setup_commands.py** - CRITICAL
**Why:** Complex conversation flow with database operations
**Commands:** `/addsetup`, `/editsetup`, `/deletesetup`
**Risk:** User setup management is core functionality

### 2. **bot/order_commands.py** - HIGH
**Why:** Order viewing and closing operations
**Commands:** `/orders`, `/orderdetail`, `/closeorder`
**Risk:** Direct MT5 operations, potential data loss

### 3. **bot/modify_order_commands.py** - HIGH (NEW)
**Why:** NEW FEATURE, modifies pending orders
**Commands:** `/modifyorder`
**Risk:** Incorrect modifications can cause losses

### 4. **bot/position_commands.py** - HIGH (NEW)
**Why:** NEW FEATURE, closes open positions
**Commands:** `/positions`
**Risk:** Incorrect closes can cause losses

### 5. **bot/conversation_utils.py** - MEDIUM (NEW)
**Why:** NEW UTILITY, shared conversation handlers
**Functions:** `cancel_conversation`, `cancel_and_process_new_command`
**Risk:** Conversation state management bugs

### 6. **database/db_manager.py** - MEDIUM
**Why:** All database operations
**Risk:** Data corruption, SQL injection

---

## 📋 Recommended Test Creation Priority

### Phase 1: NEW FEATURES (Most Critical)
1. Create `tests/test_modify_order_commands.py`
2. Create `tests/test_position_commands.py`
3. Create `tests/test_conversation_utils.py`

### Phase 2: EXISTING FEATURES
4. Create `tests/test_setup_commands.py`
5. Create `tests/test_order_commands.py`

### Phase 3: INFRASTRUCTURE
6. Create `tests/test_db_manager.py`

---

## 🧪 Existing Test Count: ~16 test functions

### Distribution:
- `test_menu_handler.py`: ~12 tests
- `test_settings_commands.py`: ~8 tests
- `test_risk_calculator.py`: ~5 tests
- `test_symbol_resolver.py`: ~4 tests
- `test_trade_validator.py`: ~6 tests
- `test_trade_command.py`: ~3 tests
- `test_tp_auto_calculation.py`: ~2 tests

**Total: ~40 test functions across 7 test files**

---

## 💡 Testing Challenges

### MT5-Dependent Code
- `engine/mt5_adapter.py` - Hard to test without MT5 running
- Solution: Mock `MetaTrader5` module

### Async Telegram Handlers
- All bot command files use async/await
- Solution: Using `pytest-asyncio` (already configured)

### Database Operations
- Requires SQLite database
- Solution: In-memory database for tests

### ConversationHandlers
- Complex state machines
- Solution: Mock Update/Context objects (already done in existing tests)

---

## 🎯 Test Coverage Goals

- **Current:** ~37% file coverage
- **Goal:** 75% file coverage
- **Priority:** 100% coverage on NEW features (modify_order, positions)

---

## 📝 Notes

1. **Integration tests** for `telegram_bot.py` are not critical
2. **MT5 adapter** can use integration tests on dev environment
3. **Conversation utils** are simple enough to test easily
4. **NEW features** (modify, positions) MUST have tests before production
