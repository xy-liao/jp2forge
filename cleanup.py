#!/usr/bin/env python3
"""
JP2Forge Cleanup Utility

This script provides two main functions:
1. Clean temporary files and resources created during JP2Forge operation
2. Prepare the repository for publication (removing development artifacts)

Usage:
    python cleanup.py [--temp] [--reports] [--output] [--benchmarks] [--all]
    python cleanup.py [--repo] [--keep-benchmarks] [--dry-run]

Options:
    --temp          Clean temporary processing files
    --reports       Clean generated reports
    --output        Clean output directory
    --benchmarks    Clean benchmark results
    --all           Clean everything (temp, reports, output, benchmarks)

    --repo          Prepare repository for publication
    --keep-benchmarks  When used with --repo, preserves benchmark data
    --dry-run       Show what would be deleted without actually deleting
    --older-than N  Only clean files older than N days (0=all)
"""

import os
import sys
import shutil
import argparse
import glob
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("jp2forge.cleanup")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='JP2Forge Cleanup Utility')

    # Operational cleanup options
    cleanup_group = parser.add_argument_group('Operational Cleanup')
    cleanup_group.add_argument('--temp', action='store_true',
                               help='Clean temporary processing files')
    cleanup_group.add_argument('--reports', action='store_true',
                               help='Clean generated reports')
    cleanup_group.add_argument('--output', action='store_true',
                               help='Clean output directory')
    cleanup_group.add_argument('--benchmarks', action='store_true',
                               help='Clean benchmark results')
    cleanup_group.add_argument('--all', action='store_true',
                               help='Clean everything (temp, reports, output, benchmarks)')
    cleanup_group.add_argument('--older-than', type=int, default=0,
                               help='Only clean files older than specified days (0=all)')

    # Repository preparation options
    repo_group = parser.add_argument_group('Repository Preparation')
    repo_group.add_argument('--repo', action='store_true',
                            help='Prepare repository for publication')
    repo_group.add_argument('--keep-benchmarks', action='store_true',
                            help='When used with --repo, preserves benchmark data')

    # General options
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be deleted without actually deleting')

    return parser.parse_args()


def get_project_root():
    """Get the absolute path to the project root directory."""
    # Use the location of this script to determine the project root
    return str(Path(__file__).resolve().parent)


def is_old_enough(file_path, days):
    """Check if file is older than specified days."""
    if days <= 0:
        return True

    file_time = os.path.getmtime(file_path)
    cutoff_time = time.time() - (days * 24 * 3600)
    return file_time < cutoff_time


def clean_temp_files(project_root, dry_run=False, days_old=0):
    """Clean temporary files created during processing."""
    logger.info("Cleaning temporary files...")

    # Look for temp directories and common temp file patterns
    temp_patterns = [
        os.path.join(project_root, "**", "*.tmp"),
        os.path.join(project_root, "temp", "**", "*"),
        os.path.join(project_root, "**", "*.tmp.jp2"),
        os.path.join(project_root, "**", "*.part"),
        "/tmp/jp2forge_*"
    ]

    cleaned = 0
    for pattern in temp_patterns:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.exists(file_path) and is_old_enough(file_path, days_old):
                if dry_run:
                    logger.info(f"Would delete temp file: {file_path}")
                else:
                    try:
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                        else:
                            os.remove(file_path)
                        logger.debug(f"Deleted temp file: {file_path}")
                        cleaned += 1
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")

    logger.info(f"Temp files cleaned: {cleaned}")
    return cleaned


def clean_reports(project_root, dry_run=False, days_old=0):
    """Clean report files."""
    logger.info("Cleaning reports...")

    reports_dir = os.path.join(project_root, "reports")
    if not os.path.exists(reports_dir):
        logger.info("Reports directory does not exist")
        return 0

    report_patterns = [
        os.path.join(reports_dir, "*.md"),
        os.path.join(reports_dir, "*.json"),
        os.path.join(reports_dir, "*.html"),
        os.path.join(reports_dir, "*.csv")
    ]

    cleaned = 0
    for pattern in report_patterns:
        for file_path in glob.glob(pattern, recursive=False):
            if os.path.exists(file_path) and is_old_enough(file_path, days_old):
                # Skip README files
                if os.path.basename(file_path) == 'README.md':
                    continue

                if dry_run:
                    logger.info(f"Would delete report: {file_path}")
                else:
                    try:
                        os.remove(file_path)
                        logger.debug(f"Deleted report: {file_path}")
                        cleaned += 1
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")

    # Create README.md if it doesn't exist after cleaning
    readme_path = os.path.join(reports_dir, "README.md")
    if not os.path.exists(readme_path) and not dry_run:
        with open(readme_path, 'w') as f:
            f.write("# Reports Directory\n\nThis directory contains reports generated by JP2Forge.\n")
        logger.debug(f"Created: {readme_path}")

    logger.info(f"Reports cleaned: {cleaned}")
    return cleaned


