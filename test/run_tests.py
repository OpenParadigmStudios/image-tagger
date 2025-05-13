#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Test runner script

import unittest
import sys
import os
import argparse
import time
import logging
import pytest
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path to allow importing test modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def discover_tests(pattern=None, performance=False, edge_cases=True):
    """Discover all test modules."""
    test_dir = Path(__file__).parent

    # Start with standard tests
    test_modules = [
        "test.test_filesystem",
        "test.test_session",
        "test.test_image_processing",
        "test.test_tagging",
        "test.test_integration",
        "test.test_api_models",
        "test.test_api_endpoints",
        "test.test_websocket"
    ]

    # Add edge case tests if requested
    if edge_cases:
        test_modules.append("test.test_edge_cases")

    # Add performance tests if requested
    if performance:
        test_modules.append("test.test_performance")

    # If pattern specified, filter test modules
    if pattern:
        test_modules = [m for m in test_modules if pattern.lower() in m.lower()]

    return test_modules

def run_tests(test_modules, verbosity=1):
    """Run the specified test modules."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add each test module to the suite
    for module_name in test_modules:
        try:
            # Import the module
            __import__(module_name)
            module = sys.modules[module_name]

            # Add all tests from the module
            module_tests = loader.loadTestsFromModule(module)
            suite.addTest(module_tests)
            logger.info(f"Added tests from {module_name}")
        except ImportError as e:
            logger.error(f"Error importing {module_name}: {e}")

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)

def run_pytest_tests():
    """Run tests using pytest for asyncio support."""
    logger.info("Running pytest for asyncio tests...")
    pytest_args = ["-v", str(Path(__file__).parent), "--capture=no", "-xvs"]
    return pytest.main(pytest_args)

def run_browser_tests():
    """Run browser compatibility tests if available."""
    try:
        from test import browser_compatibility
        logger.info("Running browser compatibility tests...")
        tester = browser_compatibility.BrowserCompatibilityTest()
        tester.run_tests()
    except ImportError:
        logger.error("Browser compatibility tests require Selenium. Install with 'pip install selenium'")

def main():
    """Parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Run CivitAI Tagger tests")
    parser.add_argument(
        "-p", "--pattern",
        help="Pattern to filter test modules",
        default=None
    )
    parser.add_argument(
        "-v", "--verbose",
        help="Verbose output",
        action="store_true"
    )
    parser.add_argument(
        "--performance",
        help="Include performance tests (slow)",
        action="store_true"
    )
    parser.add_argument(
        "--no-edge-cases",
        help="Exclude edge case tests",
        action="store_true"
    )
    parser.add_argument(
        "--browser",
        help="Run browser compatibility tests",
        action="store_true"
    )
    parser.add_argument(
        "--all",
        help="Run all tests including performance and browser tests",
        action="store_true"
    )
    parser.add_argument(
        "--pytest",
        help="Use pytest for running all tests (required for asyncio tests)",
        action="store_true"
    )

    args = parser.parse_args()

    # Determine verbosity level
    verbosity = 2 if args.verbose else 1

    # Start timing
    start_time = time.time()

    # Use pytest if specified
    if args.pytest:
        result_code = run_pytest_tests()
        # Print summary
        duration = time.time() - start_time
        logger.info(f"Tests completed in {duration:.2f} seconds with exit code {result_code}.")
        return result_code

    # Discover test modules
    test_modules = discover_tests(
        pattern=args.pattern,
        performance=args.performance or args.all,
        edge_cases=not args.no_edge_cases
    )

    if not test_modules:
        logger.error("No test modules found matching pattern.")
        return 1

    # Run unit tests
    logger.info(f"Running tests: {', '.join(test_modules)}")
    result = run_tests(test_modules, verbosity=verbosity)

    # Run browser tests if requested
    if args.browser or args.all:
        run_browser_tests()

    # Print summary
    duration = time.time() - start_time
    logger.info(f"Tests completed in {duration:.2f} seconds.")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")

    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())
