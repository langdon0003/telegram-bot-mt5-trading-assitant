"""
Command Queue Handler - Simple File-Based Queue

Provides a simple file-based queue system for trade commands.
Commands are written as JSON files to a queue directory.

This is a temporary solution that can be replaced with Redis/RabbitMQ later.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CommandQueue:
    """
    Simple file-based queue for trade commands.

    Commands are written to the queue directory as JSON files.
    The Trade Engine (MT5 Adapter) monitors this directory and processes files.
    """

    def __init__(self, queue_dir: str = "queue"):
        """
        Initialize command queue.

        Args:
            queue_dir: Directory path for queue files (relative or absolute)
        """
        self.queue_dir = Path(queue_dir)
        self._ensure_queue_directory()

    def _ensure_queue_directory(self):
        """Create queue directory if it doesn't exist"""
        try:
            self.queue_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Queue directory ready: {self.queue_dir.absolute()}")
        except Exception as e:
            logger.error(f"Failed to create queue directory: {e}")
            raise

    def enqueue(self, command: Dict) -> str:
        """
        Add a trade command to the queue.

        Args:
            command: Trade command dictionary (from TradeCommandBuilder)

        Returns:
            Queue file ID (filename without extension)

        Raises:
            Exception if command cannot be written
        """
        # Generate unique queue ID
        queue_id = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Add queue metadata
        queue_command = {
            "queue_id": queue_id,
            "queued_at": datetime.utcnow().isoformat(),
            "status": "pending",
            "command": command
        }

        # Write to file atomically
        temp_file = self.queue_dir / f".{queue_id}.tmp"
        final_file = self.queue_dir / f"{queue_id}.json"

        try:
            # Write to temp file first
            with open(temp_file, 'w') as f:
                json.dump(queue_command, f, indent=2)

            # Atomic rename
            temp_file.rename(final_file)

            logger.info(f"Command queued: {queue_id} (Trade #{command.get('trade_id', 'N/A')})")
            return queue_id

        except Exception as e:
            logger.error(f"Failed to enqueue command: {e}")
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()
            raise

    def get_pending_count(self) -> int:
        """
        Get number of pending commands in queue.

        Returns:
            Count of .json files in queue directory
        """
        try:
            return len(list(self.queue_dir.glob("*.json")))
        except Exception as e:
            logger.error(f"Failed to count queue files: {e}")
            return 0

    def dequeue(self, queue_id: str) -> Optional[Dict]:
        """
        Read and remove a command from the queue.

        Args:
            queue_id: Queue file ID

        Returns:
            Command dictionary or None if not found
        """
        file_path = self.queue_dir / f"{queue_id}.json"

        try:
            if not file_path.exists():
                logger.warning(f"Queue file not found: {queue_id}")
                return None

            # Read command
            with open(file_path, 'r') as f:
                queue_command = json.load(f)

            # Delete file
            file_path.unlink()

            logger.info(f"Command dequeued: {queue_id}")
            return queue_command

        except Exception as e:
            logger.error(f"Failed to dequeue command {queue_id}: {e}")
            return None

    def list_pending(self) -> list:
        """
        List all pending queue IDs.

        Returns:
            List of queue IDs (sorted by timestamp)
        """
        try:
            files = sorted(self.queue_dir.glob("*.json"))
            return [f.stem for f in files]
        except Exception as e:
            logger.error(f"Failed to list queue files: {e}")
            return []

    def clear_all(self):
        """
        Clear all pending commands from queue.

        WARNING: This deletes all pending trade commands!
        Use only for testing or emergency cleanup.
        """
        try:
            for file_path in self.queue_dir.glob("*.json"):
                file_path.unlink()
            logger.warning("Queue cleared - all pending commands deleted")
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            raise
