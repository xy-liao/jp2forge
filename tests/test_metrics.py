"""Unit tests for the quality metrics in utils.image.

These pin down historical bugs: integer wraparound in MSE, the 8-bit
peak assumption in PSNR, and a non-windowed SSIM.
"""

import numpy as np
import pytest

from utils.image import (
    calculate_mse,
    calculate_psnr,
    calculate_ssim,
    peak_signal_value,
)


class TestMSE:
    def test_uniform_difference_no_wraparound(self):
        # A uniform error of 50 levels used to report MSE 196 instead of
        # 2500 because uint8 subtraction wraps modulo 256
        orig = np.full((64, 64), 100, dtype=np.uint8)
        conv = np.full((64, 64), 150, dtype=np.uint8)
        assert calculate_mse(orig, conv) == pytest.approx(2500.0)

    def test_symmetry(self):
        rng = np.random.default_rng(0)
        a = rng.integers(0, 256, (32, 32), dtype=np.uint8)
        b = rng.integers(0, 256, (32, 32), dtype=np.uint8)
        assert calculate_mse(a, b) == pytest.approx(calculate_mse(b, a))

    def test_identical_is_zero(self):
        a = np.arange(256, dtype=np.uint8).reshape(16, 16)
        assert calculate_mse(a, a.copy()) == pytest.approx(0.0, abs=0.0)

    def test_16bit_scale(self):
        orig = np.full((32, 32), 1000, dtype=np.uint16)
        conv = np.full((32, 32), 2000, dtype=np.uint16)
        assert calculate_mse(orig, conv) == pytest.approx(1000.0 ** 2)

    def test_shape_mismatch_raises(self):
        with pytest.raises(ValueError, match="shapes do not match"):
            calculate_mse(np.zeros((4, 4)), np.zeros((4, 5)))


class TestPSNR:
    def test_zero_mse_is_infinite(self):
        assert calculate_psnr(0.0) == float("inf")

    def test_8bit_reference_value(self):
        # MSE of 2500 on the 8-bit scale: 20*log10(255/50) ~= 14.15 dB
        assert calculate_psnr(2500.0) == pytest.approx(14.15, abs=0.01)

    def test_16bit_peak(self):
        # The same relative error must give the same PSNR at 16 bits;
        # with the old hardcoded 255 peak this reported ~0 dB
        mse_16 = (50.0 * 257) ** 2
        assert calculate_psnr(mse_16, max_pixel=65535.0) == pytest.approx(
            14.15, abs=0.02)

    def test_peak_signal_value_dtypes(self):
        assert peak_signal_value(np.zeros((2, 2), dtype=np.uint8)) == pytest.approx(255.0, abs=0.0)
        assert peak_signal_value(np.zeros((2, 2), dtype=np.uint16)) == pytest.approx(65535.0, abs=0.0)


class TestSSIM:
    def test_identical_is_one(self):
        rng = np.random.default_rng(1)
        a = rng.integers(0, 256, (64, 64), dtype=np.uint8)
        assert calculate_ssim(a, a.copy()) == pytest.approx(1.0)

    def test_shuffled_structure_is_near_zero(self):
        # Same histogram, destroyed structure: a global (non-windowed)
        # formula cannot distinguish this reliably
        rng = np.random.default_rng(2)
        a = rng.integers(0, 256, (128, 128), dtype=np.uint8)
        b = a.copy()
        rng.shuffle(b.reshape(-1))
        assert calculate_ssim(a, b) < 0.1

    def test_blur_scores_lower_than_light_noise(self, photo_array):
        rng = np.random.default_rng(3)
        gray = photo_array[:, :, 0]
        noisy = np.clip(
            gray.astype(np.int32) + rng.integers(-3, 4, gray.shape), 0, 255
        ).astype(np.uint8)
        # crude 5x5 box blur without scipy
        padded = np.pad(gray.astype(np.float64), 2, mode="edge")
        blurred = np.zeros_like(gray, dtype=np.float64)
        for dy in range(5):
            for dx in range(5):
                blurred += padded[dy:dy + gray.shape[0], dx:dx + gray.shape[1]]
        blurred = (blurred / 25).astype(np.uint8)
        assert calculate_ssim(gray, blurred) < calculate_ssim(gray, noisy)

    def test_multichannel(self, photo_array):
        rng = np.random.default_rng(4)
        noisy = np.clip(
            photo_array.astype(np.int32) + rng.integers(-5, 6, photo_array.shape),
            0, 255,
        ).astype(np.uint8)
        score = calculate_ssim(photo_array, noisy)
        assert 0.8 < score < 1.0

    def test_16bit_input(self, gray16_array):
        rng = np.random.default_rng(5)
        noisy = np.clip(
            gray16_array.astype(np.int64) + rng.integers(-500, 501, gray16_array.shape),
            0, 65535,
        ).astype(np.uint16)
        score = calculate_ssim(gray16_array, noisy)
        assert 0.9 < score <= 1.0

    def test_tiny_image_does_not_crash(self):
        a = np.arange(25, dtype=np.uint8).reshape(5, 5)
        assert 0.0 < calculate_ssim(a, a.copy()) <= 1.0

    def test_shape_mismatch_raises(self):
        with pytest.raises(ValueError, match="shapes do not match"):
            calculate_ssim(np.zeros((8, 8)), np.zeros((9, 9)))
