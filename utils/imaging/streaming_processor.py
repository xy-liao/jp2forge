"""
Streaming image processor for memory-efficient processing.

This module provides a processor that can work with large images
by processing them in chunks to reduce memory usage.
"""

import os
import logging
import tempfile
import gc
import weakref
import time
import heapq
import threading
from typing import Tuple, Optional, Dict, Any, List, Callable, BinaryIO, NamedTuple, Set
from PIL import Image, ImageFile
import numpy as np
import psutil

from utils.imaging.memory_estimator import (
    estimate_memory_usage,
    calculate_optimal_chunk_size,
    estimate_image_file_memory
)

logger = logging.getLogger(__name__)

# Enable streaming for PIL (process large images in chunks)
ImageFile.LOAD_TRUNCATED_IMAGES = True


class MemoryBlockInfo(NamedTuple):
    """Information about a memory block for priority queue handling."""
    last_used: float  # Timestamp when the block was last used
    size_mb: int      # Size of the block in MB
    block_id: int     # Unique identifier for the block


class MemoryPoolStats:
    """Statistics for memory pool usage tracking."""

    def __init__(self):
        self.total_allocations = 0
        self.total_releases = 0
        self.peak_blocks_used = 0
        self.total_size_mb = 0
        self.hits = 0  # When a block is successfully reused
        self.misses = 0  # When a new block needs to be allocated
        self.start_time = time.time()

    def add_allocation(self, size_mb: int):
        self.total_allocations += 1
        self.total_size_mb += size_mb

    def add_release(self):
        self.total_releases += 1

    def add_hit(self):
        self.hits += 1

    def add_miss(self):
        self.misses += 1

    def update_peak_usage(self, current_blocks_used: int):
        self.peak_blocks_used = max(self.peak_blocks_used, current_blocks_used)

    @property
    def usage_duration(self) -> float:
        return time.time() - self.start_time

    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0

    def __str__(self) -> str:
        return (
            f"Memory Pool Stats:\n"
            f"- Duration: {self.usage_duration:.2f} seconds\n"
            f"- Allocations: {self.total_allocations}\n"
            f"- Releases: {self.total_releases}\n"
            f"- Hit ratio: {self.hit_ratio*100:.1f}%\n"
            f"- Total size: {self.total_size_mb} MB\n"
            f"- Peak blocks: {self.peak_blocks_used}"
        )


