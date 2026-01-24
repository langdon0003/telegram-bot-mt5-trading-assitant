"""
Notification Queue - Send execution results back to users

Worker writes notifications after processing commands.
Bot polls and sends notifications to users via Telegram.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class NotificationQueue:
    """
    Queue for sending trade execution notifications to users.

    Worker writes notifications after trade execution.
    Bot reads and sends to users via Telegram.
    """

    def __init__(self, notification_dir: str = "notifications"):
        """
        Initialize notification queue.

        Args:
            notification_dir: Directory for notification files
        """
        self.notification_dir = Path(notification_dir)
        self._ensure_notification_directory()

    def _ensure_notification_directory(self):
        """Create notification directory if it doesn't exist"""
        try:
            self.notification_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Notification directory ready: {self.notification_dir.absolute()}")
        except Exception as e:
            logger.error(f"Failed to create notification directory: {e}")
            raise

    def enqueue(
        self,
        telegram_id: int,
        trade_id: int,
        success: bool,
        message: str,
        details: Dict = None
    ) -> str:
        """
        Add notification to queue.

        Args:
            telegram_id: User's Telegram ID
            trade_id: Trade ID from database
            success: Whether trade was successful
            message: Notification message
            details: Additional details (ticket, error, etc.)

        Returns:
            Notification file ID
        """
        # Generate unique notification ID
        notif_id = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{telegram_id}_{trade_id}"

        # Build notification
        notification = {
            "notification_id": notif_id,
            "telegram_id": telegram_id,
            "trade_id": trade_id,
            "success": success,
            "message": message,
            "details": details or {},
            "created_at": datetime.utcnow().isoformat(),
            "sent": False
        }

        # Write to file atomically
        temp_file = self.notification_dir / f".{notif_id}.tmp"
        final_file = self.notification_dir / f"{notif_id}.json"

        try:
            with open(temp_file, 'w') as f:
                json.dump(notification, f, indent=2)

            temp_file.rename(final_file)

            logger.info(f"Notification queued: {notif_id} for user {telegram_id}")
            return notif_id

        except Exception as e:
            logger.error(f"Failed to enqueue notification: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

    def get_pending(self) -> list:
        """
        Get all pending notifications.

        Returns:
            List of notification dictionaries
        """
        notifications = []

        try:
            for file_path in sorted(self.notification_dir.glob("*.json")):
                try:
                    with open(file_path, 'r') as f:
                        notif = json.load(f)
                        notif['_file_path'] = file_path
                        notifications.append(notif)
                except Exception as e:
                    logger.error(f"Failed to read notification {file_path}: {e}")

            return notifications

        except Exception as e:
            logger.error(f"Failed to list notifications: {e}")
            return []

    def mark_sent(self, notification_id: str) -> bool:
        """
        Mark notification as sent and delete file.

        Args:
            notification_id: Notification ID

        Returns:
            True if successful
        """
        file_path = self.notification_dir / f"{notification_id}.json"

        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Notification sent and deleted: {notification_id}")
                return True
            else:
                logger.warning(f"Notification file not found: {notification_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete notification {notification_id}: {e}")
            return False

    def get_pending_count(self) -> int:
        """Get number of pending notifications"""
        try:
            return len(list(self.notification_dir.glob("*.json")))
        except Exception as e:
            logger.error(f"Failed to count notifications: {e}")
            return 0