def clean_output(project_root, dry_run=False, days_old=0):
    """Clean output directory."""
    logger.info("Cleaning output directory...")

    # Check both the old and new output directory paths
    output_dir = os.path.join(project_root, "output_dir")
    legacy_output_dir = os.path.join(project_root, "output")

    # Track if either output directory exists
    output_exists = False

    # Process the new "output_dir" directory if it exists
    if os.path.exists(output_dir):
        output_exists = True
        logger.info(f"Cleaning files in output_dir directory: {output_dir}")

        output_patterns = [
            os.path.join(output_dir, "*.jp2"),
            os.path.join(output_dir, "*.xmp"),
            os.path.join(output_dir, "**", "*.jp2"),
            os.path.join(output_dir, "**", "*.xmp")
        ]

        cleaned = 0
        for pattern in output_patterns:
            for file_path in glob.glob(pattern, recursive=True):
                if os.path.exists(file_path) and is_old_enough(file_path, days_old):
                    if dry_run:
                        logger.info(f"Would delete output file: {file_path}")
                    else:
                        try:
                            os.remove(file_path)
                            logger.debug(f"Deleted output file: {file_path}")
                            cleaned += 1
                        except Exception as e:
                            logger.error(f"Failed to delete {file_path}: {e}")

        # Create README.md if it doesn't exist after cleaning
        readme_path = os.path.join(output_dir, "README.md")
        if not os.path.exists(readme_path) and not dry_run:
            with open(readme_path, 'w') as f:
                f.write("# Output Directory\n\nThis directory is the default output location for JPEG2000 files generated by jp2forge.\n\nWhen processing images, the tool will save the converted JP2 files here.\n\n## Example usage:\n\n```bash\npython -m cli.workflow input_dir/ output_dir/ --bnf-compliant\n```")
            logger.debug(f"Created: {readme_path}")

        # Create .gitkeep to keep the directory even when empty
        gitkeep_path = os.path.join(output_dir, ".gitkeep")
        if not os.path.exists(gitkeep_path) and not dry_run:
            with open(gitkeep_path, 'w') as f:
                pass  # Create an empty file
            logger.debug(f"Created: {gitkeep_path}")

        logger.info(f"Output files cleaned: {cleaned}")

    # Also check the legacy "output" directory for backward compatibility
    if os.path.exists(legacy_output_dir):
        output_exists = True
        logger.info(f"Cleaning files in legacy output directory: {legacy_output_dir}")

        legacy_patterns = [
            os.path.join(legacy_output_dir, "*.jp2"),
            os.path.join(legacy_output_dir, "*.xmp"),
            os.path.join(legacy_output_dir, "**", "*.jp2"),
            os.path.join(legacy_output_dir, "**", "*.xmp")
        ]

        legacy_cleaned = 0
        for pattern in legacy_patterns:
            for file_path in glob.glob(pattern, recursive=True):
                if os.path.exists(file_path) and is_old_enough(file_path, days_old):
                    if dry_run:
                        logger.info(f"Would delete legacy output file: {file_path}")
                    else:
                        try:
                            os.remove(file_path)
                            logger.debug(f"Deleted legacy output file: {file_path}")
                            legacy_cleaned += 1
                        except Exception as e:
                            logger.error(f"Failed to delete {file_path}: {e}")

        logger.info(f"Legacy output files cleaned: {legacy_cleaned}")
        cleaned += legacy_cleaned

    if not output_exists:
        logger.info("Neither output_dir nor output directory exists")
        return 0

    return cleaned