class MemoryPool:
    """
    Optimized memory pool implementation to reduce memory fragmentation.

    This class pre-allocates memory blocks that can be reused
    for image processing operations, reducing the overhead
    of frequent memory allocations and deallocations. It supports
    dynamic block sizes, efficient allocation through LRU priority,
    and detailed usage statistics.
    """

    def __init__(
        self,
        initial_size_mb: int = 100,
        max_blocks: int = 10,
        min_block_size_mb: int = 16,
        max_block_size_mb: int = 512,
        enable_stats: bool = True
    ):
        """
        Initialize the memory pool.

        Args:
            initial_size_mb: Initial size of each memory block in MB
            max_blocks: Maximum number of memory blocks to allocate
            min_block_size_mb: Minimum block size in MB for dynamic sizing
            max_block_size_mb: Maximum block size in MB for dynamic sizing
            enable_stats: Whether to track memory usage statistics
        """
        self.min_block_size_mb = min_block_size_mb
        self.max_block_size_mb = max_block_size_mb
        self.default_block_size_mb = min(max(initial_size_mb, min_block_size_mb), max_block_size_mb)
        self.max_blocks = max_blocks
        self._blocks = {}  # Dictionary of block_id -> block
        self._block_sizes = {}  # Dictionary of block_id -> size in bytes
        self._in_use = set()  # Set of in-use block IDs
        self._free_blocks = []  # Priority queue of (last_used, size_mb, block_id)
        self._next_block_id = 0
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._enable_stats = enable_stats
        self._stats = MemoryPoolStats() if enable_stats else None

        # Pre-allocate first block
        self._create_block(self.default_block_size_mb)

        logger.info(
            f"Initialized optimized memory pool with initial block size: {self.default_block_size_mb}MB, "
            f"max blocks: {max_blocks}, dynamic sizing: {min_block_size_mb}-{max_block_size_mb}MB"
        )

    def _create_block(self, size_mb: int) -> int:
        """
        Create a new memory block and return its ID.

        Args:
            size_mb: Size of the memory block in MB

        Returns:
            int: Block ID or -1 if creation failed
        """
        with self._lock:
            if len(self._blocks) >= self.max_blocks:
                return -1

            # Create block and add to pool
            try:
                size_bytes = size_mb * 1024 * 1024
                block = bytearray(size_bytes)
                block_id = self._next_block_id
                self._next_block_id += 1

                self._blocks[block_id] = block
                self._block_sizes[block_id] = size_bytes

                # Add to free blocks with current timestamp
                heapq.heappush(
                    self._free_blocks,
                    MemoryBlockInfo(time.time(), size_mb, block_id)
                )

                if self._enable_stats:
                    self._stats.add_allocation(size_mb)

                logger.debug(f"Created memory block {block_id} of size {size_mb}MB")
                return block_id
            except MemoryError:
                logger.error(f"Failed to allocate memory block of size {size_mb}MB")
                return -1

    def _find_best_fit_block(self, required_size_bytes: int) -> int:
        """
        Find the best block that fits the required size using a best-fit approach.

        Args:
            required_size_bytes: Minimum size needed in bytes

        Returns:
            int: Block ID or -1 if no suitable block found
        """
        if not self._free_blocks:
            return -1

        best_block_id = -1
        best_block_size = float('inf')
        best_block_idx = -1

        # Find the smallest block that fits the requirement
        for i, block_info in enumerate(self._free_blocks):
            size_bytes = block_info.size_mb * 1024 * 1024
            if (size_bytes >= required_size_bytes and
                    size_bytes < best_block_size):
                best_block_size = size_bytes
                best_block_id = block_info.block_id
                best_block_idx = i

        # If we found a suitable block, remove it from the free list
        if best_block_idx != -1:
            self._free_blocks.pop(best_block_idx)
            heapq.heapify(self._free_blocks)  # Reheapify after removal
            return best_block_id

        return -1

    def get_block(self, size_bytes: Optional[int] = None) -> Tuple[int, Optional[bytearray]]:
        """
        Get an available memory block that meets the size requirement.

        Args:
            size_bytes: Required size in bytes, or None to use default size

        Returns:
            tuple: (block_id, block) or (-1, None) if no blocks available
        """
        with self._lock:
            required_size = size_bytes or (self.default_block_size_mb * 1024 * 1024)
            required_size_mb = required_size // (1024 * 1024) + 1  # Round up to MB

            # Try to find existing block that fits
            if self._free_blocks:
                # First, try best-fit approach
                block_id = self._find_best_fit_block(required_size)

                # If that fails, use oldest block if it's big enough
                if block_id == -1 and self._free_blocks:
                    oldest_block = heapq.heappop(self._free_blocks)
                    if oldest_block.size_mb * 1024 * 1024 >= required_size:
                        block_id = oldest_block.block_id
                    else:
                        # Put it back if it's too small
                        heapq.heappush(self._free_blocks, oldest_block)
                        block_id = -1

                if block_id >= 0:
                    self._in_use.add(block_id)

                    if self._enable_stats:
                        self._stats.add_hit()
                        self._stats.update_peak_usage(len(self._in_use))

                    logger.debug(
                        f"Reused memory block {block_id} of size {self._block_sizes[block_id]/1024/1024:.1f}MB")
                    return block_id, self._blocks[block_id]

            # No suitable existing blocks, try to create a new one
            if self._enable_stats:
                self._stats.add_miss()

            # Dynamically size the new block based on the requirement
            size_mb = max(
                self.min_block_size_mb,
                min(required_size_mb, self.max_block_size_mb)
            )

            block_id = self._create_block(size_mb)
            if block_id >= 0:
                self._in_use.add(block_id)

                if self._enable_stats:
                    self._stats.update_peak_usage(len(self._in_use))

                return block_id, self._blocks[block_id]

            # All blocks in use and at max capacity, check if we can resize
            current_system_memory = psutil.virtual_memory()
            if (current_system_memory.percent < 75 and
                    current_system_memory.available > (required_size * 2)):
                # Attempt to create an oversized block for this specific request
                logger.warning(f"Creating temporary oversized block of {required_size_mb}MB")
                temp_block_id = self._next_block_id
                self._next_block_id += 1

                try:
                    temp_block = bytearray(required_size)
                    self._blocks[temp_block_id] = temp_block
                    self._block_sizes[temp_block_id] = required_size
                    self._in_use.add(temp_block_id)

                    if self._enable_stats:
                        self._stats.add_allocation(required_size_mb)
                        self._stats.update_peak_usage(len(self._in_use))

                    return temp_block_id, temp_block
                except MemoryError:
                    logger.error(f"Failed to allocate oversized block of {required_size_mb}MB")
                    pass

            # Memory pool truly exhausted
            logger.warning(f"Memory pool exhausted, all blocks in use. Need {required_size_mb}MB")
            return -1, None

    def release_block(self, block_id: int) -> None:
        """
        Release a memory block back to the pool.

        Args:
            block_id: ID of the block to release
        """
        with self._lock:
            if block_id in self._in_use:
                self._in_use.remove(block_id)

                if block_id in self._blocks:
                    # Add back to free blocks priority queue with current timestamp
                    size_mb = self._block_sizes[block_id] // (1024 * 1024)
                    heapq.heappush(
                        self._free_blocks,
                        MemoryBlockInfo(time.time(), size_mb, block_id)
                    )

                    if self._enable_stats:
                        self._stats.add_release()

                    logger.debug(f"Released memory block {block_id} back to pool")

    def resize_pool(self, new_max_blocks: int) -> bool:
        """
        Resize the maximum number of blocks in the pool.

        Args:
            new_max_blocks: New maximum number of blocks

        Returns:
            bool: True if resizing was successful
        """
        with self._lock:
            if new_max_blocks < len(self._in_use):
                logger.warning(
                    f"Cannot resize pool to {new_max_blocks} blocks, "
                    f"{len(self._in_use)} blocks currently in use"
                )
                return False

            self.max_blocks = new_max_blocks
            logger.info(f"Resized memory pool to max {new_max_blocks} blocks")
            return True

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get memory pool statistics.

        Returns:
            dict: Statistics about memory pool usage or None if stats disabled
        """
        if not self._enable_stats or not self._stats:
            return None

        with self._lock:
            return {
                "total_allocations": self._stats.total_allocations,
                "total_releases": self._stats.total_releases,
                "current_blocks_used": len(self._in_use),
                "free_blocks": len(self._free_blocks),
                "total_blocks": len(self._blocks),
                "peak_blocks_used": self._stats.peak_blocks_used,
                "total_size_mb": self._stats.total_size_mb,
                "hit_ratio": self._stats.hit_ratio,
                "usage_duration_seconds": self._stats.usage_duration
            }

    def cleanup(self, force: bool = False) -> None:
        """
        Clean up the memory pool.

        Args:
            force: Force cleanup even if blocks are still in use
        """
        with self._lock:
            if len(self._in_use) > 0 and not force:
                logger.warning(
                    f"Memory pool cleanup attempted while {len(self._in_use)} blocks still in use"
                )
                return

            # Log statistics before cleanup
            if self._enable_stats and self._stats:
                logger.info(f"Memory pool statistics on cleanup:\n{self._stats}")

            # Clear blocks to release memory
            self._blocks.clear()
            self._block_sizes.clear()
            self._in_use.clear()
            self._free_blocks.clear()

            # Reset for potential reuse
            self._next_block_id = 0

            # Force garbage collection
            gc.collect()
            logger.debug("Memory pool cleaned up completely")


class StreamingImageProcessor:
    """
    Process large images efficiently by chunking.

    This class breaks large images into manageable chunks for
    memory-efficient processing and supports various operations
    on the chunks.
    """

    def __init__(
        self,
        memory_limit_mb: Optional[int] = None,
        min_chunk_height: int = 16,
        force_chunking: bool = False,
        temp_dir: Optional[str] = None,
        use_memory_pool: bool = True,
        memory_pool_size_mb: int = 100,
        min_block_size_mb: int = 16,
        max_block_size_mb: int = 512,
        max_memory_blocks: int = 10
    ):
        """
        Initialize the streaming image processor.

        Args:
            memory_limit_mb: Maximum memory to use in MB, or None for auto
            min_chunk_height: Minimum chunk height in pixels
            force_chunking: Always use chunking even for small images
            temp_dir: Directory for temporary files
            use_memory_pool: Whether to use memory pooling
            memory_pool_size_mb: Default size of each memory pool block in MB
            min_block_size_mb: Minimum size for dynamic memory blocks in MB
            max_block_size_mb: Maximum size for dynamic memory blocks in MB
            max_memory_blocks: Maximum number of memory blocks to allocate
        """
        self.memory_limit_mb = memory_limit_mb
        self.min_chunk_height = min_chunk_height
        self.force_chunking = force_chunking
        self.temp_dir = temp_dir
        self.use_memory_pool = use_memory_pool

        # Memory pool configuration
        self.memory_pool_size_mb = memory_pool_size_mb
        self.min_block_size_mb = min_block_size_mb
        self.max_block_size_mb = max_block_size_mb
        self.max_memory_blocks = max_memory_blocks

        # Track temporary files for cleanup
        self._temp_files = []

        # Initialize memory pool if enabled
        self.memory_pool = None
        if use_memory_pool:
            self.initialize_memory_pool(
                memory_pool_size_mb,
                max_memory_blocks,
                min_block_size_mb,
                max_block_size_mb
            )

        logger.info(
            f"StreamingImageProcessor initialized with "
            f"memory_limit: {memory_limit_mb} MB, "
            f"min_chunk_height: {min_chunk_height} px, "
            f"memory_pool: {'enabled' if use_memory_pool else 'disabled'}"
        )

    def initialize_memory_pool(
        self,
        size_mb: int = 100,
        max_blocks: int = 10,
        min_block_size_mb: Optional[int] = None,
        max_block_size_mb: Optional[int] = None
    ) -> None:
        """
        Initialize or reinitialize the memory pool.

        Args:
            size_mb: Default size of each memory block in MB
            max_blocks: Maximum number of memory blocks
            min_block_size_mb: Minimum block size in MB for dynamic sizing
            max_block_size_mb: Maximum block size in MB for dynamic sizing
        """
        if self.memory_pool:
            self.memory_pool.cleanup()

        # Use instance values if not specified
        min_block_size = min_block_size_mb or self.min_block_size_mb
        max_block_size = max_block_size_mb or self.max_block_size_mb

        self.memory_pool = MemoryPool(
            initial_size_mb=size_mb,
            max_blocks=max_blocks,
            min_block_size_mb=min_block_size,
            max_block_size_mb=max_block_size,
            enable_stats=True
        )
        logger.info(
            f"Initialized optimized memory pool with {size_mb}MB default block size, {max_blocks} max blocks")

    def get_memory_pool_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get statistics about memory pool usage.

        Returns:
            dict: Memory usage statistics or None if memory pool is disabled
        """
        if not self.use_memory_pool or not self.memory_pool:
            return None

        return self.memory_pool.get_stats()

    def resize_memory_pool(self, new_max_blocks: int) -> bool:
        """
        Resize the memory pool to accommodate more or fewer blocks.

        Args:
            new_max_blocks: New maximum number of blocks

        Returns:
            bool: True if resizing was successful
        """
        if not self.use_memory_pool or not self.memory_pool:
            logger.warning("Cannot resize memory pool: memory pool is disabled")
            return False

        result = self.memory_pool.resize_pool(new_max_blocks)
        if result:
            self.max_memory_blocks = new_max_blocks

        return result

    def __del__(self):
        """Clean up temporary files on object destruction."""
        self.cleanup()

    def cleanup(self):
        """
        Clean up temporary files and memory pool created during processing.
        """
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"Removed temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_file}: {e}")

        self._temp_files = []

        # Clean up memory pool
        if self.memory_pool:
            self.memory_pool.cleanup()
            self.memory_pool = None

    def _create_temp_file(self, suffix: str = '.tmp') -> str:
        """
        Create a temporary file and track it for cleanup.

        Args:
            suffix: File extension

        Returns:
            str: Path to temporary file
        """
        fd, temp_path = tempfile.mkstemp(suffix=suffix, dir=self.temp_dir)
        os.close(fd)
        self._temp_files.append(temp_path)
        return temp_path

    def should_use_chunking(self, image_path: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Determine if chunking should be used based on image size.

        Args:
            image_path: Path to image file

        Returns:
            tuple: (use_chunking, memory_info)
        """
        # Estimate memory usage
        memory_info = estimate_image_file_memory(image_path)

        # Determine if chunking is needed
        use_chunking = (
            self.force_chunking or
            memory_info['recommended_chunking']
        )

        if use_chunking:
            logger.info(
                f"Using chunked processing for {os.path.basename(image_path)}: "
                f"{memory_info['width']}x{memory_info['height']} "
                f"({memory_info['memory_mb']:.1f} MB estimated)"
            )
        else:
            logger.debug(
                f"Using standard processing for {os.path.basename(image_path)}: "
                f"{memory_info['width']}x{memory_info['height']} "
                f"({memory_info['memory_mb']:.1f} MB estimated)"
            )

        return use_chunking, memory_info

    def _calculate_optimal_block_size(self, width: int, height: int, mode: str) -> int:
        """
        Calculate the optimal memory block size based on image dimensions.

        Args:
            width: Image width in pixels
            height: Image height in pixels
            mode: Image mode (RGB, RGBA, etc.)

        Returns:
            int: Optimal block size in bytes
        """
        # Calculate bytes per pixel based on mode
        bytes_per_pixel = len(mode)
        if mode == 'RGB':
            bytes_per_pixel = 3
        elif mode == 'RGBA':
            bytes_per_pixel = 4
        elif mode == 'L':
            bytes_per_pixel = 1

        # Calculate size for a full-width stripe that's 32 pixels high
        stripe_height = 32
        stripe_size_bytes = width * stripe_height * bytes_per_pixel

        # Add 20% overhead for processing
        block_size_bytes = int(stripe_size_bytes * 1.2)

        # Convert to MB and ensure it's within bounds
        block_size_mb = max(
            self.min_block_size_mb,
            min(block_size_bytes // (1024 * 1024) + 1, self.max_block_size_mb)
        )

        return block_size_mb * 1024 * 1024

    def process_whole_image(
        self,
        input_path: str,
        output_path: str,
        process_function: Callable[[Image.Image], Image.Image],
        save_kwargs: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Process an entire image at once.

        Args:
            input_path: Path to input image
            output_path: Path to save processed image
            process_function: Function to apply to the image
            save_kwargs: Additional arguments for saving the output image

        Returns:
            bool: True if processing was successful
        """
        block_id = -1
        memory_block = None

        try:
            # Open and process the image
            with Image.open(input_path) as img:
                # If using memory pool, try to get a block sized for this image
                if self.use_memory_pool and self.memory_pool:
                    width, height = img.size
                    mode = img.mode
                    optimal_size = self._calculate_optimal_block_size(width, height, mode)
                    block_id, memory_block = self.memory_pool.get_block(optimal_size)

                # Apply processing function
                processed_img = process_function(img)

                # Apply additional save settings if provided
                if save_kwargs is None:
                    save_kwargs = {}

                # Determine format from output path
                output_format = os.path.splitext(output_path)[1][1:].upper()
                if not output_format:
                    output_format = 'PNG'

                # Fix format name for JPEG
                if output_format == 'JPG':
                    output_format = 'JPEG'

                # Save with specified format
                processed_img.save(output_path, format=output_format, **save_kwargs)

            logger.info(
                f"Standard processing completed for {os.path.basename(input_path)} "
                f"-> {os.path.basename(output_path)}"
            )

            return True

        except Exception as e:
            logger.error(f"Error in standard image processing: {e}")
            raise

        finally:
            # Release memory block if used
            if self.memory_pool and block_id >= 0:
                self.memory_pool.release_block(block_id)

    def process_in_chunks(
        self,
        input_path: str,
        output_path: str,
        process_function: Callable[[Image.Image], Image.Image],
        save_kwargs: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Process an image in chunks to reduce memory usage.

        Args:
            input_path: Path to input image
            output_path: Path to save processed image
            process_function: Function to apply to each chunk
            save_kwargs: Additional arguments for saving the output image

        Returns:
            bool: True if processing was successful
        """
        # Check if chunking is needed
        use_chunking, memory_info = self.should_use_chunking(input_path)

        if not use_chunking:
            # Process normally if chunking isn't needed
            return self.process_whole_image(
                input_path, output_path, process_function, save_kwargs
            )

        # Use chunking for large images
        block_id = -1
        memory_block = None

        try:
            # Open the image to get basic information
            with Image.open(input_path) as img:
                width, height = img.size
                mode = img.mode

                # Get memory block if using memory pool - optimally sized for chunks
                if self.use_memory_pool and self.memory_pool:
                    optimal_size = self._calculate_optimal_block_size(width, height, mode)
                    block_id, memory_block = self.memory_pool.get_block(optimal_size)

                # Calculate optimal chunk size based on memory constraints
                chunk_height = calculate_optimal_chunk_size(
                    width, height, mode,
                    memory_limit_mb=self.memory_limit_mb,
                    min_chunk_height=self.min_chunk_height
                )

                logger.debug(f"Using chunk height of {chunk_height} pixels")

                # Create intermediate chunked output
                temp_output = self._create_temp_file('.png')

                # Process image in chunks
                with Image.open(input_path) as src_img:
                    # Create a blank target image with the same dimensions and mode
                    with Image.new(mode, (width, height)) as dst_img:
                        # Process the image in horizontal strips
                        for y_offset in range(0, height, chunk_height):
                            # Calculate the actual height of this chunk
                            current_height = min(chunk_height, height - y_offset)

                            logger.debug(
                                f"Processing chunk at y={y_offset}, "
                                f"height={current_height} ({y_offset/height*100:.1f}%)"
                            )

                            # Extract the chunk as a crop
                            chunk_box = (0, y_offset, width, y_offset + current_height)
                            with src_img.crop(chunk_box) as chunk:
                                # Process the chunk
                                processed_chunk = process_function(chunk)

                                # Paste the processed chunk back into the output image
                                dst_img.paste(processed_chunk, (0, y_offset))

                                # Clean up
                                del processed_chunk

                            # Manual garbage collection after each chunk if not using memory pool
                            if not self.use_memory_pool or block_id < 0:
                                gc.collect()

                        # Save the final result to the temporary file
                        dst_img.save(temp_output, format='PNG')

                # Open the intermediate result and save to the final output format
                with Image.open(temp_output) as result_img:
                    # Apply additional save settings if provided
                    if save_kwargs is None:
                        save_kwargs = {}

                    # Determine format from output path
                    output_format = os.path.splitext(output_path)[1][1:].upper()
                    if not output_format:
                        output_format = 'PNG'

                    # Fix format name for JPEG
                    if output_format == 'JPG':
                        output_format = 'JPEG'

                    # Save with specified format
                    result_img.save(output_path, format=output_format, **save_kwargs)

            logger.info(
                f"Chunked processing completed for {os.path.basename(input_path)} "
                f"-> {os.path.basename(output_path)}"
            )

            return True

        except Exception as e:
            logger.error(f"Error in chunked image processing: {e}")
            raise

        finally:
            # Release memory block
            if self.memory_pool and block_id >= 0:
                self.memory_pool.release_block(block_id)

            # Clean up temporary files from this operation
            for temp_file in self._temp_files[:]:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        self._temp_files.remove(temp_file)
                        logger.debug(f"Removed temporary file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file {temp_file}: {e}")

    # Other methods remain unchanged
