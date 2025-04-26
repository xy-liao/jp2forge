#!/usr/bin/env python3
"""
Check dependencies for JP2Forge.

This script checks if all required dependencies are installed
and provides guidance on installing missing dependencies.
"""

import os
import importlib.util
import subprocess
import sys
import platform


def check_module(module_name):
    """Check if a Python module is installed."""
    spec = importlib.util.find_spec(module_name)
    return spec is not None


def check_command(command):
    """Check if a command is available in the system."""
    try:
        subprocess.run(
            [command, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        return True
    except FileNotFoundError:
        return False


def get_module_version(module_name):
    """Get the version of an installed module."""
    try:
        module = importlib.import_module(module_name)
        return getattr(module, "__version__", "unknown")
    except ImportError:
        return None


def main():
    """Main function to check dependencies."""
    print("=" * 60)
    print("JP2Forge Dependency Checker")
    print("=" * 60)
    
    # System information
    print("\nSystem Information:")
    print(f"Python version: {platform.python_version()}")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Platform: {platform.platform()}")
    
    # Required Python modules
    print("\nChecking required Python modules:")
    required_modules = {
        "PIL": "pillow",  # PIL is imported as PIL but installed as pillow
        "numpy": "numpy",
        "psutil": "psutil"
    }
    
    all_modules_installed = True
    missing_modules = []
    
    for module_name, package_name in required_modules.items():
        if check_module(module_name):
            version = get_module_version(module_name)
            print(f"✅ {module_name} is installed (version: {version})")
        else:
            print(f"❌ {module_name} is NOT installed")
            missing_modules.append(package_name)
            all_modules_installed = False
    
    # External dependencies
    print("\nChecking external dependencies:")
    
    # Check exiftool (optional)
    exiftool_found = check_command("exiftool")
    if exiftool_found:
        try:
            version_output = subprocess.run(
                ["exiftool", "-ver"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )
            version = version_output.stdout.strip()
            print(f"✅ ExifTool is installed (version: {version})")
        except subprocess.CalledProcessError:
            print("✅ ExifTool is installed (version: unknown)")
    else:
        print("⚠️ ExifTool is NOT installed (optional for advanced metadata handling)")
    
    # Check jpylyzer (optional but recommended for JP2 validation)
    jpylyzer_found = check_command("jpylyzer")
    if jpylyzer_found:
        try:
            version_output = subprocess.run(
                ["jpylyzer", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )
            version = version_output.stdout.strip() if version_output.stdout.strip() else "unknown"
            print(f"✅ JPylyzer is installed (version: {version})")
        except subprocess.CalledProcessError:
            print("✅ JPylyzer is installed (version: unknown)")
    else:
        print("\033[93m⚠️ JPylyzer is NOT installed\033[0m")
        print("\033[93m  JP2 validation will be limited without JPylyzer.\033[0m")
        print("\033[93m  The validation reports will not contain detailed properties information.\033[0m")
        
    # Installation instructions
    if not all_modules_installed:
        print("\nMissing required dependencies:")
        print("Install them using pip:")
        print(f"pip install {' '.join(missing_modules)}")
    
    if not exiftool_found:
        print("\nTo install ExifTool (optional):")
        if platform.system() == "Darwin":  # macOS
            print("brew install exiftool")
        elif platform.system() == "Linux":
            print("For Debian/Ubuntu: sudo apt-get install libimage-exiftool-perl")
            print("For Fedora/RHEL: sudo dnf install perl-Image-ExifTool")
        elif platform.system() == "Windows":
            print("Download from https://exiftool.org/ and add to PATH")
    
    if not jpylyzer_found:
        print("\nTo install JPylyzer (recommended for JP2 validation):")
        print("pip install jpylyzer")
    
    print("\nDependency check completed.")
    if all_modules_installed:
        if not jpylyzer_found:
            print("All required dependencies are installed! 🎉")
            print("However, JPylyzer is recommended for complete JP2 validation.")
        else:
            print("All dependencies are installed! 🎉")
        return 0
    else:
        print("Some required dependencies are missing. Please install them before running JP2Forge.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