def clean_benchmarks(project_root, dry_run=False, days_old=0):
    """Clean benchmark results."""
    logger.info("Cleaning benchmark results...")

    benchmark_dir = os.path.join(project_root, "benchmark")
    if not os.path.exists(benchmark_dir):
        logger.info("Benchmark directory does not exist")
        return 0

    # Define the benchmark directory structure
    benchmark_subdirs = {
        "output": os.path.join(benchmark_dir, "output"),
        "reports": os.path.join(benchmark_dir, "reports"),
        "results": os.path.join(benchmark_dir, "results")
    }

    # Old paths for backward compatibility
    legacy_benchmark_patterns = [
        os.path.join(project_root, "benchmark_results", "**", "*"),
        os.path.join(project_root, "benchmark_output", "**", "*"),
        os.path.join(project_root, "benchmark_reports", "**", "*"),
    ]

    cleaned = 0

    # Clean specific benchmark subdirectories
    for subdir_name, subdir_path in benchmark_subdirs.items():
        if not os.path.exists(subdir_path):
            continue

        # Define patterns for each subdirectory
        patterns = []
        if subdir_name == "output":
            patterns = [
                os.path.join(subdir_path, "config_*", "**", "*"),
                os.path.join(subdir_path, "*.jp2"),
            ]
        elif subdir_name == "reports":
            patterns = [
                os.path.join(subdir_path, "summary_report.md"),
                os.path.join(subdir_path, "*.csv"),
            ]
        elif subdir_name == "results":
            patterns = [
                os.path.join(subdir_path, "*.json"),
                os.path.join(subdir_path, "*.png"),
            ]

        # Process files in each subdirectory
        for pattern in patterns:
            for file_path in glob.glob(pattern, recursive=True):
                if os.path.exists(file_path) and is_old_enough(file_path, days_old):
                    # Skip README files
                    if os.path.basename(file_path) == 'README.md':
                        continue

                    if dry_run:
                        logger.info(f"Would delete benchmark file: {file_path}")
                    else:
                        try:
                            if os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                            else:
                                os.remove(file_path)
                            logger.debug(f"Deleted benchmark file: {file_path}")
                            cleaned += 1
                        except Exception as e:
                            logger.error(f"Failed to delete {file_path}: {e}")

    # Process legacy benchmark directories for backward compatibility
    for pattern in legacy_benchmark_patterns:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.exists(file_path) and is_old_enough(file_path, days_old):
                # Skip README files
                if os.path.basename(file_path) == 'README.md':
                    continue

                if dry_run:
                    logger.info(f"Would delete legacy benchmark file: {file_path}")
                else:
                    try:
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                        else:
                            os.remove(file_path)
                        logger.debug(f"Deleted legacy benchmark file: {file_path}")
                        cleaned += 1
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")

    # Ensure README files exist in each benchmark subdirectory
    if not dry_run:
        for subdir_name, subdir_path in benchmark_subdirs.items():
            if not os.path.exists(subdir_path):
                os.makedirs(subdir_path, exist_ok=True)
                logger.debug(f"Created benchmark subdirectory: {subdir_path}")

            # Add README.md if it doesn't exist
            readme_path = os.path.join(subdir_path, "README.md")
            if not os.path.exists(readme_path):
                with open(readme_path, 'w') as f:
                    if subdir_name == "output":
                        f.write("# Benchmark Output Directory\n\nThis directory contains JPEG2000 files generated during benchmark tests.\nOutput files are not included in the repository but will be generated when you run benchmarks.\n")
                    elif subdir_name == "reports":
                        f.write("# Benchmark Reports Directory\n\nThis directory stores benchmark summary reports.\nReport files are not included in the repository but will be generated when you run benchmarks.\n")
                    elif subdir_name == "results":
                        f.write("# Benchmark Results Directory\n\nThis directory stores benchmark result data and visualizations.\nResult files are not included in the repository but will be generated when you run benchmarks.\n")
                logger.debug(f"Created README file: {readme_path}")

    logger.info(f"Benchmark files cleaned: {cleaned}")
    return cleaned


def should_remove_for_repo(path):
    """Determine if a file or directory should be removed for repository preparation."""
    # Essential directories to keep
    essential_dirs = {
        'cli', 'core', 'docs', 'images', 'utils', 'workflow', 'reporting',
        'output', 'reports',  # Keep these directories but clean their contents separately
    }

    # Essential files to keep
    essential_files = {
        '__init__.py', 'AUTHORS', 'CHANGELOG.md', 'LICENSE', 'README.md',
        'requirements.txt', 'setup.py', 'CONTRIBUTING.md', 'check_dependencies.py',
        'cleanup.py', '.gitignore', '.gitattributes', 'INTEGRATION_WITH_JP2FORGE_WEB.md',
        'RELEASE_NOTES_0.9.0.md'
    }

    # Keep essential directories
    if path.name in essential_dirs and path.is_dir():
        return False

    # Keep essential files
    if path.name in essential_files and path.is_file():
        return False

    # Files and directories to always remove
    remove_patterns = [
        # Cache and temporary directories
        '__pycache__', '.mypy_cache', 'jp2forge.egg-info',

        # Log files
        '*.log',

        # Development files
        '.DS_Store',

        # Development scripts
        'bnf_test.py',

        # Private development scripts
        'dev_*', 'test_*',

        # Distribution files
        'dist', 'build',
    ]

    # Check if path matches any removal pattern
    for pattern in remove_patterns:
        if pattern.startswith('*') and pattern.endswith('*'):
            # Handle patterns like *test*
            if pattern.strip('*') in path.name:
                return True
        elif pattern.startswith('*'):
            # Handle patterns like *.log
            if path.name.endswith(pattern[1:]):
                return True
        elif pattern.endswith('*'):
            # Handle patterns like test_*
            if path.name.startswith(pattern[:-1]):
                return True
        elif pattern == path.name:
            # Direct match
            return True

    # By default, keep the file/directory
    return False


