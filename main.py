#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Main entry point

import logging
import signal
import sys
from pathlib import Path

from core.config import parse_arguments, setup_logging
from core.filesystem import setup_directories
from server.main import start_server


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        int: Exit code
    """
    try:
        # Parse command line arguments
        config = parse_arguments()

        # Setup logging
        setup_logging(config.verbose)

        # Validate and prepare directories
        if not setup_directories(config):
            return 1

        # Start FastAPI server
        logging.info(f"Starting server on http://{config.host}:{config.port}")
        start_server(config)

        return 0

    except KeyboardInterrupt:
        logging.info("Process interrupted by user.")
        return 0
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        if 'config' in locals() and config.verbose:
            logging.exception("Exception details:")
        return 1


if __name__ == "__main__":
    # Register signal handlers for clean shutdown
    def handle_signal(sig, frame):
        logging.info(f"Received signal {sig}, exiting gracefully.")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    sys.exit(main())
