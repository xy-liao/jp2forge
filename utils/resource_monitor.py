#!/usr/bin/env python3
"""
Resource monitoring utilities for adaptive worker pool scaling.

This module provides functions to monitor CPU and memory usage
to enable dynamic adjustment of the worker pool size.
"""

import os
import time
import logging
import threading
import platform
import multiprocessing
import psutil
from typing import Callable, Dict, Any, Optional, List

# Set up logger
logger = logging.getLogger("jp2forge.resource_monitor")


class ResourceMonitor:
    """
    Monitor system resources (CPU and memory) to enable adaptive worker pool scaling.
    """
    
    # Use class variables to store state shared between processes
    # This avoids pickling issues by ensuring these values are initialized in each process
    _shared_current_workers = None
    _monitoring = False
    
    def __init__(
        self,
        min_workers: int = 1,
        max_workers: int = multiprocessing.cpu_count() - 1,
        memory_threshold: float = 0.8,
        cpu_threshold: float = 0.9,
        memory_limit_mb: int = 4096,
        check_interval: float = 2.0
    ):
        """
        Initialize the resource monitor.
        
        Args:
            min_workers (int): Minimum number of workers to use
            max_workers (int): Maximum number of workers to use
            memory_threshold (float): Memory usage threshold (0-1) to trigger scaling
            cpu_threshold (float): CPU usage threshold (0-1) to trigger scaling
            memory_limit_mb (int): Memory limit in MB as a hard cap
            check_interval (float): How often to check resource usage in seconds
        """
        self.min_workers = max(1, min_workers)
        self.max_workers = max(self.min_workers, max_workers)
        self.memory_threshold = max(0.1, min(1.0, memory_threshold))
        self.cpu_threshold = max(0.1, min(1.0, cpu_threshold))
        self.memory_limit_mb = memory_limit_mb
        self.check_interval = check_interval
        
        # Initialize the shared counter if not already set
        if ResourceMonitor._shared_current_workers is None:
            ResourceMonitor._shared_current_workers = multiprocessing.Value('i', self.max_workers)
        
        # Set initial current workers
        with ResourceMonitor._shared_current_workers.get_lock():
            ResourceMonitor._shared_current_workers.value = self.max_workers
        
        # System info (these don't need to be shared between processes)
        self._total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
        self._total_cpu_cores = multiprocessing.cpu_count()
        
        # Thread for monitoring resources
        self._monitor_thread = None
        
        # Log initial configuration
        logger.info(f"ResourceMonitor initialized: min_workers={self.min_workers}, "
                   f"max_workers={self.max_workers}, memory_threshold={self.memory_threshold}, "
                   f"cpu_threshold={self.cpu_threshold}")
        logger.info(f"System has {self._total_cpu_cores} CPU cores and "
                  f"{self._total_memory_mb:.0f}MB total memory")
    
    def start(self):
        """Start the resource monitoring thread."""
        if ResourceMonitor._monitoring:
            logger.warning("Resource monitor is already running")
            return
        
        ResourceMonitor._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_resources,
            daemon=True,
            name="ResourceMonitor"
        )
        self._monitor_thread.start()
        logger.info("Resource monitor started")
    
    def stop(self):
        """Stop the resource monitoring thread."""
        if not ResourceMonitor._monitoring:
            logger.warning("Resource monitor is not running")
            return
        
        ResourceMonitor._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=3.0)
        logger.info("Resource monitor stopped")
    
    def get_recommended_workers(self) -> int:
        """
        Get the currently recommended number of workers based on resource usage.
        
        Returns:
            int: Recommended number of workers
        """
        # This method can be called from any process
        if ResourceMonitor._shared_current_workers is not None:
            return ResourceMonitor._shared_current_workers.value
        else:
            # Fallback if shared value not initialized
            return self.max_workers
    
    def _monitor_resources(self):
        """Background thread to monitor system resources and adjust worker count."""
        while ResourceMonitor._monitoring:
            try:
                self._check_and_adjust()
            except Exception as e:
                logger.error(f"Error monitoring resources: {str(e)}")
            
            # Sleep until next check
            time.sleep(self.check_interval)
    
    def _check_and_adjust(self):
        """Check resource usage and adjust worker count if needed."""
        # Get current resource usage
        cpu_usage = psutil.cpu_percent(interval=None) / 100.0
        memory_usage = psutil.virtual_memory().percent / 100.0
        used_memory_mb = psutil.virtual_memory().used / (1024 * 1024)
        
        # Calculate how close we are to the limits
        cpu_headroom = max(0, self.cpu_threshold - cpu_usage) / self.cpu_threshold
        memory_headroom = max(0, self.memory_threshold - memory_usage) / self.memory_threshold
        
        # Use the more constrained resource to determine scaling
        headroom = min(cpu_headroom, memory_headroom)
        
        # Also consider the memory limit as a hard cap
        memory_limit_headroom = max(0, 1.0 - (used_memory_mb / self.memory_limit_mb))
        headroom = min(headroom, memory_limit_headroom)
        
        # Calculate target worker count based on headroom
        if ResourceMonitor._shared_current_workers is None:
            return
            
        current_workers = ResourceMonitor._shared_current_workers.value
        
        if headroom < 0.1:  # Very low headroom, scale down more aggressively
            target_workers = max(self.min_workers, int(current_workers * 0.6))
        elif headroom < 0.3:  # Low headroom, scale down
            target_workers = max(self.min_workers, int(current_workers * 0.8))
        elif headroom > 0.5:  # High headroom, can scale up
            target_workers = min(self.max_workers, int(current_workers * 1.2) + 1)
        else:  # Adequate headroom, maintain current count
            target_workers = current_workers
        
        # Ensure we're within bounds
        target_workers = max(self.min_workers, min(self.max_workers, target_workers))
        
        # Update if changed
        if target_workers != current_workers:
            old_count = current_workers
            with ResourceMonitor._shared_current_workers.get_lock():
                ResourceMonitor._shared_current_workers.value = target_workers
            
            logger.info(
                f"Adjusting worker count: {old_count} → {target_workers} "
                f"(CPU: {cpu_usage:.2f}, Mem: {memory_usage:.2f}, Headroom: {headroom:.2f})"
            )


def get_system_info() -> Dict[str, Any]:
    """
    Get system information including CPU, memory, and OS details.
    
    Returns:
        Dict[str, Any]: System information
    """
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": multiprocessing.cpu_count(),
        "cpu_freq": psutil.cpu_freq() if hasattr(psutil, "cpu_freq") else None,
        "total_memory_mb": psutil.virtual_memory().total / (1024 * 1024),
        "available_memory_mb": psutil.virtual_memory().available / (1024 * 1024),
        "memory_percent": psutil.virtual_memory().percent,
    }


if __name__ == "__main__":
    # Simple test code when run directly
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    monitor = ResourceMonitor(
        min_workers=1,
        max_workers=8,
        memory_threshold=0.7,
        cpu_threshold=0.8
    )
    
    # Print system info
    print("System Information:")
    for key, value in get_system_info().items():
        print(f"  {key}: {value}")
    
    # Start monitoring
    monitor.start()
    
    try:
        print("Monitor running. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
            print(f"Current recommended workers: {monitor.get_recommended_workers()}")
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop()