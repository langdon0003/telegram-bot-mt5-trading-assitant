# Bug Fix: /limitbuy Không Hoạt Động

## 🐛 VẤN ĐỀ

Command `/limitbuy` và `/limitsell` không hoạt động do lỗi trong conversation handler flow.

## 🔍 NGUYÊN NHÂN

### Conflict trong Conversation States

**File:** [bot/telegram_bot.py](bot/telegram_bot.py)

**Vấn đề:**

1. Function `ask_take_profit()` tự động tính TP và **gọi trực tiếp** `show_preview()`:

   ```python
   # Line 590
   return await self.show_preview(update, context)
   ```

2. Nhưng trong conversation handler vẫn định nghĩa state `TAKE_PROFIT`:

   ```python
   # Line 160
   TAKE_PROFIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.show_preview)],
   ```

3. **Conflict:**
   - `ask_take_profit` return EMOTION state (từ show_preview)
   - Conversation handler expect TAKE_PROFIT state
   - State mismatch → Conversation stuck → Bot không response

## ✅ GIẢI PHÁP

Xóa state `TAKE_PROFIT` khỏi cả 2 conversation handlers vì:

- TP đã được tính tự động trong `ask_take_profit()`
- Không cần user input cho TP nữa
- Flow trực tiếp từ STOP_LOSS → ask_take_profit → show_preview → EMOTION

## 📝 THAY ĐỔI

### 1. Fixed limitbuy_handler

```python
# BEFORE (❌)
limitbuy_handler = ConversationHandler(
    entry_points=[CommandHandler("limitbuy", self.limitbuy_start)],
    states={
        SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_entry)],
        ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_stop_loss)],
        STOP_LOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_take_profit)],
        TAKE_PROFIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.show_preview)],  # ❌ KHÔNG DÙNG
        EMOTION: [CallbackQueryHandler(self.ask_setup)],
        ...
    },
    ...
)

# AFTER (✅)
limitbuy_handler = ConversationHandler(
    entry_points=[CommandHandler("limitbuy", self.limitbuy_start)],
    states={
        SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_entry)],
        ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_stop_loss)],
        STOP_LOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_take_profit)],
        # TAKE_PROFIT state removed - TP is auto-calculated
        EMOTION: [CallbackQueryHandler(self.ask_setup)],
        ...
    },
    ...
)
```

### 2. Fixed limitsell_handler

Tương tự, xóa state `TAKE_PROFIT` khỏi limitsell handler.

### 3. Improved error handling

```python
# BEFORE
except ValueError:
    await update.message.reply_text("Invalid price. Please enter a number:")
    return TAKE_PROFIT  # ❌ State không tồn tại

# AFTER
except Exception as e:
    logger.error(f"Error in show_preview: {e}")
    await update.message.reply_text(
        "❌ Error showing preview. Please try again or /cancel"
    )
    return ConversationHandler.END  # ✅ End conversation properly
```

## 🔄 CONVERSATION FLOW SAU KHI FIX

```
/limitbuy
    ↓
SYMBOL (user nhập symbol)
    ↓
ENTRY (user nhập entry price)
    ↓
STOP_LOSS (user nhập SL)
    ↓
ask_take_profit()
    ├── Validate SL
    ├── Tính TP tự động (dựa trên R:R ratio)
    ├── Show TP calculated message
    └── Call show_preview() trực tiếp
            ↓
        EMOTION (user chọn emotion button)
            ↓
        SETUP (user chọn setup)
            ↓
        CHART_URL (user nhập chart URL)
            ↓
        CONFIRM (user confirm execute)
            ↓
        execute_trade() → MT5
```

## ✅ KẾT QUẢ

- `/limitbuy` hoạt động bình thường
- `/limitsell` hoạt động bình thường
- TP được tính tự động theo R:R ratio
- User không cần nhập TP thủ công
- Conversation flow trơn tru không bị stuck

## 🧪 CÁCH TEST

```bash
# 1. Start bot
python3 run_bot.py

# 2. Trong Telegram
/start
/limitbuy
# Nhập symbol: XAU
# Nhập entry: 2650
# Nhập SL: 2645
# → Bot sẽ tự động tính TP và show preview
# → Chọn emotion
# → Chọn setup
# → Nhập chart URL hoặc skip
# → Confirm
# → Execute trade
```

## 📋 FILES CHANGED

- [bot/telegram_bot.py](bot/telegram_bot.py)
  - Line 153-167: Fixed limitbuy_handler
  - Line 169-183: Fixed limitsell_handler
  - Line 596-606: Cleaned up show_preview
  - Line 668-673: Fixed error handling

## 🔗 RELATED

- [AUTO_TP_CALCULATION.md](AUTO_TP_CALCULATION.md) - Chi tiết về tính TP tự động
- [TDD_SUMMARY.md](TDD_SUMMARY.md) - Test cases

---

**Status:** ✅ FIXED
**Date:** January 29, 2026
**Impact:** HIGH - Core functionality restored
