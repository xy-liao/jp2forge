"""
Image analysis module for JP2Forge.

This module provides functionality for analyzing pixel loss
between original and compressed images.
"""

import os
import logging
import numpy as np
import json
from PIL import Image
from typing import Dict, Any, Optional, Tuple

from core.types import AnalysisResult, WorkflowStatus
from utils.image import calculate_mse, calculate_psnr, calculate_ssim

logger = logging.getLogger(__name__)


class ImageAnalyzer:
    """Handles image analysis and quality assessment."""

    def __init__(
        self,
        psnr_threshold: float = 40.0,
        ssim_threshold: float = 0.95,
        mse_threshold: float = 50.0,
        report_dir: Optional[str] = None
    ):
        """Initialize the analyzer.

        Args:
            psnr_threshold: PSNR threshold for quality control
            ssim_threshold: SSIM threshold for quality control
            mse_threshold: MSE threshold for quality control
            report_dir: Directory for reports
        """
        self.psnr_threshold = psnr_threshold
        self.ssim_threshold = ssim_threshold
        self.mse_threshold = mse_threshold
        self.report_dir = report_dir

        if report_dir:
            os.makedirs(report_dir, exist_ok=True)

    def analyze_pixel_loss(
        self,
        original_path: str,
        converted_path: str,
        save_report: bool = False  # Changed default from True to False
    ) -> AnalysisResult:
        """Analyze pixel loss between original and converted images.

        Args:
            original_path: Path to original image
            converted_path: Path to converted image
            save_report: Whether to save a detailed report (default: False)

        Returns:
            AnalysisResult: Analysis results
        """
        try:
            # Load images
            with Image.open(original_path) as orig_img:
                orig_array = np.array(orig_img)
            with Image.open(converted_path) as conv_img:
                conv_array = np.array(conv_img)

            # Calculate metrics
            mse = calculate_mse(orig_array, conv_array)
            psnr = calculate_psnr(mse)
            ssim = calculate_ssim(orig_array, conv_array)

            # Check if quality thresholds are met
            quality_passed = (
                psnr >= self.psnr_threshold and
                ssim >= self.ssim_threshold and
                mse <= self.mse_threshold
            )

            # Create result
            result = AnalysisResult(
                psnr=float(psnr),
                ssim=float(ssim),
                mse=float(mse),
                quality_passed=quality_passed
            )

            # Save report if requested and directory is set
            if save_report and self.report_dir:
                self._save_analysis_report(
                    result,
                    original_path,
                    converted_path
                )

            return result

        except Exception as e:
            logger.error(f"Error analyzing pixel loss: {str(e)}")
            return AnalysisResult(
                psnr=0.0,
                ssim=0.0,
                mse=float('inf'),
                quality_passed=False,
                error=str(e)
            )

    def _save_analysis_report(
        self,
        result: AnalysisResult,
        original_path: str,
        converted_path: str
    ) -> str:
        """Save analysis results to a report file.

        Args:
            result: Analysis results
            original_path: Path to original image
            converted_path: Path to converted image

        Returns:
            str: Path to report file
        """
        try:
            # Create report filename
            report_name = f"analysis_{os.path.basename(original_path)}.json"
            report_path = os.path.join(self.report_dir, report_name)

            # Get file sizes
            original_size = os.path.getsize(original_path)
            converted_size = os.path.getsize(converted_path)
            compression_ratio = original_size / converted_size if converted_size > 0 else 0

            # Create report data - Convert boolean to string for JSON serialization
            report_data = {
                "original_file": os.path.basename(original_path),
                "converted_file": os.path.basename(converted_path),
                "file_sizes": {
                    "original_size": original_size,
                    "original_size_human": self._format_file_size(original_size),
                    "converted_size": converted_size,
                    "converted_size_human": self._format_file_size(converted_size),
                    "compression_ratio": f"{compression_ratio:.2f}:1"
                },
                "metrics": {
                    "psnr": f"{result.psnr:.2f} dB",
                    "ssim": f"{result.ssim:.4f}",
                    "mse": f"{result.mse:.2f}"
                },
                "quality_passed": "yes" if result.quality_passed else "no",  # Use strings instead of booleans
                "thresholds": {
                    "psnr": self.psnr_threshold,
                    "ssim": self.ssim_threshold,
                    "mse": self.mse_threshold
                },
                "recommendations": self._get_recommendations(result)
            }

            # Write report to file
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=4)

            logger.info(f"Saved analysis report to {report_path}")
            return report_path

        except Exception as e:
            logger.error(f"Error saving analysis report: {str(e)}")
            return ""

    def _get_recommendations(self, result: AnalysisResult) -> list:
        """Generate recommendations based on analysis results.

        Args:
            result: Analysis results

        Returns:
            List of recommendations
        """
        recommendations = []

        if not result.quality_passed:
            if result.psnr < self.psnr_threshold:
                recommendations.append(
                    f"PSNR ({result.psnr:.2f} dB) is below threshold ({self.psnr_threshold} dB). "
                    "Consider using lossless compression."
                )
            if result.ssim < self.ssim_threshold:
                recommendations.append(
                    f"SSIM ({result.ssim:.4f}) is below threshold ({self.ssim_threshold}). "
                    "Image structure significantly altered."
                )
            if result.mse > self.mse_threshold:
                recommendations.append(
                    f"MSE ({result.mse:.2f}) exceeds threshold ({self.mse_threshold}). "
                    "High pixel value differences detected."
                )

        if not recommendations:
            recommendations.append(
                "No quality issues detected. All metrics within acceptable thresholds."
            )

        return recommendations

    def _format_file_size(self, size_in_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_in_bytes: File size in bytes

        Returns:
            str: Human-readable file size
        """
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_in_bytes)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.2f} {units[unit_index]}"
