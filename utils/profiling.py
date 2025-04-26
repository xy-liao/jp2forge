"""
Performance profiling module for JP2Forge.

This module provides tools for profiling the performance of
various JP2Forge operations and analyzing bottlenecks.
"""

import os
import time
import json
import logging
import functools
import threading
import tracemalloc
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional, Union
import psutil

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """
    Performance profiler for tracking execution time and memory usage.

    This class provides decorators and context managers for profiling
    code execution and identifying bottlenecks.
    """

    def __init__(
        self,
        output_dir: str = None,
        enabled: bool = True,
        track_memory: bool = True,
        detailed_memory: bool = False
    ):
        """
        Initialize the profiler.

        Args:
            output_dir: Directory for profiling reports
            enabled: Whether profiling is enabled
            track_memory: Whether to track memory usage
            detailed_memory: Whether to use tracemalloc for detailed memory tracking
        """
        self.output_dir = output_dir
        self.enabled = enabled
        self.track_memory = track_memory
        self.detailed_memory = detailed_memory and track_memory
        self._profile_data = []
        self._lock = threading.RLock()
        self._tracemalloc_started = False

        if self.detailed_memory and not tracemalloc.is_tracing():
            tracemalloc.start()
            self._tracemalloc_started = True
            logger.info("Tracemalloc started for detailed memory profiling")

        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        logger.info(
            f"Performance profiler initialized: enabled={enabled}, "
            f"track_memory={track_memory}, detailed_memory={detailed_memory}"
        )

    def __del__(self):
        """Clean up on deletion."""
        if self._tracemalloc_started:
            tracemalloc.stop()

    def profile(self, name: str = None) -> Callable:
        """
        Decorator to profile a function.

        Args:
            name: Optional name for the profiling entry

        Returns:
            Decorator function
        """
        def decorator(func):
            if not self.enabled:
                return func

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                entry_name = name or func.__name__

                # Capture start metrics
                start_time = time.time()
                start_memory = None
                memory_snapshot = None

                if self.track_memory:
                    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    if self.detailed_memory:
                        memory_snapshot = tracemalloc.take_snapshot()

                # Execute function
                try:
                    result = func(*args, **kwargs)
                    status = "success"
                except Exception as e:
                    status = f"error: {str(e)}"
                    raise
                finally:
                    # Capture end metrics
                    end_time = time.time()
                    duration = end_time - start_time

                    profile_entry = {
                        "name": entry_name,
                        "timestamp": datetime.now().isoformat(),
                        "duration": duration,
                        "status": status,
                    }

                    # Add memory metrics if tracking
                    if self.track_memory:
                        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                        memory_delta = end_memory - start_memory
                        profile_entry.update({
                            "start_memory_mb": start_memory,
                            "end_memory_mb": end_memory,
                            "memory_delta_mb": memory_delta
                        })

                        # Add detailed memory stats if enabled
                        if self.detailed_memory and memory_snapshot:
                            end_snapshot = tracemalloc.take_snapshot()
                            top_stats = end_snapshot.compare_to(memory_snapshot, 'lineno')
                            memory_details = []
                            for stat in top_stats[:10]:  # Top 10 allocations
                                memory_details.append({
                                    "file": str(stat.traceback.format()[0]),
                                    "size_delta": stat.size_diff / 1024,  # KB
                                    "size": stat.size / 1024  # KB
                                })
                            profile_entry["memory_details"] = memory_details

                    # Record profile data
                    self._record_profile_data(profile_entry)

                return result

            return wrapper
        return decorator

    def profile_block(self, name: str):
        """
        Context manager for profiling a block of code.

        Args:
            name: Name for the profiling entry

        Returns:
            Context manager
        """
        class ProfileContext:
            def __init__(self_ctx, block_name):
                self_ctx.block_name = block_name
                self_ctx.start_time = None
                self_ctx.start_memory = None
                self_ctx.memory_snapshot = None

            def __enter__(self_ctx):
                if not self.enabled:
                    return self_ctx

                # Capture start metrics
                self_ctx.start_time = time.time()

                if self.track_memory:
                    self_ctx.start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    if self.detailed_memory:
                        self_ctx.memory_snapshot = tracemalloc.take_snapshot()

                return self_ctx

            def __exit__(self_ctx, exc_type, exc_val, exc_tb):
                if not self.enabled:
                    return

                # Capture end metrics
                end_time = time.time()
                duration = end_time - self_ctx.start_time

                status = "success"
                if exc_type:
                    status = f"error: {exc_val}"

                profile_entry = {
                    "name": self_ctx.block_name,
                    "timestamp": datetime.now().isoformat(),
                    "duration": duration,
                    "status": status,
                }

                # Add memory metrics if tracking
                if self.track_memory and self_ctx.start_memory is not None:
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    memory_delta = end_memory - self_ctx.start_memory
                    profile_entry.update({
                        "start_memory_mb": self_ctx.start_memory,
                        "end_memory_mb": end_memory,
                        "memory_delta_mb": memory_delta
                    })

                    # Add detailed memory stats if enabled
                    if self.detailed_memory and self_ctx.memory_snapshot:
                        end_snapshot = tracemalloc.take_snapshot()
                        top_stats = end_snapshot.compare_to(self_ctx.memory_snapshot, 'lineno')
                        memory_details = []
                        for stat in top_stats[:10]:  # Top 10 allocations
                            memory_details.append({
                                "file": str(stat.traceback.format()[0]),
                                "size_delta": stat.size_diff / 1024,  # KB
                                "size": stat.size / 1024  # KB
                            })
                        profile_entry["memory_details"] = memory_details

                # Record profile data
                self._record_profile_data(profile_entry)

        return ProfileContext(name)

    def _record_profile_data(self, entry: Dict[str, Any]) -> None:
        """Record profile data entry."""
        with self._lock:
            self._profile_data.append(entry)

            # Log the entry
            duration = entry.get("duration", 0)
            memory_delta = entry.get("memory_delta_mb", "N/A")
            memory_str = f", memory delta: {memory_delta:.2f} MB" if memory_delta != "N/A" else ""

            logger.debug(
                f"Profile: {entry['name']} took {duration:.4f}s{memory_str}"
            )

    def mark_event(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark a profiling event.

        Args:
            name: Name of the event
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        entry = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "type": "event"
        }

        if metadata:
            entry["metadata"] = metadata

        self._record_profile_data(entry)

    def get_profile_data(self) -> List[Dict[str, Any]]:
        """Get all profile data."""
        with self._lock:
            return self._profile_data.copy()

    def reset(self) -> None:
        """Reset profiling data."""
        with self._lock:
            self._profile_data = []

    def save_report(self, filename: Optional[str] = None) -> str:
        """
        Save profiling data to a JSON file.

        Args:
            filename: Optional filename, defaults to timestamp

        Returns:
            str: Path to the saved report
        """
        if not self.output_dir:
            raise ValueError("Output directory not specified")

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"profile_report_{timestamp}.json"

        output_path = os.path.join(self.output_dir, filename)

        with open(output_path, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "entries": self.get_profile_data(),
                "summary": self.get_summary()
            }, f, indent=2)

        logger.info(f"Saved profile report to {output_path}")
        return output_path

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of profiling data.

        Returns:
            Dict summarizing profiling information
        """
        data = self.get_profile_data()

        if not data:
            return {"entries": 0}

        # Group entries by name
        entries_by_name = {}
        for entry in data:
            if entry.get("type") == "event":
                continue

            name = entry.get("name", "unknown")
            if name not in entries_by_name:
                entries_by_name[name] = []
            entries_by_name[name].append(entry)

        # Calculate statistics for each group
        summary = {
            "entries": len(data),
            "functions": {}
        }

        for name, entries in entries_by_name.items():
            durations = [e.get("duration", 0) for e in entries]
            total_duration = sum(durations)
            avg_duration = total_duration / len(entries)
            max_duration = max(durations)
            min_duration = min(durations)

            func_summary = {
                "count": len(entries),
                "total_duration": total_duration,
                "avg_duration": avg_duration,
                "max_duration": max_duration,
                "min_duration": min_duration
            }

            # Add memory stats if available
            memory_deltas = [e.get("memory_delta_mb") for e in entries if "memory_delta_mb" in e]
            if memory_deltas:
                func_summary.update({
                    "total_memory_delta": sum(memory_deltas),
                    "avg_memory_delta": sum(memory_deltas) / len(memory_deltas),
                    "max_memory_delta": max(memory_deltas),
                    "min_memory_delta": min(memory_deltas)
                })

            summary["functions"][name] = func_summary

        return summary


# Global profiler instance for convenience
_global_profiler = None


def get_profiler(output_dir: Optional[str] = None, **kwargs) -> PerformanceProfiler:
    """
    Get or create the global profiler instance.

    Args:
        output_dir: Optional output directory for reports
        **kwargs: Additional parameters for the profiler

    Returns:
        Global profiler instance
    """
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = PerformanceProfiler(output_dir=output_dir, **kwargs)
    return _global_profiler


def profile(name: Optional[str] = None) -> Callable:
    """
    Decorator for profiling a function using the global profiler.

    Args:
        name: Optional name for the profiling entry

    Returns:
        Decorated function
    """
    profiler = get_profiler()
    return profiler.profile(name)


def profile_block(name: str):
    """
    Context manager for profiling a code block using the global profiler.

    Args:
        name: Name for the profiling entry

    Returns:
        Context manager
    """
    profiler = get_profiler()
    return profiler.profile_block(name)


def mark_event(name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Mark a profiling event using the global profiler.

    Args:
        name: Name of the event
        metadata: Additional metadata
    """
    profiler = get_profiler()
    profiler.mark_event(name, metadata)


def save_report(filename: Optional[str] = None) -> str:
    """
    Save a profiling report using the global profiler.

    Args:
        filename: Optional filename

    Returns:
        Path to the saved report
    """
    profiler = get_profiler()
    return profiler.save_report(filename)


def get_summary() -> Dict[str, Any]:
    """
    Get a summary of profiling data from the global profiler.

    Returns:
        Dict summarizing profiling information
    """
    profiler = get_profiler()
    return profiler.get_summary()


def reset() -> None:
    """Reset the global profiler."""
    profiler = get_profiler()
    profiler.reset()
