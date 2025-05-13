#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Browser compatibility testing script

"""
This script is used to test browser compatibility for the web interface.
It requires Selenium WebDriver and appropriate browser drivers installed.

Note: This is a manual test script and requires additional setup:
- Install Selenium: pip install selenium
- Download browser drivers for Chrome, Firefox, etc.
- Set browser driver paths in the script or add to PATH

Usage:
python browser_compatibility.py

The script will generate a report of compatibility issues in each browser.
"""

import time
import logging
import subprocess
import signal
import sys
import os
from pathlib import Path
import tempfile
import shutil

# Configure these paths for your environment or add drivers to PATH
CHROME_DRIVER_PATH = ""  # Leave empty if in PATH
FIREFOX_DRIVER_PATH = ""  # Leave empty if in PATH
SAFARI_DRIVER_PATH = ""   # Leave empty if in PATH (macOS only)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
except ImportError:
    print("Selenium is not installed. Please install it with: pip install selenium")
    print("This script is for manual testing and requires additional setup.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BrowserCompatibilityTest:
    """Class to test browser compatibility for the web interface."""

    def __init__(self, url="http://localhost:8000"):
        """Initialize with server URL."""
        self.url = url
        self.server_process = None
        self.test_dir = None
        self.browsers_to_test = self._get_available_browsers()

        # Test results
        self.results = {}

    def _get_available_browsers(self):
        """Determine which browsers are available for testing."""
        browsers = []

        # Check Chrome
        try:
            if CHROME_DRIVER_PATH:
                webdriver.Chrome(executable_path=CHROME_DRIVER_PATH)
            else:
                webdriver.Chrome()
            browsers.append("chrome")
            logger.info("Chrome is available for testing")
        except (WebDriverException, Exception):
            logger.warning("Chrome WebDriver not available")

        # Check Firefox
        try:
            if FIREFOX_DRIVER_PATH:
                webdriver.Firefox(executable_path=FIREFOX_DRIVER_PATH)
            else:
                webdriver.Firefox()
            browsers.append("firefox")
            logger.info("Firefox is available for testing")
        except (WebDriverException, Exception):
            logger.warning("Firefox WebDriver not available")

        # Check Safari (macOS only)
        if sys.platform == 'darwin':
            try:
                if SAFARI_DRIVER_PATH:
                    webdriver.Safari(executable_path=SAFARI_DRIVER_PATH)
                else:
                    webdriver.Safari()
                browsers.append("safari")
                logger.info("Safari is available for testing")
            except (WebDriverException, Exception):
                logger.warning("Safari WebDriver not available")

        return browsers

    def setup_test_environment(self):
        """Create a test environment with sample images."""
        self.test_dir = Path(tempfile.mkdtemp())
        input_dir = self.test_dir / "test_images"
        input_dir.mkdir()

        # Create a few test images
        for i in range(5):
            test_img = input_dir / f"test_image_{i}.jpg"
            test_img.write_bytes(b"FAKE IMAGE DATA")

        logger.info(f"Created test environment at {self.test_dir}")
        return input_dir

    def start_server(self, input_dir):
        """Start the application server for testing."""
        try:
            # Run the main application in a subprocess
            cmd = [sys.executable, "main.py", str(input_dir)]
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Give the server some time to start
            time.sleep(5)
            logger.info("Server started")
            return True
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False

    def stop_server(self):
        """Stop the application server."""
        if self.server_process:
            # Send termination signal
            self.server_process.send_signal(signal.SIGTERM)
            try:
                # Wait for process to terminate
                self.server_process.wait(timeout=5)
                logger.info("Server stopped")
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                self.server_process.kill()
                logger.warning("Server forcefully terminated")

            self.server_process = None

    def cleanup(self):
        """Clean up test environment."""
        if self.test_dir and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            logger.info("Test environment cleaned up")

    def test_browser(self, browser_name):
        """Test application in specific browser."""
        driver = None
        result = {
            "browser": browser_name,
            "success": False,
            "issues": []
        }

        logger.info(f"Testing in {browser_name}")

        try:
            # Initialize the appropriate WebDriver
            if browser_name == "chrome":
                options = webdriver.ChromeOptions()
                options.add_argument("--headless")  # Comment this for visual debugging
                if CHROME_DRIVER_PATH:
                    driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, options=options)
                else:
                    driver = webdriver.Chrome(options=options)
            elif browser_name == "firefox":
                options = webdriver.FirefoxOptions()
                options.add_argument("--headless")  # Comment this for visual debugging
                if FIREFOX_DRIVER_PATH:
                    driver = webdriver.Firefox(executable_path=FIREFOX_DRIVER_PATH, options=options)
                else:
                    driver = webdriver.Firefox(options=options)
            elif browser_name == "safari":
                # Safari doesn't support headless mode
                if SAFARI_DRIVER_PATH:
                    driver = webdriver.Safari(executable_path=SAFARI_DRIVER_PATH)
                else:
                    driver = webdriver.Safari()

            # Set window size
            driver.set_window_size(1366, 768)

            # Test the application UI
            driver.get(self.url)

            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "app"))
            )

            # Test elements
            result["elements"] = self._test_elements(driver)

            # Test functionality
            result["functionality"] = self._test_functionality(driver)

            # Test responsiveness
            result["responsiveness"] = self._test_responsiveness(driver)

            # If we reached here without exceptions, test is generally successful
            result["success"] = True

        except Exception as e:
            logger.error(f"Error testing {browser_name}: {str(e)}")
            result["issues"].append(f"Fatal error: {str(e)}")

        finally:
            if driver:
                driver.quit()
                logger.info(f"Completed testing in {browser_name}")

            return result

    def _test_elements(self, driver):
        """Test that all UI elements are present and visible."""
        element_results = {
            "all_present": True,
            "missing": []
        }

        # Elements to check - update based on your actual UI
        elements_to_check = {
            "app": "app",
            "image_viewer": "image-viewer",
            "tag_container": "tag-container",
            "session_controls": "session-controls"
        }

        for name, element_id in elements_to_check.items():
            try:
                element = driver.find_element(By.ID, element_id)
                if not element.is_displayed():
                    element_results["all_present"] = False
                    element_results["missing"].append(f"{name} (hidden)")
            except Exception:
                element_results["all_present"] = False
                element_results["missing"].append(name)

        return element_results

    def _test_functionality(self, driver):
        """Test basic functionality."""
        functionality_results = {
            "all_working": True,
            "issues": []
        }

        # Test WebSocket connection
        try:
            # Wait for WebSocket status indicator
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "connection-status"))
            )

            # Check connection status
            status_elem = driver.find_element(By.ID, "connection-status")
            if "connected" not in status_elem.get_attribute("class"):
                functionality_results["all_working"] = False
                functionality_results["issues"].append("WebSocket connection failed")
        except Exception as e:
            functionality_results["all_working"] = False
            functionality_results["issues"].append(f"WebSocket check error: {str(e)}")

        # Test tag selection (simplified)
        try:
            # Add a tag if input exists
            tag_input = driver.find_element(By.ID, "tag-input")
            tag_input.send_keys("test_tag")
            tag_input.send_keys(Keys.ENTER)

            # Check if tag was added
            time.sleep(1)  # Give time for UI to update
            tag_elements = driver.find_elements(By.CLASS_NAME, "tag")
            if not tag_elements or "test_tag" not in driver.page_source:
                functionality_results["all_working"] = False
                functionality_results["issues"].append("Tag addition failed")
        except Exception as e:
            functionality_results["all_working"] = False
            functionality_results["issues"].append(f"Tag functionality error: {str(e)}")

        return functionality_results

    def _test_responsiveness(self, driver):
        """Test UI responsiveness at different screen sizes."""
        responsive_results = {
            "all_responsive": True,
            "issues": []
        }

        # Test different screen sizes
        sizes = [
            (320, 568),   # Mobile
            (768, 1024),  # Tablet
            (1366, 768),  # Laptop
            (1920, 1080)  # Desktop
        ]

        for width, height in sizes:
            driver.set_window_size(width, height)
            time.sleep(1)  # Allow time for responsive layout to adjust

            # Check if main elements are still visible
            try:
                app = driver.find_element(By.ID, "app")
                if not app.is_displayed():
                    responsive_results["all_responsive"] = False
                    responsive_results["issues"].append(f"App not visible at {width}x{height}")
            except Exception as e:
                responsive_results["all_responsive"] = False
                responsive_results["issues"].append(f"Error at {width}x{height}: {str(e)}")

        return responsive_results

    def run_tests(self):
        """Run tests on all available browsers."""
        logger.info("Starting browser compatibility tests")

        if not self.browsers_to_test:
            logger.error("No browsers available for testing")
            return False

        try:
            # Setup test environment
            input_dir = self.setup_test_environment()

            # Start server
            if not self.start_server(input_dir):
                return False

            # Test each browser
            for browser in self.browsers_to_test:
                self.results[browser] = self.test_browser(browser)

            # Output results
            self._print_results()

            return True

        finally:
            # Clean up
            self.stop_server()
            self.cleanup()

    def _print_results(self):
        """Print test results in a readable format."""
        logger.info("\n===== BROWSER COMPATIBILITY TEST RESULTS =====")

        for browser, result in self.results.items():
            logger.info(f"\n{browser.upper()} - {'PASS' if result['success'] else 'FAIL'}")

            # Elements
            elements = result.get("elements", {})
            if elements:
                logger.info(f"  UI Elements: {'All Present' if elements.get('all_present', False) else 'Issues Found'}")
                for missing in elements.get("missing", []):
                    logger.warning(f"    - Missing: {missing}")

            # Functionality
            functionality = result.get("functionality", {})
            if functionality:
                logger.info(f"  Functionality: {'All Working' if functionality.get('all_working', False) else 'Issues Found'}")
                for issue in functionality.get("issues", []):
                    logger.warning(f"    - {issue}")

            # Responsiveness
            responsiveness = result.get("responsiveness", {})
            if responsiveness:
                logger.info(f"  Responsiveness: {'Good' if responsiveness.get('all_responsive', False) else 'Issues Found'}")
                for issue in responsiveness.get("issues", []):
                    logger.warning(f"    - {issue}")

            # Other issues
            for issue in result.get("issues", []):
                logger.error(f"    - {issue}")

        logger.info("\n=== END OF TEST RESULTS ===")


def main():
    """Main function to run browser compatibility tests."""
    tester = BrowserCompatibilityTest()
    tester.run_tests()


if __name__ == "__main__":
    main()
