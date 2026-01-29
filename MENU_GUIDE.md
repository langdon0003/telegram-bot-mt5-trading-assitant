# Menu Guide - Telegram Bot Menu Button

## Overview

The bot now features an interactive menu system with a persistent **Menu button** at the bottom-left of the Telegram chat interface.

## Menu Button

### What is it?

The Menu button (📱) appears at the bottom-left corner of the chat, next to the text input field. When clicked, it shows a list of available bot commands.

### How to use it?

1. **Open chat with bot**
2. **Look for "Menu" button** at bottom-left (next to attachment icon)
3. **Click "Menu"** to see command list
4. **Select a command** from the list to execute it

### Commands shown in Menu:

#### 📈 Trading
- `/start` - Main menu
- `/limitbuy` - Place LIMIT BUY order
- `/limitsell` - Place LIMIT SELL order

#### 📋 Order Management
- `/orders` - View pending orders
- `/orderdetail` - View order details
- `/closeorder` - Close pending order

#### ⚙️ Settings
- `/settings` - View current settings
- `/setrisktype` - Configure risk settings
- `/setrr` - Configure R:R ratio
- `/setsymbol` - Configure symbol

#### 📝 Setup Management
- `/addsetup` - Add trade setup
- `/setups` - View all setups

#### 🔧 MT5 Connection
- `/mt5connection` - Check MT5 status
- `/reconnectmt5` - Reconnect to MT5

#### 🚫 Help
- `/cancel` - Cancel operation

## Interactive Main Menu

When you send `/start`, you'll see an **interactive menu with buttons**:

```
📱 MT5 Trading Assistant Menu
👋 Vui lòng chọn menu:

[📊 Place Order]
[📋 View Orders] [⚙️ Settings]
[🔧 More Commands]
```

### Navigation

#### 1. Place Order
Click to see trading options:
- 🟢 Limit Buy
- 🔴 Limit Sell
- « Back to Menu

#### 2. View Orders
Shows instructions for:
- `/orders` - View all orders
- `/orderdetail` - Check details
- `/closeorder` - Close order

#### 3. Settings
Configure bot settings:
- 📈 Risk Settings
- 🎯 R:R Ratio
- 📊 Symbol Config
- 📋 View Settings
- « Back to Menu

#### 4. More Commands
Shows complete command list with descriptions.

### Back to Menu

All submenus have a **"« Back to Menu"** button to return to the main menu.

## Technical Details

### Menu Button Configuration

The menu button is automatically configured when the bot starts:

```python
async def setup_bot_menu(app):
    """Set up bot menu button and commands"""
    # Define commands
    commands = [
        BotCommand("start", "📱 Main menu"),
        BotCommand("limitbuy", "🟢 Place LIMIT BUY order"),
        # ... more commands
    ]

    # Set commands
    await app.bot.set_my_commands(commands)

    # Set menu button to show commands
    await app.bot.set_chat_menu_button(
        menu_button=MenuButtonCommands()
    )
```

### Features

✅ **Persistent Menu Button**
- Always visible at bottom-left
- Shows command list when clicked
- No need to remember commands

✅ **Interactive Main Menu**
- Button-based navigation
- Vietnamese text support
- Emoji icons for clarity

✅ **Nested Submenus**
- Trading submenu
- Settings submenu
- Easy navigation with "Back" buttons

✅ **Markdown Formatting**
- Bold text for headers
- Bullet points for clarity
- Better readability

## User Experience

### Before (Text-based)
```
Welcome to MT5 Trading Assistant!

📈 Trading:
/limitbuy - Place LIMIT BUY order
/limitsell - Place LIMIT SELL order
...
(long text list)
```

### After (Interactive Menu)
```
📱 MT5 Trading Assistant Menu
👋 Vui lòng chọn menu:

[📊 Place Order]
[📋 View Orders] [⚙️ Settings]
[🔧 More Commands]
```

**Benefits:**
- ✅ Easier navigation
- ✅ Less scrolling
- ✅ Clear visual hierarchy
- ✅ Quick access to common actions
- ✅ Vietnamese language support

## Troubleshooting

### Menu button not showing?

**Option 1:** Restart chat
1. Close chat with bot
2. Reopen chat
3. Menu button should appear

**Option 2:** Send `/start`
1. Send `/start` command
2. This triggers menu setup

**Option 3:** Update Telegram
1. Make sure you're using latest Telegram version
2. Menu button requires Telegram 5.7+

### Commands not in menu?

If menu button is there but shows empty list:
1. Stop the bot
2. Restart the bot (menu is configured on startup)
3. Commands should appear

### Want to customize menu?

Edit `bot/telegram_bot.py` → `setup_bot_menu()`:

```python
commands = [
    BotCommand("yourcommand", "Your description"),
    # Add more commands here
]
```

## See Also

- [Main README](README.md) - Bot overview
- [Setup Guide](README.md#setup) - Installation
- [Commands List](README.md#commands) - All commands
