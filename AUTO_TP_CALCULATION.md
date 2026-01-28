# Auto TP Calculation from R:R Ratio

## Overview

Take Profit (TP) is now **automatically calculated** based on:
- Entry price
- Stop Loss (SL) price
- Your configured Risk:Reward (R:R) ratio

You no longer need to manually calculate TP!

## How It Works

### Formula

```
Risk Distance = |Entry - SL|
Reward Distance = Risk Distance × R:R Ratio

For LIMIT BUY:  TP = Entry + Reward Distance
For LIMIT SELL: TP = Entry - Reward Distance
```

### Example: Gold Trade

**Settings:**
- R:R Ratio: 2:1 (default)

**LIMIT BUY:**
- Entry: 2000
- SL: 1995 (risk = 5 points)
- **TP: 2010** ← Auto-calculated (reward = 10 points)

**LIMIT SELL:**
- Entry: 2000
- SL: 2010 (risk = 10 points)
- **TP: 1980** ← Auto-calculated (reward = 20 points)

## Configuration

### Set Your R:R Ratio

Use the `/setrr` command:

```
/setrr
```

Bot will ask for your preferred R:R ratio:

```
Current R:R: 2:1

Examples:
• 2   = 2:1 (default) - TP is 2x SL distance
• 3   = 3:1 - TP is 3x SL distance
• 1.5 = 1.5:1 - TP is 1.5x SL distance

Enter new R:R ratio (e.g., 2, 2.5, 3):
```

### View Current Settings

```
/settings
```

Shows your current R:R ratio:

```
⚙️ Your Settings:

📈 R:R Ratio: 2.0:1
  (TP auto-calculated from SL)
```

## Trade Flow

The new flow when placing trades:

1. **/limitbuy** or **/limitsell**
2. Enter symbol (e.g., XAU)
3. Enter entry price
4. Enter stop loss
5. **TP is auto-calculated and displayed**
6. Continue with emotion, setup, etc.

### What You'll See

After entering SL:

```
✅ Stop Loss: 1995

📊 Auto-calculated TP:
Risk: 5 points
R:R: 2.0:1
Reward: 10 points
TP: 2010

💡 Use /setrr to change R:R ratio

Proceeding to trade preview...
```

## Benefits

### ✅ Consistency
- All trades follow the same R:R ratio
- No more inconsistent TP placement

### ✅ Speed
- Faster order entry
- No manual TP calculation

### ✅ Discipline
- Forces you to stick to your plan
- Pre-defined risk/reward structure

### ✅ Flexibility
- Change R:R anytime with `/setrr`
- Different ratios for different strategies

## Common R:R Ratios

| R:R | Use Case | Description |
|-----|----------|-------------|
| 1.5:1 | Conservative | Small profit targets |
| 2:1 | **Standard** | Most common, balanced |
| 3:1 | Aggressive | Larger profit targets |
| 5:1 | Swing trades | Long-term holds |

## Examples by Strategy

### Scalping (Quick trades)
```
R:R: 1.5:1 to 2:1
Entry: 2000
SL: 1998 (2 points)
TP: 2003 to 2004 (3-4 points)
```

### Day Trading
```
R:R: 2:1 to 3:1
Entry: 2000
SL: 1995 (5 points)
TP: 2010 to 2015 (10-15 points)
```

### Swing Trading
```
R:R: 3:1 to 5:1
Entry: 2000
SL: 1980 (20 points)
TP: 2060 to 2100 (60-100 points)
```

## Technical Details

### Precision
- TP is rounded to 2 decimal places
- Works for all instruments (Gold, Forex, Indices)

### Validation
- SL position still validated (BUY: SL < Entry, SELL: SL > Entry)
- TP automatically positioned correctly
- R:R ratio must be between 0.1 and 10

### Database
- R:R ratio stored in `user_settings.default_rr_ratio`
- Default value: 2.0
- Persists across sessions

## Migration

### Existing Users

Run the migration script to add R:R ratio to your database:

```bash
python migrate_add_rr_ratio.py
```

This will:
- Add `default_rr_ratio` column to `user_settings`
- Set default value to 2.0 for all existing users
- No data loss

### New Users

New users automatically get R:R ratio = 2.0

## FAQ

**Q: Can I still manually enter TP?**
A: No, TP is always auto-calculated from R:R ratio. This ensures consistency.

**Q: What if I want different TPs for different trades?**
A: Change your R:R ratio with `/setrr` before placing the trade.

**Q: Can I use fractional R:R ratios?**
A: Yes! Use 1.5, 2.5, 3.5, etc.

**Q: What's the min/max R:R ratio?**
A: Min: 0.1, Max: 10.0

**Q: Does this work with all symbols?**
A: Yes! Works with Gold, Forex, Indices, Crypto, etc.

**Q: Will old trades be affected?**
A: No, only new trades use auto TP calculation.

## Commands Summary

| Command | Description |
|---------|-------------|
| `/setrr` | Configure R:R ratio |
| `/settings` | View current R:R ratio |
| `/limitbuy` | Place BUY with auto TP |
| `/limitsell` | Place SELL with auto TP |

## See Also

- [Risk Management Guide](README.md#risk--volume-calculation)
- [Settings Commands](README.md#user-configuration)
- [Trade Flow](README.md#trade-flow)
