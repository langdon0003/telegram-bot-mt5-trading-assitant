# Command Queue System

## Overview

The bot uses a simple file-based queue to communicate trade commands to the MT5 Trade Engine.

## How It Works

1. **Telegram Bot** → Creates trade command → Writes to `queue/` directory as JSON file
2. **MT5 Trade Engine** → Monitors `queue/` directory → Picks up and processes files

## Queue Directory Structure

```
queue/
├── 20260124_153045_a1b2c3d4.json  # Pending command
├── 20260124_153048_e5f6g7h8.json  # Pending command
└── ...
```

## Queue File Format

Each queue file contains:

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
    "setup_code": "ORB",
    "chart_url": "https://tradingview.com/...",
    "timestamp": "2026-01-24T15:30:45.123456Z"
  }
}
```

## Usage in Bot

```python
from engine.command_queue import CommandQueue

# Initialize queue
queue = CommandQueue(queue_dir="queue")

# Enqueue a trade command
command = {...}  # From TradeCommandBuilder
queue_id = queue.enqueue(command)

# Check pending count
pending = queue.get_pending_count()
```

## Usage in Trade Engine

```python
from engine.command_queue import CommandQueue

# Initialize queue
queue = CommandQueue(queue_dir="queue")

# Get pending commands
pending_ids = queue.list_pending()

# Process each command
for queue_id in pending_ids:
    queue_command = queue.dequeue(queue_id)
    if queue_command:
        command = queue_command['command']
        # Execute trade...
```

## Future Improvements

This simple file-based queue will be replaced with a proper message queue system:

- **Redis Queue (RQ)** - Simple, Python-native
- **RabbitMQ** - Enterprise-grade, reliable
- **AWS SQS** - Cloud-native, scalable

### Migration Path

The `CommandQueue` class provides a consistent interface that can be swapped out:

```python
# Current: File-based
queue = CommandQueue(queue_dir="queue")

# Future: Redis-based
queue = RedisCommandQueue(redis_url="redis://localhost:6379")

# Future: RabbitMQ-based
queue = RabbitMQCommandQueue(amqp_url="amqp://localhost:5672")
```

All queue implementations will support the same methods:

- `enqueue(command)` - Add command to queue
- `dequeue(queue_id)` - Remove and return command
- `get_pending_count()` - Count pending commands
- `list_pending()` - List all pending queue IDs

## Error Handling

### If Queue Directory is Not Accessible

The bot will:

1. Log an error
2. Notify the user via Telegram
3. Save the trade to database (for manual retry)

### If Command Cannot Be Written

The bot will:

1. Catch the exception
2. Notify the user
3. Not save to database (to prevent orphaned records)

### If Trade Engine is Down

Commands will accumulate in the queue directory. When the engine comes back online, it will process all pending commands in order.

## Monitoring

### Check Queue Status

```bash
# Count pending commands
ls -1 queue/*.json | wc -l

# View oldest pending command
ls -t queue/*.json | tail -1

# View queue contents
cat queue/*.json | jq .
```

### Clear Queue (Emergency)

```python
from engine.command_queue import CommandQueue
queue = CommandQueue()
queue.clear_all()  # WARNING: Deletes all pending commands!
```

## Testing

```bash
# Run bot in one terminal
python bot/telegram_bot.py

# Monitor queue in another terminal
watch -n 1 'ls -lh queue/'

# Process commands with engine (future implementation)
python engine/trade_engine_worker.py
```
