"""
Test Command Queue System

Simple test to verify the queue implementation works correctly.
"""

import os
import json
import tempfile
from pathlib import Path
from engine.command_queue import CommandQueue


def test_command_queue():
    """Test basic queue operations"""

    # Create temporary queue directory
    with tempfile.TemporaryDirectory() as temp_dir:
        queue = CommandQueue(queue_dir=temp_dir)

        print("✓ Queue initialized")

        # Test enqueue
        test_command = {
            "trade_id": 123,
            "user_id": 1,
            "symbol": "XAUUSD",
            "order_type": "LIMIT_BUY",
            "entry_price": 2650.0,
            "sl_price": 2640.0,
            "tp_price": 2670.0,
            "volume": 0.1
        }

        queue_id = queue.enqueue(test_command)
        print(f"✓ Command enqueued: {queue_id}")

        # Test pending count
        count = queue.get_pending_count()
        assert count == 1, f"Expected 1 pending, got {count}"
        print(f"✓ Pending count: {count}")

        # Test list pending
        pending = queue.list_pending()
        assert len(pending) == 1, f"Expected 1 in list, got {len(pending)}"
        assert pending[0] == queue_id, f"Queue ID mismatch"
        print(f"✓ Listed pending: {pending}")

        # Test dequeue
        dequeued = queue.dequeue(queue_id)
        assert dequeued is not None, "Dequeue returned None"
        assert dequeued['queue_id'] == queue_id, "Queue ID mismatch"
        assert dequeued['command'] == test_command, "Command data mismatch"
        print(f"✓ Command dequeued successfully")

        # Verify file is gone
        count_after = queue.get_pending_count()
        assert count_after == 0, f"Expected 0 after dequeue, got {count_after}"
        print(f"✓ Queue empty after dequeue")

        print("\n✅ All tests passed!")


def test_multiple_commands():
    """Test enqueueing multiple commands"""

    with tempfile.TemporaryDirectory() as temp_dir:
        queue = CommandQueue(queue_dir=temp_dir)

        # Enqueue 5 commands
        queue_ids = []
        for i in range(5):
            command = {
                "trade_id": i,
                "symbol": "XAUUSD",
                "entry_price": 2650.0 + i
            }
            queue_id = queue.enqueue(command)
            queue_ids.append(queue_id)

        print(f"✓ Enqueued {len(queue_ids)} commands")

        # Verify count
        count = queue.get_pending_count()
        assert count == 5, f"Expected 5 pending, got {count}"
        print(f"✓ Pending count: {count}")

        # Process all
        processed = 0
        for queue_id in queue_ids:
            result = queue.dequeue(queue_id)
            if result:
                processed += 1

        assert processed == 5, f"Expected to process 5, got {processed}"
        print(f"✓ Processed {processed} commands")

        # Verify empty
        final_count = queue.get_pending_count()
        assert final_count == 0, f"Expected 0 after processing, got {final_count}"
        print(f"✓ Queue empty")

        print("\n✅ Multiple commands test passed!")


def test_queue_persistence():
    """Test that queue files persist and can be read back"""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create queue and enqueue
        queue1 = CommandQueue(queue_dir=temp_dir)
        command = {"trade_id": 999, "symbol": "EURUSD"}
        queue_id = queue1.enqueue(command)
        print(f"✓ Command enqueued: {queue_id}")

        # Create new queue instance (simulating restart)
        queue2 = CommandQueue(queue_dir=temp_dir)

        # Verify command still there
        count = queue2.get_pending_count()
        assert count == 1, f"Expected 1 after restart, got {count}"
        print(f"✓ Command persisted after restart")

        # Dequeue with new instance
        result = queue2.dequeue(queue_id)
        assert result is not None, "Could not dequeue after restart"
        assert result['command']['trade_id'] == 999
        print(f"✓ Command retrieved successfully")

        print("\n✅ Persistence test passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Command Queue System")
    print("=" * 60)
    print()

    try:
        test_command_queue()
        print()
        test_multiple_commands()
        print()
        test_queue_persistence()

        print()
        print("=" * 60)
        print("🎉 All queue tests passed successfully!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)
