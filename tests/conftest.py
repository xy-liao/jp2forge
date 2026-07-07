"""Shared fixtures: synthetic images with photo-like content.

The images mix smooth gradients with texture noise so they are neither
trivially compressible (flat color) nor incompressible (pure noise),
which keeps rate-targeting tests realistic.
"""

import numpy as np
import pytest
from PIL import Image


@pytest.fixture(scope="session")
def photo_array():
    """8-bit RGB photo-like array (512x512)."""
    rng = np.random.default_rng(42)
    h, w = 512, 512
    yy, xx = np.mgrid[0:h, 0:w]
    base = 128 + 80 * np.sin(xx / 60.0) * np.cos(yy / 45.0)
    texture = rng.normal(0, 12, (h, w, 3))
    return np.clip(base[:, :, None] + texture, 0, 255).astype(np.uint8)


@pytest.fixture(scope="session")
def gray16_array():
    """16-bit grayscale photo-like array (512x512)."""
    rng = np.random.default_rng(7)
    h, w = 512, 512
    yy, xx = np.mgrid[0:h, 0:w]
    base = (128 + 80 * np.sin(xx / 60.0) * np.cos(yy / 45.0)) * 256
    return np.clip(base + rng.normal(0, 3000, (h, w)), 0, 65535).astype(np.uint16)


@pytest.fixture()
def photo_tif(tmp_path, photo_array):
    """Path to an 8-bit RGB TIFF."""
    path = tmp_path / "photo.tif"
    Image.fromarray(photo_array).save(path)
    return str(path)


@pytest.fixture()
def gray16_tif(tmp_path, gray16_array):
    """Path to a 16-bit grayscale (I;16) TIFF."""
    path = tmp_path / "gray16.tif"
    img = Image.fromarray(gray16_array)
    assert img.mode in ("I;16", "I;16L", "I;16B", "I;16N")
    img.save(path)
    return str(path)
