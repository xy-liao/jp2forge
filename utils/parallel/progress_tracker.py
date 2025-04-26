"""
Progress tracking and ETA estimation for parallel processing.

This module provides tools to track progress and estimate completion
time for long-running parallel operations.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Tracks progress and estimates completion time for batch operations.

    This class provides tools for monitoring progress, calculating
    completion percentage, and estimating remaining time for batch
    operations.
    """

    def __init__(
        self,
        total_items: int,
        update_interval: float = 1.0,
        callbacks: Optional[List[Callable[[Dict[str, Any]], None]]] = None
    ):
        """
        Initialize the progress tracker.

        Args:
            total_items: Total number of items to process
            update_interval: Seconds between progress updates
            callbacks: Functions to call with progress data on each update
        """
        self.total_items = total_items
        self.update_interval = update_interval
        self.callbacks = callbacks or []

        # Internal state
        self._completed = 0
        self._started = 0
        self._failed = 0
        self._start_time = time.time()
        self._last_update_time = self._start_time
        self._tracking = False
        self._tracking_thread = None
        self._lock = threading.RLock()
        self._last_update = {}
        self._active_items = set()

        logger.debug(f"ProgressTracker initialized with {total_items} total items")

    def start(self) -> None:
        """
        Start the progress tracking thread.
        """
        with self._lock:
            if self._tracking:
                return

            self._start_time = time.time()
            self._tracking = True
            self._tracking_thread = threading.Thread(
                target=self._update_loop,
                daemon=True
            )
            self._tracking_thread.start()
            logger.info("Progress tracking started")

    def stop(self) -> None:
        """
        Stop the progress tracking thread.
        """
        with self._lock:
            self._tracking = False

            if self._tracking_thread and self._tracking_thread.is_alive():
                self._tracking_thread.join(timeout=2.0)

            self._tracking_thread = None
            logger.info("Progress tracking stopped")

    def _update_loop(self) -> None:
        """
        Main update loop that periodically refreshes progress stats.
        """
        while self._tracking:
            try:
                # Update progress stats
                stats = self.get_progress()

                # Store for external access
                with self._lock:
                    self._last_update = stats

                # Execute callbacks with the progress data
                for callback in self.callbacks:
                    try:
                        callback(stats)
                    except Exception as e:
                        logger.error(f"Error in progress tracker callback: {e}")

            except Exception as e:
                logger.error(f"Error updating progress: {e}")

            # Sleep until next update
            time.sleep(self.update_interval)

    def item_started(self, item_id: Any) -> None:
        """
        Mark an item as started.

        Args:
            item_id: Unique identifier for the item
        """
        with self._lock:
            if item_id not in self._active_items:
                self._active_items.add(item_id)
                self._started += 1

    def item_completed(self, item_id: Any, success: bool = True) -> None:
        """
        Mark an item as completed.

        Args:
            item_id: Unique identifier for the item
            success: Whether the item completed successfully
        """
        with self._lock:
            if item_id in self._active_items:
                self._active_items.remove(item_id)

            self._completed += 1
            if not success:
                self._failed += 1

    def update_total(self, new_total: int) -> None:
        """
        Update the total number of items to process.

        Args:
            new_total: New total number of items
        """
        with self._lock:
            self.total_items = max(new_total, self._completed)

    def get_progress(self) -> Dict[str, Any]:
        """
        Get current progress statistics.

        Returns:
            dict: Progress statistics
        """
        with self._lock:
            current_time = time.time()
            elapsed = current_time - self._start_time
            completed = self._completed
            total = self.total_items

            # Calculate completion percentage
            percent_complete = (completed / total * 100) if total > 0 else 0

            # Calculate processing rate
            rate = completed / elapsed if elapsed > 0 else 0

            # Estimate time remaining
            remaining_items = total - completed
            eta_seconds = remaining_items / rate if rate > 0 else 0

            # Format ETA for display
            if eta_seconds > 0:
                eta_time = datetime.now() + timedelta(seconds=eta_seconds)
                eta_str = eta_time.strftime("%H:%M:%S")
            else:
                eta_str = "N/A"

            return {
                'timestamp': current_time,
                'start_time': self._start_time,
                'elapsed_seconds': elapsed,
                'total_items': total,
                'completed': completed,
                'started': self._started,
                'active': len(self._active_items),
                'failed': self._failed,
                'percent_complete': percent_complete,
                'items_per_second': rate,
                'eta_seconds': eta_seconds,
                'eta_time': eta_str,
            }

    @property
    def last_update(self) -> Dict[str, Any]:
        """
        Get the latest progress update.

        Returns:
            dict: Latest progress statistics
        """
        with self._lock:
            return self._last_update.copy() if self._last_update else self.get_progress()

    @property
    def percent_complete(self) -> float:
        """
        Get the current completion percentage.

        Returns:
            float: Percentage complete (0-100)
        """
        return self.last_update.get('percent_complete', 0.0)

    @property
    def eta_seconds(self) -> float:
        """
        Get the estimated time remaining in seconds.

        Returns:
            float: Estimated seconds remaining
        """
        return self.last_update.get('eta_seconds', 0.0)

    @property
    def eta_time(self) -> str:
        """
        Get the estimated completion time as a string.

        Returns:
            str: Formatted estimated completion time
        """
        return self.last_update.get('eta_time', 'N/A')

    @property
    def items_per_second(self) -> float:
        """
        Get the current processing rate.

        Returns:
            float: Items processed per second
        """
        return self.last_update.get('items_per_second', 0.0)
