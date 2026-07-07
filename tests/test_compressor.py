"""Conversion tests for JPEG2000Compressor (no ExifTool required)."""

import os

import numpy as np
import pytest
from PIL import Image

from core.compressor import JPEG2000Compressor
from core.types import CompressionMode, DocumentType


@pytest.fixture()
def compressor():
    return JPEG2000Compressor(num_resolutions=6)


class TestLossless:
    def test_rgb_roundtrip_bit_identical(self, compressor, photo_tif, tmp_path):
        # Lossless mode used to apply rate-based quality layers, which
        # made the encoder discard data despite the reversible wavelet
        out = str(tmp_path / "out.jp2")
        assert compressor.convert_to_jp2(
            photo_tif, out, DocumentType.PHOTOGRAPH, CompressionMode.LOSSLESS)
        orig = np.array(Image.open(photo_tif))
        conv = np.array(Image.open(out))
        assert np.array_equal(orig, conv)

    def test_16bit_roundtrip_bit_identical(self, compressor, gray16_tif, tmp_path):
        out = str(tmp_path / "out16.jp2")
        assert compressor.convert_to_jp2(
            gray16_tif, out, DocumentType.GRAYSCALE, CompressionMode.LOSSLESS)
        orig = np.array(Image.open(gray16_tif))
        conv = np.array(Image.open(out))
        assert orig.dtype == conv.dtype == np.uint16
        assert np.array_equal(orig, conv)


class Test16BitPreservation:
    def test_16bit_mode_preserved_in_lossy(self, compressor, gray16_tif, tmp_path):
        # 16-bit grayscale used to be silently converted to 8-bit RGB
        out = str(tmp_path / "out.jp2")
        assert compressor.convert_to_jp2(
            gray16_tif, out, DocumentType.GRAYSCALE, CompressionMode.SUPERVISED,
            lossless_fallback=False)
        assert Image.open(out).mode in ("I;16", "I;16L", "I;16B", "I;16N")


class TestBnFRatio:
    def test_photograph_hits_4_to_1(self, compressor, photo_tif, tmp_path):
        # BnF mode used to encode at a fixed ~20:1 and then fail its own
        # 4:1 ratio check, silently falling back to lossless
        out = str(tmp_path / "bnf.jp2")
        assert compressor.convert_to_jp2(
            photo_tif, out, DocumentType.PHOTOGRAPH, CompressionMode.BNF_COMPLIANT,
            lossless_fallback=False)
        with Image.open(photo_tif) as img:
            raw_size = img.size[0] * img.size[1] * len(img.getbands())
        ratio = raw_size / os.path.getsize(out)
        assert 4.0 * 0.95 <= ratio <= 4.0 * 1.05

    def test_grayscale_hits_16_to_1(self, compressor, photo_tif, tmp_path):
        out = str(tmp_path / "bnf_gray.jp2")
        assert compressor.convert_to_jp2(
            photo_tif, out, DocumentType.GRAYSCALE, CompressionMode.BNF_COMPLIANT,
            lossless_fallback=False)
        with Image.open(photo_tif) as img:
            raw_size = img.size[0] * img.size[1] * len(img.getbands())
        ratio = raw_size / os.path.getsize(out)
        assert 16.0 * 0.95 <= ratio <= 16.0 * 1.05
