#!/usr/bin/env python
import os
import subprocess
import sys


def fix_style_in_directory(directory):
    """Fix style issues in all Python files in a directory recursively."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                print(f"Fixing style in {filepath}...")
                # Fix trailing whitespace, blank lines with whitespace, and missing final newlines
                subprocess.run(['autopep8', '--in-place', '--aggressive',
                               '--select=W291,W293,W292,E303,E302,E305,E226,E261', filepath])

                # Fix long lines without breaking code
                subprocess.run(['autopep8', '--in-place', '--max-line-length=100', filepath])

                print(f"Fixed {filepath}")


if __name__ == '__main__':
    directories = ['core', 'utils', 'workflow', 'cli', 'reporting']
    for directory in directories:
        if os.path.isdir(directory):
            print(f"Processing directory: {directory}")
            fix_style_in_directory(directory)
        else:
            print(f"Directory not found: {directory}")

    # Also fix individual Python files in the root directory
    for file in os.listdir('.'):
        if file.endswith('.py') and os.path.isfile(file):
            filepath = os.path.join('.', file)
            print(f"Fixing style in {filepath}...")
            subprocess.run(['autopep8', '--in-place', '--aggressive',
                           '--select=W291,W293,W292,E303,E302,E305,E226,E261', filepath])
            subprocess.run(['autopep8', '--in-place', '--max-line-length=100', filepath])
            print(f"Fixed {filepath}")
