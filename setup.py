"""
JP2Forge - JPEG2000 Processing Tool

A comprehensive Python library for converting images to JPEG2000 format,
supporting both standard operations and BnF-compliant workflows.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="jp2forge",
    version="0.9.6",
    author="xy-liao",
    description="A comprehensive JPEG2000 processing tool with BnF compatibility",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xy-liao/jp2forge",
    project_urls={
        "Bug Tracker": "https://github.com/xy-liao/jp2forge/issues",
        "Documentation": "https://github.com/xy-liao/jp2forge/tree/main/docs",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
    ],
    packages=find_packages(exclude=["benchmark", "input_dir", "output", "output_dir", "reports"]),
    install_requires=[
        "numpy>=1.20.0",
        "pillow>=9.0.0",
        "psutil>=5.8.0",
        "structlog>=21.1.0",
        "lxml>=4.9.0",
        "pyyaml>=6.0",
        "jpylyzer>=2.2.0",
        "matplotlib>=3.9.0",
        "pandas>=2.2.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "jp2forge=cli.workflow:main",
        ],
    },
)
