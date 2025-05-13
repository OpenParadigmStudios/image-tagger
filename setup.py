#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Package setup script

from setuptools import setup, find_packages
import os

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="civitai-tagger",
    version="1.0.0",
    author="CivitAI Tagger Contributors",
    author_email="author@example.com",  # Replace with actual email
    description="CivitAI Flux Dev LoRA Tagging Assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/civitai-tagger",  # Replace with actual URL
    packages=find_packages(exclude=["test", "test.*"]),
    include_package_data=True,
    package_data={
        "": ["static/**/*"],
    },
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "civitai-tagger=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
)
