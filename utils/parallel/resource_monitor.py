"""
Resource monitoring functionality for parallel processing.

This module provides tools to monitor system resources like CPU, memory,
and disk usage to inform adaptive parallel processing decisions.

NOTE: This module duplicates functionality from utils/resource_monitor.py
and is currently unused in the main codebase. Consider consolidation.
"""

import os
import time
import logging
import threading
import psutil
from typing import Dict, Any, Optional, Callable, List

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """
    Monitors system resources and provides usage metrics.

    This class tracks CPU, memory, and disk usage to help with
    making decisions about parallel processing capacity.
    """

    def __init__(
        self,
        check_interval: float = 1.0,
        memory_high_threshold: float = 0.85,
        memory_critical_threshold: float = 0.95,
        cpu_high_threshold: float = 0.85,
        callbacks: Optional[List[Callable[[Dict[str, Any]], None]]] = None
    ):
        """
        Initialize the resource monitor.

        Args:
            check_interval: Seconds between resource checks
            memory_high_threshold: Memory usage ratio considered high (0.0-1.0)
            memory_critical_threshold: Memory usage ratio considered critical (0.0-1.0)
            cpu_high_threshold: CPU usage ratio considered high (0.0-1.0)
            callbacks: Functions to call with resource data on each update
        """
        self.check_interval = check_interval
        self.memory_high_threshold = memory_high_threshold
        self.memory_critical_threshold = memory_critical_threshold
        self.cpu_high_threshold = cpu_high_threshold
        self.callbacks = callbacks or []

        # Internal state
        self._monitoring = False
        self._monitor_thread = None
        self._lock = threading.RLock()
        self._last_check = {}

        logger.debug("ResourceMonitor initialized")

    def start(self) -> None:
        """
        Start the resource monitoring thread.
        """
        with self._lock:
            if self._monitoring:
                return

            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self._monitor_thread.start()
            logger.info("ResourceMonitor started")

    def stop(self) -> None:
        """
        Stop the resource monitoring thread.
        """
        with self._lock:
            self._monitoring = False

            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=2.0)

            self._monitor_thread = None
            logger.info("ResourceMonitor stopped")

    def _monitor_loop(self) -> None:
        """
        Main monitoring loop that periodically checks resources.
        """
        while self._monitoring:
            try:
                # Get current resource usage
                metrics = self.get_resource_usage()

                # Store for external access
                with self._lock:
                    self._last_check = metrics

                # Execute callbacks with the metrics
                for callback in self.callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        logger.error(f"Error in resource monitor callback: {e}")

                # Log warnings for high usage
                self._log_warnings(metrics)

            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")

            # Sleep until next check
            time.sleep(self.check_interval)

    def _log_warnings(self, metrics: Dict[str, Any]) -> None:
        """
        Log warnings if resource usage is high.

        Args:
            metrics: Current resource metrics
        """
        # Memory warnings
        if metrics['memory_percent'] >= self.memory_critical_threshold * 100:
            logger.warning(f"CRITICAL: Memory usage at {metrics['memory_percent']:.1f}%")
        elif metrics['memory_percent'] >= self.memory_high_threshold * 100:
            logger.info(f"HIGH: Memory usage at {metrics['memory_percent']:.1f}%")

        # CPU warnings
        if metrics['cpu_percent'] >= self.cpu_high_threshold * 100:
            logger.info(f"HIGH: CPU usage at {metrics['cpu_percent']:.1f}%")

    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Get current system resource usage metrics.

        Returns:
            dict: Resource usage metrics
        """
        # Get memory information
        memory = psutil.virtual_memory()

        # Get CPU information (interval=0.1 for a quick check)
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Get disk information for the working directory
        disk = psutil.disk_usage(os.getcwd())

        metrics = {
            'timestamp': time.time(),
            'memory_total': memory.total,
            'memory_available': memory.available,
            'memory_used': memory.used,
            'memory_percent': memory.percent,
            'cpu_percent': cpu_percent,
            'cpu_count': psutil.cpu_count(),
            'cpu_count_physical': psutil.cpu_count(logical=False),
            'disk_total': disk.total,
            'disk_used': disk.used,
            'disk_free': disk.free,
            'disk_percent': disk.percent,
            'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
        }

        # Calculate available worker capacity based on memory and CPU
        memory_capacity = max(0, 1.0 - (memory.percent / 100) / self.memory_high_threshold)
        cpu_capacity = max(0, 1.0 - (cpu_percent / 100) / self.cpu_high_threshold)
        metrics['worker_capacity'] = min(memory_capacity, cpu_capacity)

        return metrics

    @property
    def last_check(self) -> Dict[str, Any]:
        """
        Get the latest resource check results.

        Returns:
            dict: Latest resource metrics
        """
        with self._lock:
            return self._last_check.copy() if self._last_check else self.get_resource_usage()

    def is_memory_critical(self) -> bool:
        """
        Check if memory usage is at a critical level.

        Returns:
            bool: True if memory usage is critical
        """
        metrics = self.last_check
        return metrics.get('memory_percent', 0) >= self.memory_critical_threshold * 100

    def is_memory_high(self) -> bool:
        """
        Check if memory usage is at a high level.

        Returns:
            bool: True if memory usage is high
        """
        metrics = self.last_check
        return metrics.get('memory_percent', 0) >= self.memory_high_threshold * 100

    def get_recommended_workers(self, max_workers: int) -> int:
        """
        Get the recommended number of worker processes based on current resources.

        Args:
            max_workers: Maximum number of workers requested

        Returns:
            int: Recommended number of workers
        """
        metrics = self.last_check
        capacity = metrics.get('worker_capacity', 1.0)

        # Start with CPU count as a base
        physical_cpus = metrics.get('cpu_count_physical', 1)
        base_workers = max(1, physical_cpus - 1)  # Leave one CPU free

        # Adjust based on capacity
        recommended = int(max(1, base_workers * capacity))

        # Cap at max_workers
        return min(recommended, max_workers)
