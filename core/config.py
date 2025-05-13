#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Core configuration and argument parsing

"""
Core configuration and argument parsing module for CivitAI Flux Dev LoRA Tagging Assistant.
Provides command line parsing and configuration management functionality.
"""

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    """Store application configuration settings."""
    input_directory: Path
    output_dir: str = "output"
    resume: bool = False
    prefix: str = "img"
    verbose: bool = False
    auto_save: int = 60  # seconds
    host: str = "127.0.0.1"  # Server host
    port: int = 8000  # Server port


def setup_logging(verbose: bool) -> None:
    """Configure the logging system based on verbosity level."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logging.info("Logging initialized")


def parse_arguments() -> AppConfig:
    """
    Parse command line arguments.

    Returns:
        AppConfig: Application configuration object
    """
    parser = argparse.ArgumentParser(
        description="CivitAI Flux Dev LoRA Tagging Assistant",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Required argument
    parser.add_argument(
        "input_directory",
        help="Path to the directory containing images to process"
    )

    # Optional arguments
    parser.add_argument(
        "-o", "--output-dir",
        default="output",
        help="Specify a custom output directory name"
    )

    parser.add_argument(
        "-r", "--resume",
        action="store_true",
        help="Resume from a previous session"
    )

    parser.add_argument(
        "-p", "--prefix",
        default="img",
        help="Prefix for renamed image files"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "-a", "--auto-save",
        type=int,
        default=60,
        help="Time interval in seconds for auto-saving session state"
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host IP address for the web server"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number for the web server"
    )

    args = parser.parse_args()

    # Convert input_directory string to Path object
    input_dir = Path(args.input_directory)

    # Create configuration object
    config = AppConfig(
        input_directory=input_dir,
        output_dir=args.output_dir,
        resume=args.resume,
        prefix=args.prefix,
        verbose=args.verbose,
        auto_save=args.auto_save,
        host=args.host,
        port=args.port
    )

    return config
