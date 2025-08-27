"""
Frontend Component Test Suite for QubitLens
Tests React components, state management, and API integration
"""
import json
import time
import subprocess
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'circuits'))
from test_circuits import TEST_CIRCUITS

class QuantumStateVisualizerFrontendTester:
    def __init__(self, frontend_url: str = "http://localhost:5173", backend_url: str = "http://localhost:8001", logger = None):
        self.frontend_url = frontend_url
        self.backend_url = backend_url
        self.driver = None
        self.wait = None
        self.logger = logger
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "warnings": []
        }
        
        # Setup Chrome driver with options
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run headless Chrome
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            if self.logger:
                self.logger.debug("Chrome WebDriver setup completed")
            
        except Exception as e:
            error_msg = f"Failed to setup Chrome driver: {e}"
            if self.logger:
                self.logger.error(error_msg)
                self.logger.info("Please install ChromeDriver and Chrome browser")
            else:
                print(error_msg)
                print("Please install ChromeDriver and Chrome browser")
            sys.exit(1)
    
    def teardown(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
    
    def log_test(self, test_name: str, status: str, message: str = ""):
        """Log test result"""
        log_msg = f"[{status}] {test_name}: {message}"
        if self.logger:
            if status == "PASS":
                self.logger.info(log_msg)
            elif status == "WARNING":
                self.logger.warning(log_msg)
            else:
                self.logger.error(log_msg)
        else:
            print(log_msg)
            
        if status == "PASS":
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
            
        if status == "WARNING":
            self.test_results["warnings"].append(f"{test_name}: {message}")
    
    def wait_for_element(self, by, value, timeout=10):
        """Wait for element to be present and visible"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def test_page_load(self):
        """Test if the main page loads successfully"""
        try:
            self.driver.get(self.frontend_url)
            
            # Wait for page title
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.title != ""
            )
            
            # Check if React app has loaded
            app_element = self.wait_for_element(By.ID, "root")
            if app_element:
                self.log_test("Page Load", "PASS", f"Title: {self.driver.title}")
            else:
                self.log_test("Page Load", "FAIL", "React app root not found")
                
        except Exception as e:
            self.log_test("Page Load", "FAIL", f"Exception: {str(e)}")
    
    def test_editor_panel_exists(self):
        """Test if the QASM editor panel is present"""
        try:
            # Look for common editor elements
            editor_selectors = [
                "[data-testid='qasm-editor']",
                ".monaco-editor",
                "textarea[placeholder*='QASM']",
                "textarea[placeholder*='quantum']",
                ".editor-panel",
                "#qasm-input"
            ]
            
            editor_found = False
            for selector in editor_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        editor_found = True
                        self.log_test("Editor Panel", "PASS", f"Found editor with selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            if not editor_found:
                # Try to find any textarea or input element
                textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                
                if textareas or inputs:
                    self.log_test("Editor Panel", "WARNING", 
                                f"Found {len(textareas)} textareas and {len(inputs)} inputs, but no clear QASM editor")
                else:
                    self.log_test("Editor Panel", "FAIL", "No editor panel found")
                    
        except Exception as e:
            self.log_test("Editor Panel", "FAIL", f"Exception: {str(e)}")
    
    def test_controls_bar_exists(self):
        """Test if control buttons are present"""
        try:
            # Look for common control elements
            control_selectors = [
                "button[data-testid='simulate-button']",
                "button[data-testid='run-button']",
                "button:contains('Simulate')",
                "button:contains('Run')",
                ".controls-bar button",
                ".toolbar button"
            ]
            
            buttons_found = []
            for selector in control_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    buttons_found.extend([el for el in elements if el.is_displayed()])
                except:
                    continue
            
            if buttons_found:
                self.log_test("Controls Bar", "PASS", f"Found {len(buttons_found)} control buttons")
            else:
                # Count all buttons
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                visible_buttons = [btn for btn in all_buttons if btn.is_displayed()]
                
                if visible_buttons:
                    self.log_test("Controls Bar", "WARNING", 
                                f"Found {len(visible_buttons)} buttons, but no clear control bar")
                else:
                    self.log_test("Controls Bar", "FAIL", "No control buttons found")
                    
        except Exception as e:
            self.log_test("Controls Bar", "FAIL", f"Exception: {str(e)}")
    
    def test_canvas_area_exists(self):
        """Test if the 3D visualization canvas is present"""
        try:
            # Look for canvas elements (Three.js typically uses canvas)
            canvas_selectors = [
                "canvas[data-testid='bloch-canvas']",
                ".bloch-sphere canvas",
                ".visualization-canvas",
                ".three-canvas",
                "canvas"
            ]
            
            canvas_found = False
            for selector in canvas_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.size['width'] > 100:
                            canvas_found = True
                            width = element.size['width']
                            height = element.size['height']
                            self.log_test("Canvas Area", "PASS", 
                                        f"Found canvas: {width}x{height}px")
                            break
                except:
                    continue
                    
                if canvas_found:
                    break
            
            if not canvas_found:
                self.log_test("Canvas Area", "FAIL", "No visualization canvas found")
                
        except Exception as e:
            self.log_test("Canvas Area", "FAIL", f"Exception: {str(e)}")
    
    def test_simulation_with_sample_circuit(self, circuit_name: str, circuit_data: dict):
        """Test running a simulation with a sample circuit"""
        try:
            # First, check if backend is available
            backend_response = requests.get(f"{self.backend_url}/health", timeout=5)
            if backend_response.status_code != 200:
                self.log_test(f"Simulation: {circuit_name}", "SKIP", "Backend not available")
                return
            
            # Find editor input
            editor_element = None
            editor_selectors = [
                "textarea[data-testid='qasm-editor']",
                ".monaco-editor textarea",
                "textarea",
                "#qasm-input"
            ]
            
            for selector in editor_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        editor_element = element
                        break
                except:
                    continue
            
            if not editor_element:
                self.log_test(f"Simulation: {circuit_name}", "FAIL", "No editor input found")
                return
            
            # Clear and enter QASM code
            editor_element.clear()
            editor_element.send_keys(circuit_data["qasm"])
            
            # Find and click simulate button
            simulate_button = None
            button_selectors = [
                "button[data-testid='simulate-button']",
                "button:contains('Simulate')",
                "button:contains('Run')",
                "button"
            ]
            
            for selector in button_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and ("simulate" in button.text.lower() or 
                                                    "run" in button.text.lower()):
                            simulate_button = button
                            break
                    if simulate_button:
                        break
                except:
                    continue
            
            if not simulate_button:
                self.log_test(f"Simulation: {circuit_name}", "FAIL", "No simulate button found")
                return
            
            # Click simulate button
            simulate_button.click()
            
            # Wait for simulation to complete (look for results or error messages)
            time.sleep(2)  # Give time for API call
            
            # Check for error messages
            error_selectors = [
                ".error-message",
                ".alert-error",
                "[data-testid='error']",
                ".text-red-500"
            ]
            
            has_error = False
            for selector in error_selectors:
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for error_elem in error_elements:
                        if error_elem.is_displayed() and error_elem.text.strip():
                            has_error = True
                            self.log_test(f"Simulation: {circuit_name}", "FAIL", 
                                        f"Error: {error_elem.text}")
                            break
                    if has_error:
                        break
                except:
                    continue
            
            if not has_error:
                # Check if visualization was updated (canvas changes, new elements)
                # This is a basic check - in a real test you might check for specific changes
                success_indicators = [
                    ".simulation-results",
                    ".bloch-sphere",
                    ".state-info",
                    "canvas"
                ]
                
                found_results = False
                for selector in success_indicators:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if any(elem.is_displayed() for elem in elements):
                            found_results = True
                            break
                    except:
                        continue
                
                if found_results:
                    self.log_test(f"Simulation: {circuit_name}", "PASS", 
                                "Simulation completed without errors")
                else:
                    self.log_test(f"Simulation: {circuit_name}", "WARNING", 
                                "Simulation ran but no clear results visible")
                    
        except Exception as e:
            self.log_test(f"Simulation: {circuit_name}", "FAIL", f"Exception: {str(e)}")
    
    def test_responsive_design(self):
        """Test responsive design at different screen sizes"""
        try:
            screen_sizes = [
                ("Desktop", 1920, 1080),
                ("Tablet", 768, 1024),
                ("Mobile", 375, 667)
            ]
            
            for size_name, width, height in screen_sizes:
                self.driver.set_window_size(width, height)
                time.sleep(1)  # Let layout adjust
                
                # Check if main elements are still visible
                body = self.driver.find_element(By.TAG_NAME, "body")
                if body.is_displayed():
                    # Basic check for layout not breaking
                    page_width = self.driver.execute_script("return document.body.scrollWidth")
                    if page_width <= width + 20:  # Allow small margin
                        self.log_test(f"Responsive: {size_name}", "PASS", 
                                    f"{width}x{height} - No horizontal scroll")
                    else:
                        self.log_test(f"Responsive: {size_name}", "WARNING", 
                                    f"{width}x{height} - May have horizontal scroll ({page_width}px wide)")
                else:
                    self.log_test(f"Responsive: {size_name}", "FAIL", 
                                f"{width}x{height} - Body not visible")
            
            # Reset to standard size
            self.driver.set_window_size(1920, 1080)
            
        except Exception as e:
            self.log_test("Responsive Design", "FAIL", f"Exception: {str(e)}")
    
    def test_console_errors(self):
        """Check for JavaScript console errors"""
        try:
            logs = self.driver.get_log('browser')
            errors = [log for log in logs if log['level'] == 'SEVERE']
            
            if errors:
                error_messages = [log['message'] for log in errors[:5]]  # Show first 5 errors
                self.log_test("Console Errors", "WARNING", 
                            f"Found {len(errors)} severe errors: {'; '.join(error_messages)}")
            else:
                self.log_test("Console Errors", "PASS", "No severe console errors")
                
        except Exception as e:
            self.log_test("Console Errors", "FAIL", f"Exception: {str(e)}")
    
    def test_api_integration(self):
        """Test if frontend can communicate with backend"""
        try:
            # Check if backend is reachable from browser context
            # This involves checking network requests or testing simulation
            
            # Navigate to page and wait for load
            self.driver.get(self.frontend_url)
            time.sleep(3)
            
            # Check if there are any failed network requests in browser
            # Note: This is a simplified test - full network monitoring would need more setup
            
            # Check if page loaded without network errors in console
            logs = self.driver.get_log('browser')
            network_errors = [log for log in logs if 'net::' in log.get('message', '')]
            
            if network_errors:
                self.log_test("API Integration", "WARNING", 
                            f"Found {len(network_errors)} potential network errors")
            else:
                # Try to perform a simple API test by attempting simulation
                simple_circuit = TEST_CIRCUITS["single_qubit_superposition"]
                self.test_simulation_with_sample_circuit("API Test", simple_circuit)
                
        except Exception as e:
            self.log_test("API Integration", "FAIL", f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all frontend tests"""
        if self.logger:
            self.logger.info("=" * 80)
            self.logger.info("QUBITLENS - FRONTEND TESTS")
            self.logger.info("=" * 80)
        else:
            print("=" * 80)
            print("QUBITLENS - FRONTEND TESTS")
            print("=" * 80)
        
        # Basic component tests
        if self.logger:
            self.logger.info("\n--- BASIC COMPONENT TESTS ---")
        else:
            print("\n--- BASIC COMPONENT TESTS ---")
        self.test_page_load()
        self.test_editor_panel_exists()
        self.test_controls_bar_exists()
        self.test_canvas_area_exists()
        
        # Functionality tests
        if self.logger:
            self.logger.info("\n--- FUNCTIONALITY TESTS ---")
        else:
            print("\n--- FUNCTIONALITY TESTS ---")
        # Test with a few key circuits
        key_circuits = ["single_qubit_superposition", "bell_state"]
        for circuit_name in key_circuits:
            if circuit_name in TEST_CIRCUITS:
                self.test_simulation_with_sample_circuit(circuit_name, TEST_CIRCUITS[circuit_name])
        
        # Integration and quality tests
        if self.logger:
            self.logger.info("\n--- INTEGRATION AND QUALITY TESTS ---")
        else:
            print("\n--- INTEGRATION AND QUALITY TESTS ---")
        self.test_api_integration()
        self.test_responsive_design()
        self.test_console_errors()
        
        # Print summary
        if self.logger:
            self.logger.info("\n" + "=" * 80)
            self.logger.info("TEST SUMMARY")
            self.logger.info("=" * 80)
            self.logger.info(f"Total Passed: {self.test_results['passed']}")
            self.logger.info(f"Total Failed: {self.test_results['failed']}")
        else:
            print("\n" + "=" * 80)
            print("TEST SUMMARY")
            print("=" * 80)
            print(f"Total Passed: {self.test_results['passed']}")
            print(f"Total Failed: {self.test_results['failed']}")
        
        if self.test_results["errors"]:
            if self.logger:
                self.logger.info("\nErrors:")
                for error in self.test_results["errors"]:
                    self.logger.info(f"  - {error}")
            else:
                print("\nErrors:")
                for error in self.test_results["errors"]:
                    print(f"  - {error}")
        
        if self.test_results["warnings"]:
            if self.logger:
                self.logger.info("\nWarnings:")
                for warning in self.test_results["warnings"]:
                    self.logger.info(f"  - {warning}")
            else:
                print("\nWarnings:")
                for warning in self.test_results["warnings"]:
                    print(f"  - {warning}")
        
        success_rate = self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100 if self.test_results['passed'] + self.test_results['failed'] > 0 else 0
        if self.logger:
            self.logger.info(f"\nSuccess Rate: {success_rate:.1f}%")
        else:
            print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        return self.test_results

def check_prerequisites():
    """Check if required tools are available"""
    try:
        # Check if chromedriver is available
        subprocess.run(["chromedriver", "--version"], capture_output=True, check=True)
        print("✓ ChromeDriver is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ ChromeDriver not found. Please install ChromeDriver:")
        print("  - Ubuntu/Debian: apt-get install chromium-chromedriver")
        print("  - macOS: brew install chromedriver")
        print("  - Windows: Download from https://chromedriver.chromium.org/")
        return False

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test QubitLens Frontend")
    parser.add_argument("--frontend-url", default="http://localhost:5173", help="Frontend URL")
    parser.add_argument("--backend-url", default="http://localhost:8001", help="Backend URL")
    parser.add_argument("--no-headless", action="store_true", help="Run browser in visible mode")
    
    args = parser.parse_args()
    
    if not check_prerequisites():
        sys.exit(1)
    
    tester = None
    try:
        tester = QuantumStateVisualizerFrontendTester(args.frontend_url, args.backend_url)
        results = tester.run_all_tests()
        
        # Exit with non-zero code if tests failed
        if results["failed"] > 0:
            exit(1)
            
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"Test runner failed: {e}")
        exit(1)
    finally:
        if tester:
            tester.teardown()

if __name__ == "__main__":
    main()
