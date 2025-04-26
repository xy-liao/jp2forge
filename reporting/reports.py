"""
Report generation for JPEG2000 processing.

This module provides functionality for generating reports on
JPEG2000 processing results.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class LossAnalysisReport:
    """Generates detailed reports for pixel loss analysis."""
    
    def __init__(self, report_dir: str):
        """Initialize the report generator.
        
        Args:
            report_dir: Directory for storing reports
        """
        self.report_dir = report_dir
        os.makedirs(report_dir, exist_ok=True)
    
    def generate_report(
        self,
        input_file: str,
        output_file: str,
        analysis_results: Dict[str, Any],
        metadata: Dict[str, Any],
        jpylyzer_dir: Optional[str] = None
    ) -> str:
        """Generate a detailed analysis report.
        
        Args:
            input_file: Path to original image
            output_file: Path to converted image
            analysis_results: Results from pixel loss analysis
            metadata: Additional metadata for the report
            jpylyzer_dir: Directory where JPylyzer JSON reports are stored (optional)
            
        Returns:
            str: Path to generated report
        """
        try:
            # Ensure analysis_results is a dictionary
            if not isinstance(analysis_results, dict):
                analysis_results = {
                    "psnr": 0.0,
                    "ssim": 0.0,
                    "mse": float('inf'),
                    "quality_passed": "no",
                    "error": "Invalid analysis results format"
                }
            
            # Ensure quality_passed is present and a string
            if "quality_passed" not in analysis_results:
                analysis_results["quality_passed"] = "no"
            elif not isinstance(analysis_results["quality_passed"], str):
                analysis_results["quality_passed"] = "yes" if analysis_results["quality_passed"] else "no"
            
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "input_file": os.path.basename(input_file),
                "output_file": os.path.basename(output_file),
                "analysis_results": analysis_results,
                "metadata": metadata
            }
            
            # Add summary section
            report_data["summary"] = self._generate_summary(
                analysis_results,
                metadata
            )
            
            # Try to include JPylyzer results if available
            if jpylyzer_dir:
                jp2_name = Path(output_file).stem
                jpylyzer_json = Path(jpylyzer_dir) / f"{jp2_name}_jpylyzer.json"
                if jpylyzer_json.exists():
                    try:
                        with open(jpylyzer_json, 'r') as f:
                            report_data['jpylyzer'] = json.load(f)
                    except Exception as e:
                        report_data['jpylyzer'] = {"error": f"Failed to load JPylyzer report: {e}"}
            
            # Save report
            report_name = (
                f"loss_analysis_{os.path.basename(input_file)}.json"
            )
            report_path = os.path.join(self.report_dir, report_name)
            
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=4)
            
            logger.info(f"Generated analysis report: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return ""
    
    def _generate_summary(
        self,
        analysis_results: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary section for the report.
        
        Args:
            analysis_results: Results from pixel loss analysis
            metadata: Additional metadata for the report
            
        Returns:
            Dict containing summary information
        """
        # Ensure quality_passed is converted consistently
        quality_passed = str(analysis_results.get("quality_passed", "no")).lower() == "yes"
        
        # Get metrics with defaults
        try:
            psnr = float(analysis_results.get("psnr", 0.0))
        except (ValueError, TypeError):
            psnr = 0.0
            
        try:
            ssim = float(analysis_results.get("ssim", 0.0))
        except (ValueError, TypeError):
            ssim = 0.0
            
        try:
            mse = float(analysis_results.get("mse", float('inf')))
        except (ValueError, TypeError):
            mse = float('inf')
        
        return {
            "quality_assessment": (
                "PASSED" if quality_passed else "FAILED"
            ),
            "compression_mode": metadata.get(
                "compression_mode",
                "unknown"
            ),
            "quality_metrics": {
                "psnr": f"{psnr:.2f} dB",
                "ssim": f"{ssim:.4f}",
                "mse": f"{mse:.2f}"
            },
            "recommendations": self._get_recommendations(
                quality_passed,
                psnr,
                ssim,
                mse
            )
        }
    
    def _get_recommendations(
        self,
        quality_passed: bool,
        psnr: float,
        ssim: float,
        mse: float
    ) -> list:
        """Generate recommendations based on analysis results.
        
        Args:
            quality_passed: Whether quality checks passed
            psnr: Peak Signal-to-Noise Ratio
            ssim: Structural Similarity Index
            mse: Mean Square Error
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if not quality_passed:
            if psnr < 40.0:
                recommendations.append(
                    "Consider using lossless compression"
                )
            if ssim < 0.95:
                recommendations.append(
                    "Image structure significantly altered"
                )
            if mse > 50.0:
                recommendations.append(
                    "High pixel value differences detected"
                )
        
        if not recommendations:
            recommendations.append(
                "No quality issues detected"
            )
        
        return recommendations


class WorkflowReport:
    """Generates reports for the entire workflow."""
    
    def __init__(self, report_dir: str):
        """Initialize the report generator.
        
        Args:
            report_dir: Directory for storing reports
        """
        self.report_dir = report_dir
        os.makedirs(report_dir, exist_ok=True)
    
    def generate_summary_report(
        self,
        results: Dict[str, Any],
        config: Dict[str, Any],
        jpylyzer_dir: Optional[str] = None
    ) -> str:
        """Generate a summary report for the workflow, including JPylyzer validation info."""
        try:
            # Create summary data
            summary_data = {
                "timestamp": datetime.now().isoformat(),
                "config": config,
                "results": {
                    "total_files": len(results.get("processed_files", [])),
                    "success_count": results.get("success_count", 0),
                    "warning_count": results.get("warning_count", 0),
                    "error_count": results.get("error_count", 0),
                    "corrupted_count": results.get("corrupted_count", 0),
                    "overall_status": results.get("status", "UNKNOWN"),
                    "processing_time": results.get("processing_time", 0.0)
                },
                "processed_files": results.get("processed_files", [])
            }
            
            # Save JSON report
            json_report_path = os.path.join(
                self.report_dir,
                f"workflow_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(json_report_path, 'w') as f:
                json.dump(summary_data, f, indent=4)
            
            # Generate Markdown report
            markdown_report = self._generate_markdown_report(summary_data, jpylyzer_dir)
            md_report_path = os.path.join(
                self.report_dir,
                f"workflow_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            )
            
            with open(md_report_path, 'w') as f:
                f.write(markdown_report)
            
            logger.info(f"Generated summary reports: {json_report_path}, {md_report_path}")
            return md_report_path
            
        except Exception as e:
            logger.error(f"Error generating summary report: {str(e)}")
            return ""
    
    def _generate_markdown_report(self, summary_data: Dict[str, Any], jpylyzer_dir: Optional[str] = None) -> str:
        """Generate a Markdown report from summary data, including JPylyzer validation info in block format."""
        report = []
        timestamp = datetime.fromisoformat(summary_data["timestamp"])
        
        report.append("# JPEG2000 Conversion Summary Report")
        report.append(f"Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Overall statistics
        report.append("## Overall Statistics")
        report.append("-----------------")
        results = summary_data["results"]
        report.append(f"Total Files: {results['total_files']}")
        report.append(f"Successful: {results['success_count']}")
        report.append(f"Warnings: {results['warning_count']}")
        report.append(f"Errors: {results['error_count']}")
        report.append(f"Corrupted: {results['corrupted_count']}")
        report.append(f"Overall Status: {results['overall_status']}")
        
        # Processing time
        if results["processing_time"] > 0:
            report.append(f"Total Processing Time: {results['processing_time']:.2f} seconds")
            report.append(f"Average Processing Rate: {results['total_files'] / results['processing_time']:.2f} files/second\n")
        
        # Configuration
        report.append("## Configuration")
        report.append("-----------------")
        config = summary_data["config"]
        
        for key, value in config.items():
            report.append(f"{key}: {value}")
        report.append("")
        
        # File details
        report.append("## Detailed Results")
        report.append("----------------")
        
        # Load info_jpylyzer.json if available
        all_jpylyzer = {}
        if jpylyzer_dir:
            info_jpylyzer_path = Path(jpylyzer_dir) / "info_jpylyzer.json"
            if info_jpylyzer_path.exists():
                try:
                    with open(info_jpylyzer_path, 'r') as f:
                        all_jpylyzer = json.load(f)
                except Exception:
                    all_jpylyzer = {}
        
        for file_result in summary_data["processed_files"]:
            input_file = file_result['input_file']
            status = file_result['status']
            output_file = file_result.get('output_file', '')
            orig_size = file_result.get('file_sizes', {}).get('original_size_human', 'N/A')
            conv_size = file_result.get('file_sizes', {}).get('converted_size_human', 'N/A')
            ratio = file_result.get('file_sizes', {}).get('compression_ratio', 'N/A')

            # JPylyzer validation status and details from info_jpylyzer.json
            jpylyzer_status = "N/A"
            jpylyzer_details = ""
            if output_file:
                jp2_name = Path(output_file).name
                if jp2_name in all_jpylyzer:
                    jpylyzer_entry = all_jpylyzer[jp2_name]
                    jpylyzer_status = "Valid" if jpylyzer_entry.get("isValid") else "Invalid"
                    # Show errors/warnings if present
                    errors = jpylyzer_entry.get("errors")
                    warnings = jpylyzer_entry.get("warnings")
                    if errors:
                        jpylyzer_details += f"    Errors: {errors}\n"
                    if warnings:
                        jpylyzer_details += f"    Warnings: {warnings}\n"

            report.append(f"File: {input_file}")
            report.append(f"Status: {status}")
            report.append(f"Output: {output_file}")
            report.append(f"Original Size: {orig_size}")
            report.append(f"Converted Size: {conv_size}")
            report.append(f"Compression Ratio: {ratio}")
            report.append(f"JPylyzer Validation: {jpylyzer_status}")
            if jpylyzer_details:
                report.append(jpylyzer_details)
            report.append("")

        return "\n".join(report)
