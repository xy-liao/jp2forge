#!/usr/bin/env python3
"""
JP2Forge Package Build Script

This script automates the process of building and publishing the JP2Forge package:
1. Cleans the dist directory to avoid uploading old versions
2. Builds both wheel and source distribution packages
3. Provides instructions for uploading to PyPI

Usage:
    python build_package.py

Requirements:
    pip install build twine
"""

import os
import shutil
import subprocess
import sys


def clean_dist_directory():
    """Remove old distribution files to prevent accidental uploads."""
    print("Cleaning dist directory...")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
        print("✓ Old distribution files removed")
    else:
        print("✓ No existing distribution files found")


def build_package():
    """Build both wheel and source distribution."""
    print("\nBuilding distribution packages...")
    try:
        subprocess.run([sys.executable, "-m", "build"], check=True)
        print("✓ Package built successfully")
    except subprocess.CalledProcessError:
        print("❌ Package build failed")
        sys.exit(1)


def check_version():
    """Ensure version numbers are consistent."""
    # Import version from package
    sys.path.insert(0, os.path.abspath('.'))
    try:
        from jp2forge import __version__ as init_version
    except ImportError:
        print("❌ Could not import version from __init__.py")
        return False
    
    # Extract version from setup.py
    setup_version = None
    try:
        with open("setup.py", "r") as f:
            for line in f:
                if "version=" in line:
                    # Extract version string from something like version="0.9.2",
                    version_str = line.split("version=")[1].strip()
                    if '"' in version_str:
                        setup_version = version_str.split('"')[1]
                    elif "'" in version_str:
                        setup_version = version_str.split("'")[1]
                    break
    except Exception as e:
        print(f"❌ Error reading setup.py: {e}")
        return False
    
    if setup_version is None:
        print("❌ Could not find version in setup.py")
        return False
    
    # Compare versions
    if init_version != setup_version:
        print(f"❌ Version mismatch: __init__.py ({init_version}) != setup.py ({setup_version})")
        return False
    else:
        print(f"✓ Version consistency check passed: {init_version}")
        return True


def main():
    """Main function to build the package."""
    print("=" * 60)
    print("JP2Forge Package Builder")
    print("=" * 60)
    
    # Step 1: Check version consistency
    if not check_version():
        print("Please ensure versions in __init__.py and setup.py match before building.")
        sys.exit(1)
    
    # Step 2: Clean dist directory
    clean_dist_directory()
    
    # Step 3: Build package
    build_package()
    
    # Step 4: Provide upload instructions
    print("\nPackage ready for upload!")
    print("\nTo upload ONLY the latest version to PyPI:")
    print("  python -m twine upload dist/* --skip-existing")
    print("\nOr, to upload a specific version:")
    from jp2forge import __version__ as version
    print(f"  python -m twine upload dist/jp2forge-{version}*")
    
    print("\nTo install the local build:")
    print(f"  pip install dist/jp2forge-{version}-py3-none-any.whl")
    
    print("\nBuild process completed successfully! 🎉")


if __name__ == "__main__":
    main()