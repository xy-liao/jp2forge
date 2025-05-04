#!/bin/bash
# Test script for JP2Forge
# This script tests JP2Forge in three scenarios:
# 1. Processing a single image directly
# 2. Processing a single image from input_dir
# 3. Processing multiple images from input_dir
# After each test, it validates the outputs and reports, then cleans up

# Set variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="${SCRIPT_DIR}/input_dir"
OUTPUT_DIR="${SCRIPT_DIR}/output_dir"
REPORTS_DIR="${SCRIPT_DIR}/reports"

# Function to clean up output directories
clean_output_dirs() {
  echo "Cleaning up output directories..."
  find "$OUTPUT_DIR" -type f -name "*.jp2" -delete
  find "$REPORTS_DIR" -type f \( -name "*.json" -o -name "*.md" \) ! -name "README.md" -delete
  echo "Cleanup complete."
}

# Function to check outputs
check_outputs() {
  local test_name=$1
  
  echo "Checking outputs for $test_name..."
  
  # Check if JP2 files exist in output_dir
  jp2_count=$(find "$OUTPUT_DIR" -type f -name "*.jp2" | wc -l)
  echo "Found $jp2_count JP2 file(s) in output directory."
  
  # Check if JPylyzer reports exist
  if [ -f "$REPORTS_DIR/info_jpylyzer.json" ]; then
    echo "✓ JPylyzer report exists."
  else
    echo "✗ JPylyzer report missing."
  fi
  
  # Check if summary report exists
  if [ -f "$REPORTS_DIR/summary_report.md" ]; then
    echo "✓ Summary report exists."
    echo "--- Summary Report Preview ---"
    head -n 15 "$REPORTS_DIR/summary_report.md"
    echo "----------------------------"
  else
    echo "✗ Summary report missing."
  fi
  
  echo "$test_name test complete."
  echo "----------------------------------------"
}

# Ensure the script is running from the right directory
cd "$SCRIPT_DIR"

echo "JP2Forge Test Script"
echo "=================================="
echo "Testing in three scenarios:"
echo "1. Process a single image directly"
echo "2. Process a single image from input_dir"
echo "3. Process multiple images from input_dir"
echo "=================================="

# Test 1: Process a single image directly
echo "Test 1: Processing a single image directly"
echo "------------------------------------------"
clean_output_dirs

# Run JP2Forge on a single image
python -m cli.workflow "$INPUT_DIR/Arkansas_Constitution_of_1836,_page_1.tif" "$OUTPUT_DIR" --report-dir="$REPORTS_DIR" --verbose

# Check outputs
check_outputs "Single image direct"

# Test 2: Process a single image from input_dir
echo "Test 2: Processing a single image from input_dir"
echo "------------------------------------------------"
clean_output_dirs

# Run JP2Forge on a single image using its path in input_dir
python -m cli.workflow "$INPUT_DIR/Arkansas_Constitution_of_1836,_page_2.tif" "$OUTPUT_DIR" --report-dir="$REPORTS_DIR" --verbose

# Check outputs
check_outputs "Single image from input_dir"

# Test 3: Process multiple images from input_dir
echo "Test 3: Processing multiple images from input_dir"
echo "-------------------------------------------------"
clean_output_dirs

# Run JP2Forge on the entire input_dir
python -m cli.workflow "$INPUT_DIR" "$OUTPUT_DIR" --report-dir="$REPORTS_DIR" --verbose

# Check outputs
check_outputs "Multiple images from input_dir"

echo "All tests completed."