def prepare_repo(project_root, dry_run=False, keep_benchmarks=False):
    """Prepare repository for publication."""
    logger.info("Preparing repository for publication...")
    root_path = Path(project_root)

    # First, clean up all operational artifacts
    clean_temp_files(project_root, dry_run)
    clean_reports(project_root, dry_run)
    clean_output(project_root, dry_run)

    # Only clean benchmarks if not keeping them
    if not keep_benchmarks:
        clean_benchmarks(project_root, dry_run)
    else:
        logger.info("Preserving benchmark data as requested")

    # Get a list of items to remove for repo preparation
    items_to_remove = []
    for item in root_path.iterdir():
        # If keeping benchmarks, skip benchmark-related directories
        if keep_benchmarks and item.name in ['benchmark', 'benchmark_results',
                                             'benchmark_output', 'benchmark_reports']:
            logger.info(f"Preserving benchmark directory: {item}")
            continue

        if should_remove_for_repo(item):
            items_to_remove.append(item)

    # Sort by depth (deeper paths first)
    items_to_remove.sort(key=lambda x: len(str(x).split(os.sep)), reverse=True)

    # Process the items
    removed_count = 0
    for item in items_to_remove:
        if dry_run:
            logger.info(f"Would remove: {item}")
        else:
            try:
                if item.is_file():
                    os.remove(item)
                    logger.debug(f"Removed file: {item}")
                    removed_count += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    logger.debug(f"Removed directory: {item}")
                    removed_count += 1
            except Exception as e:
                logger.error(f"Error removing {item}: {e}")

    # Clean up __pycache__ directories recursively
    for pycache_dir in root_path.glob('**/__pycache__'):
        if dry_run:
            logger.info(f"Would remove: {pycache_dir}")
        else:
            try:
                shutil.rmtree(pycache_dir)
                logger.debug(f"Removed directory: {pycache_dir}")
                removed_count += 1
            except Exception as e:
                logger.error(f"Error removing {pycache_dir}: {e}")

    # Clean up .pyc files recursively
    for pyc_file in root_path.glob('**/*.pyc'):
        if dry_run:
            logger.info(f"Would remove: {pyc_file}")
        else:
            try:
                os.remove(pyc_file)
                logger.debug(f"Removed file: {pyc_file}")
                removed_count += 1
            except Exception as e:
                logger.error(f"Error removing {pyc_file}: {e}")

    # Ensure essential directories exist with README files
    for dir_name in ['output', 'reports']:
        dir_path = root_path / dir_name
        if not dir_path.exists() and not dry_run:
            os.makedirs(dir_path, exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")

        # Add README.md if it doesn't exist
        readme_path = dir_path / 'README.md'
        if not readme_path.exists() and not dry_run:
            with open(readme_path, 'w') as f:
                f.write(
                    f"# {dir_name.capitalize()} Directory\n\nThis directory contains {dir_name} generated by JP2Forge.\n")
            logger.debug(f"Created file: {readme_path}")

    logger.info(f"Repository preparation completed: {removed_count} items removed")
    return removed_count


def main():
    """Main function to run the cleanup script."""
    args = parse_args()
    project_root = get_project_root()

    logger.info(f"JP2Forge Cleanup Utility")
    logger.info(f"Project root: {project_root}")

    if args.dry_run:
        logger.info("DRY RUN MODE: No files will be deleted")

    # Check if no specific cleanup options were provided
    no_options = not (args.temp or args.reports or args.output or
                      args.benchmarks or args.all or args.repo)

    if no_options:
        logger.error("No cleanup options specified. Use --help to see available options.")
        return

    # Track total items cleaned
    total_cleaned = 0

    # Operational cleanup
    if args.all or args.temp:
        total_cleaned += clean_temp_files(project_root, args.dry_run, args.older_than)

    if args.all or args.reports:
        total_cleaned += clean_reports(project_root, args.dry_run, args.older_than)

    if args.all or args.output:
        total_cleaned += clean_output(project_root, args.dry_run, args.older_than)

    if args.all or args.benchmarks:
        total_cleaned += clean_benchmarks(project_root, args.dry_run, args.older_than)

    # Repository preparation
    if args.repo:
        total_cleaned += prepare_repo(project_root, args.dry_run, args.keep_benchmarks)

    logger.info("-" * 50)
    if args.dry_run:
        logger.info(f"Dry run completed. Would have removed {total_cleaned} items.")
    else:
        logger.info(f"Cleanup completed successfully! Removed {total_cleaned} items.")


if __name__ == "__main__":
    main()
