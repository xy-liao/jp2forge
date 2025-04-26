"""
Adaptive worker pool for parallel processing.

This module provides a worker pool that adapts to system resource
availability and automatically adjusts concurrency levels.
"""

import os
import time
import logging
import threading
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed, Future
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic, Tuple, Iterator

from utils.parallel.resource_monitor import ResourceMonitor
from utils.parallel.progress_tracker import ProgressTracker

# Type variables for generics
T = TypeVar('T')  # Input type
R = TypeVar('R')  # Result type

logger = logging.getLogger(__name__)


class AdaptiveWorkerPool(Generic[T, R]):
    """
    A worker pool that adapts its size based on system resources.

    This class provides a process pool implementation that can
    adjust the number of workers based on system memory and CPU usage.
    """

    def __init__(
        self,
        worker_func: Callable[[T], R],
        max_workers: Optional[int] = None,
        min_workers: int = 1,
        memory_high_threshold: float = 0.85,
        memory_critical_threshold: float = 0.95,
        check_interval: float = 5.0,
        chunk_size: int = 1,
        track_progress: bool = True,
        progress_callbacks: Optional[List[Callable[[Dict[str, Any]], None]]] = None,
        resource_callbacks: Optional[List[Callable[[Dict[str, Any]], None]]] = None
    ):
        """
        Initialize the adaptive worker pool.

        Args:
            worker_func: Function to execute for each work item
            max_workers: Maximum number of worker processes
            min_workers: Minimum number of worker processes
            memory_high_threshold: Memory usage ratio considered high (0.0-1.0)
            memory_critical_threshold: Memory usage ratio considered critical (0.0-1.0)
            check_interval: Seconds between resource checks
            chunk_size: Items to process per task (for map operations)
            track_progress: Whether to track progress and provide ETA
            progress_callbacks: Functions to call with progress updates
            resource_callbacks: Functions to call with resource updates
        """
        # Store parameters
        self.worker_func = worker_func
        self.max_workers = max_workers or max(1, multiprocessing.cpu_count() - 1)
        self.min_workers = min(min_workers, self.max_workers)
        self.chunk_size = chunk_size
        self.track_progress = track_progress

        # Initialize components
        self.resource_monitor = ResourceMonitor(
            check_interval=check_interval,
            memory_high_threshold=memory_high_threshold,
            memory_critical_threshold=memory_critical_threshold,
            callbacks=resource_callbacks
        )

        # Internal state
        self._current_workers = self.max_workers
        self._executor = None
        self._futures = {}
        self._lock = threading.RLock()
        self._progress_tracker = None
        self._progress_callbacks = progress_callbacks or []

        logger.info(f"AdaptiveWorkerPool initialized with {self.max_workers} max workers")

    def start(self) -> None:
        """
        Start the worker pool and resource monitoring.
        """
        with self._lock:
            # Start resource monitoring
            self.resource_monitor.start()

            # Initialize with max workers
            self._current_workers = self.max_workers
            self._executor = self._create_executor()

            logger.info(f"Worker pool started with {self._current_workers} workers")

    def stop(self) -> None:
        """
        Stop the worker pool and resource monitoring.
        """
        with self._lock:
            # Stop resource monitoring
            self.resource_monitor.stop()

            # Shutdown progress tracking
            if self._progress_tracker:
                self._progress_tracker.stop()
                self._progress_tracker = None

            # Shutdown executor
            if self._executor:
                self._executor.shutdown(wait=True)
                self._executor = None

            logger.info("Worker pool stopped")

    def _create_executor(self) -> ProcessPoolExecutor:
        """
        Create a new process pool executor.

        Returns:
            ProcessPoolExecutor: The executor instance
        """
        return ProcessPoolExecutor(max_workers=self._current_workers)

    def _resize_pool_if_needed(self) -> bool:
        """
        Check if the pool needs to be resized based on resource usage.

        Returns:
            bool: True if the pool was resized
        """
        # Check resource usage
        metrics = self.resource_monitor.last_check

        # Get recommended worker count
        recommended = self.resource_monitor.get_recommended_workers(self.max_workers)
        recommended = max(recommended, self.min_workers)

        # Only resize if recommendation is significantly different
        if abs(recommended - self._current_workers) >= 2:
            logger.info(
                f"Adapting worker count from {self._current_workers} to {recommended} "
                f"(memory: {metrics.get('memory_percent', 0):.1f}%, "
                f"CPU: {metrics.get('cpu_percent', 0):.1f}%)"
            )

            # Create new executor with recommended workers
            old_executor = self._executor
            self._current_workers = recommended
            self._executor = self._create_executor()

            # Shut down old executor
            if old_executor:
                old_executor.shutdown(wait=False)

            return True

        return False

    def map(self, iterable: List[T]) -> List[R]:
        """
        Process items in parallel and return results in order.

        Args:
            iterable: Items to process

        Returns:
            list: Results in the same order as inputs
        """
        # Ensure pool is started
        if not self._executor:
            self.start()

        total_items = len(iterable)

        # Initialize progress tracking if enabled
        if self.track_progress:
            self._progress_tracker = ProgressTracker(
                total_items=total_items,
                callbacks=self._progress_callbacks
            )
            self._progress_tracker.start()

        # Process items
        results = []

        try:
            # Submit tasks to executor
            futures_to_data = {
                self._executor.submit(self.worker_func, item): (i, item)
                for i, item in enumerate(iterable)
            }

            # Initialize results list with placeholders
            results = [None] * total_items

            # Mark all items as started for progress tracking
            if self._progress_tracker:
                for i in range(total_items):
                    self._progress_tracker.item_started(i)

            # Process results as they complete
            for future in as_completed(futures_to_data):
                # Check if we need to resize the pool
                self._resize_pool_if_needed()

                # Get the result
                idx, item = futures_to_data[future]
                try:
                    result = future.result()
                    results[idx] = result

                    # Update progress tracking
                    if self._progress_tracker:
                        self._progress_tracker.item_completed(idx, success=True)

                except Exception as exc:
                    logger.error(f"Error processing item {idx}: {exc}")
                    results[idx] = None

                    # Update progress tracking
                    if self._progress_tracker:
                        self._progress_tracker.item_completed(idx, success=False)

        finally:
            # Stop progress tracking
            if self._progress_tracker:
                self._progress_tracker.stop()
                self._progress_tracker = None

        return results

    def process(self, work_items: List[T]) -> Dict[T, R]:
        """
        Process items in parallel and return results as a dictionary.

        Args:
            work_items: Items to process

        Returns:
            dict: Results keyed by input items
        """
        # Ensure pool is started
        if not self._executor:
            self.start()

        total_items = len(work_items)

        # Initialize progress tracking if enabled
        if self.track_progress:
            self._progress_tracker = ProgressTracker(
                total_items=total_items,
                callbacks=self._progress_callbacks
            )
            self._progress_tracker.start()

        # Process items
        results = {}

        try:
            # Submit tasks to executor
            futures_to_item = {
                self._executor.submit(self.worker_func, item): item
                for item in work_items
            }

            # Mark all items as started for progress tracking
            if self._progress_tracker:
                for i, item in enumerate(work_items):
                    self._progress_tracker.item_started(item)

            # Process results as they complete
            for future in as_completed(futures_to_item):
                # Check if we need to resize the pool
                self._resize_pool_if_needed()

                # Get the result
                item = futures_to_item[future]
                try:
                    result = future.result()
                    results[item] = result

                    # Update progress tracking
                    if self._progress_tracker:
                        self._progress_tracker.item_completed(item, success=True)

                except Exception as exc:
                    logger.error(f"Error processing item {item}: {exc}")
                    results[item] = None

                    # Update progress tracking
                    if self._progress_tracker:
                        self._progress_tracker.item_completed(item, success=False)

        finally:
            # Stop progress tracking
            if self._progress_tracker:
                self._progress_tracker.stop()
                self._progress_tracker = None

        return results

    def imap(self, iterable: List[T]) -> Iterator[Tuple[int, R]]:
        """
        Process items and yield results as they become available.

        Args:
            iterable: Items to process

        Yields:
            tuple: (index, result) pairs as they complete
        """
        # Ensure pool is started
        if not self._executor:
            self.start()

        total_items = len(iterable)

        # Initialize progress tracking if enabled
        if self.track_progress:
            self._progress_tracker = ProgressTracker(
                total_items=total_items,
                callbacks=self._progress_callbacks
            )
            self._progress_tracker.start()

        try:
            # Submit tasks to executor
            futures_to_data = {
                self._executor.submit(self.worker_func, item): (i, item)
                for i, item in enumerate(iterable)
            }

            # Mark all items as started for progress tracking
            if self._progress_tracker:
                for i in range(total_items):
                    self._progress_tracker.item_started(i)

            # Yield results as they complete
            for future in as_completed(futures_to_data):
                # Check if we need to resize the pool
                self._resize_pool_if_needed()

                # Get the result
                idx, item = futures_to_data[future]
                try:
                    result = future.result()

                    # Update progress tracking
                    if self._progress_tracker:
                        self._progress_tracker.item_completed(idx, success=True)

                    yield (idx, result)

                except Exception as exc:
                    logger.error(f"Error processing item {idx}: {exc}")

                    # Update progress tracking
                    if self._progress_tracker:
                        self._progress_tracker.item_completed(idx, success=False)

                    yield (idx, None)

        finally:
            # Stop progress tracking
            if self._progress_tracker:
                self._progress_tracker.stop()
                self._progress_tracker = None

    @property
    def progress_stats(self) -> Dict[str, Any]:
        """
        Get the current progress statistics.

        Returns:
            dict: Progress statistics
        """
        if self._progress_tracker:
            return self._progress_tracker.last_update
        return {}

    @property
    def resource_stats(self) -> Dict[str, Any]:
        """
        Get the current resource usage statistics.

        Returns:
            dict: Resource usage statistics
        """
        return self.resource_monitor.last_check

    @property
    def current_workers(self) -> int:
        """
        Get the current number of worker processes.

        Returns:
            int: Number of workers
        """
        return self._current_workers

    def __enter__(self):
        """Context manager support: start pool on entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support: stop pool on exit."""
        self.stop()
        return False  # Don't suppress exceptions
