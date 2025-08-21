#!/usr/bin/env python3
"""
Comprehensive Test Runner for Quantum State Visualizer
Runs backend API tests, frontend UI tests, and integration tests
"""
import os
import sys
import time
import subprocess
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

# Add test modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'frontend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'circuits'))

def setup_logging(workspace_root: Path) -> tuple[logging.Logger, str]:
    """Setup logging configuration with file and console handlers"""
    
    # Create logs directory
    logs_dir = workspace_root / "tests" / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create timestamp for this test run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"test_run_{timestamp}.log"
    log_filepath = logs_dir / log_filename
    
    # Setup logger
    logger = logging.getLogger('quantum_test_runner')
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # File handler - detailed logging
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler - important messages only
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, str(log_filepath)

def log_section(logger: logging.Logger, title: str, char: str = "="):
    """Log a section header to both file and console"""
    line = char * 60
    logger.info(f"\n{line}")
    logger.info(f"{title}")
    logger.info(line)

def check_service_health(url: str, service_name: str, logger: logging.Logger, timeout: int = 5) -> bool:
    """Check if a service is running and healthy"""
    try:
        import requests
        logger.debug(f"Checking health of {service_name} at {url}")
        response = requests.get(f"{url}/health", timeout=timeout)
        if response.status_code == 200:
            logger.info(f"✓ {service_name} is running at {url}")
            logger.debug(f"{service_name} health response: {response.json()}")
            return True
        else:
            logger.warning(f"✗ {service_name} responded with status {response.status_code}")
            logger.debug(f"{service_name} response content: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        logger.warning(f"✗ {service_name} is not reachable at {url}")
        return False
    except Exception as e:
        logger.error(f"✗ {service_name} health check failed: {e}")
        return False

def wait_for_service(url: str, service_name: str, logger: logging.Logger, max_wait: int = 30) -> bool:
    """Wait for a service to become available"""
    logger.info(f"Waiting for {service_name} at {url}...")
    
    for i in range(max_wait):
        if check_service_health(url, service_name, logger):
            return True
        time.sleep(1)
        if i > 0 and i % 5 == 0:
            logger.debug(f"Still waiting for {service_name}... ({i}s)")
    
    logger.error(f"Timeout waiting for {service_name} after {max_wait}s")
    return False

def start_backend_if_needed(backend_path: str, backend_url: str, logger: logging.Logger) -> subprocess.Popen:
    """Start backend server if it's not running"""
    if check_service_health(backend_url, "Backend", logger):
        logger.info("Backend is already running")
        return None
    
    logger.info("Starting backend server...")
    
    # Change to backend directory
    original_cwd = os.getcwd()
    os.chdir(backend_path)
    
    try:
        # Start the backend
        logger.debug(f"Starting backend from directory: {backend_path}")
        process = subprocess.Popen(
            [sys.executable, "start.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for backend to start
        if wait_for_service(backend_url, "Backend", logger, 20):
            logger.info("✓ Backend started successfully")
            logger.debug(f"Backend process PID: {process.pid}")
            os.chdir(original_cwd)
            return process
        else:
            logger.error("✗ Failed to start backend")
            process.terminate()
            os.chdir(original_cwd)
            return None
            
    except Exception as e:
        logger.error(f"✗ Failed to start backend: {e}")
        os.chdir(original_cwd)
        return None

def start_frontend_if_needed(frontend_path: str, frontend_url: str, logger: logging.Logger) -> subprocess.Popen:
    """Start frontend server if it's not running"""
    # Simple check - try to connect to frontend URL
    try:
        import requests
        response = requests.get(frontend_url, timeout=5)
        if response.status_code == 200:
            logger.info("✓ Frontend is already running")
            return None
    except:
        pass
    
    logger.info("Starting frontend server...")
    
    # Change to frontend directory
    original_cwd = os.getcwd()
    os.chdir(frontend_path)
    
    try:
        # Check if we have bun or npm
        logger.debug("Checking for package managers...")
        if subprocess.run(["which", "bun"], capture_output=True).returncode == 0:
            cmd = ["bun", "run", "dev", "--host", "0.0.0.0"]
            logger.debug("Using bun to start frontend")
        elif subprocess.run(["which", "npm"], capture_output=True).returncode == 0:
            cmd = ["npm", "run", "dev"]
            logger.debug("Using npm to start frontend")
        else:
            logger.error("✗ Neither bun nor npm found")
            os.chdir(original_cwd)
            return None
        
        logger.debug(f"Starting frontend with command: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for frontend to start
        logger.info("Waiting for frontend to start...")
        time.sleep(10)  # Frontend typically takes longer to start
        
        try:
            import requests
            response = requests.get(frontend_url, timeout=5)
            if response.status_code == 200:
                logger.info("✓ Frontend started successfully")
                logger.debug(f"Frontend process PID: {process.pid}")
                os.chdir(original_cwd)
                return process
            else:
                logger.warning("✗ Frontend not responding correctly")
        except:
            logger.error("✗ Frontend failed to start")
        
        process.terminate()
        os.chdir(original_cwd)
        return None
        
    except Exception as e:
        logger.error(f"✗ Failed to start frontend: {e}")
        os.chdir(original_cwd)
        return None

def run_backend_tests(backend_url: str, logger: logging.Logger, test_specific_circuit: str = None) -> dict:
    """Run backend API tests"""
    try:
        from test_api import QuantumStateVisualizerBackendTester
        
        log_section(logger, "RUNNING BACKEND API TESTS")
        
        tester = QuantumStateVisualizerBackendTester(backend_url, logger)
        
        if test_specific_circuit:
            from test_circuits import TEST_CIRCUITS
            if test_specific_circuit in TEST_CIRCUITS:
                logger.info(f"Testing specific circuit: {test_specific_circuit}")
                tester.test_simulate_endpoint_with_circuit(
                    test_specific_circuit, 
                    TEST_CIRCUITS[test_specific_circuit]
                )
                result = {
                    "passed": tester.test_results["passed"],
                    "failed": tester.test_results["failed"],
                    "errors": tester.test_results["errors"],
                    "test_type": "backend"
                }
                logger.debug(f"Backend test result: {result}")
                return result
            else:
                logger.error(f"Unknown circuit: {test_specific_circuit}")
                return {"passed": 0, "failed": 1, "errors": ["Unknown circuit"], "test_type": "backend"}
        else:
            result = {**tester.run_all_tests(), "test_type": "backend"}
            logger.debug(f"Backend test result: {result}")
            return result
            
    except ImportError as e:
        logger.error(f"Failed to import backend test module: {e}")
        return {"passed": 0, "failed": 1, "errors": [str(e)], "test_type": "backend"}
    except Exception as e:
        logger.error(f"Backend tests failed: {e}")
        logger.debug(f"Backend test exception details:", exc_info=True)
        return {"passed": 0, "failed": 1, "errors": [str(e)], "test_type": "backend"}

def run_frontend_tests(frontend_url: str, backend_url: str, logger: logging.Logger, headless: bool = True) -> dict:
    """Run frontend UI tests"""
    try:
        from test_ui import QuantumStateVisualizerFrontendTester, check_prerequisites
        
        if not check_prerequisites():
            logger.error("ChromeDriver not available")
            return {
                "passed": 0, 
                "failed": 1, 
                "errors": ["ChromeDriver not available"], 
                "test_type": "frontend"
            }
        
        log_section(logger, "RUNNING FRONTEND UI TESTS")
        
        tester = QuantumStateVisualizerFrontendTester(frontend_url, backend_url, logger)
        
        # Override headless setting if requested
        if not headless:
            logger.info("Running frontend tests with visible browser")
            tester.driver.quit()
            from selenium.webdriver.chrome.options import Options
            from selenium import webdriver
            from selenium.webdriver.support.ui import WebDriverWait
            
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            tester.driver = webdriver.Chrome(options=chrome_options)
            tester.wait = WebDriverWait(tester.driver, 10)
        
        try:
            results = tester.run_all_tests()
            result = {**results, "test_type": "frontend"}
            logger.debug(f"Frontend test result: {result}")
            return result
        finally:
            tester.teardown()
            
    except ImportError as e:
        logger.error(f"Failed to import frontend test module (missing selenium?): {e}")
        logger.info("Install selenium: pip install selenium")
        return {"passed": 0, "failed": 1, "errors": [str(e)], "test_type": "frontend"}
    except Exception as e:
        logger.error(f"Frontend tests failed: {e}")
        logger.debug(f"Frontend test exception details:", exc_info=True)
        return {"passed": 0, "failed": 1, "errors": [str(e)], "test_type": "frontend"}

def generate_test_report(results: list, logger: logging.Logger, output_file: str = None):
    """Generate a comprehensive test report"""
    total_passed = sum(r.get("passed", 0) for r in results)
    total_failed = sum(r.get("failed", 0) for r in results)
    total_tests = total_passed + total_failed
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
        },
        "results_by_type": {}
    }
    
    # Organize results by test type
    for result in results:
        test_type = result.get("test_type", "unknown")
        report["results_by_type"][test_type] = {
            "passed": result.get("passed", 0),
            "failed": result.get("failed", 0),
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", [])
        }
    
    # Log report to both file and console
    log_section(logger, "COMPREHENSIVE TEST REPORT")
    logger.info(f"Timestamp: {report['timestamp']}")
    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed: {total_passed}")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    
    logger.info("\n--- RESULTS BY TEST TYPE ---")
    for test_type, type_results in report["results_by_type"].items():
        logger.info(f"\n{test_type.upper()} TESTS:")
        logger.info(f"  Passed: {type_results['passed']}")
        logger.info(f"  Failed: {type_results['failed']}")
        
        if type_results.get("errors"):
            logger.info("  Errors:")
            for error in type_results["errors"][:5]:  # Show first 5
                logger.info(f"    - {error}")
                logger.debug(f"Full error details: {error}")  # Full details in log file only
        
        if type_results.get("warnings"):
            logger.info("  Warnings:")
            for warning in type_results["warnings"][:3]:  # Show first 3
                logger.info(f"    - {warning}")
                logger.debug(f"Full warning details: {warning}")  # Full details in log file only
    
    # Save to file if requested
    if output_file:
        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"\n✓ Report saved to {output_file}")
            logger.debug(f"Report content: {json.dumps(report, indent=2)}")
        except Exception as e:
            logger.error(f"\n✗ Failed to save report: {e}")
    
    return report

def main():
    parser = argparse.ArgumentParser(description="Quantum State Visualizer Test Runner")
    parser.add_argument("--backend-url", default="http://localhost:8001", help="Backend URL")
    parser.add_argument("--frontend-url", default="http://localhost:5173", help="Frontend URL")
    parser.add_argument("--auto-start", action="store_true", help="Automatically start services if needed")
    parser.add_argument("--backend-only", action="store_true", help="Run only backend tests")
    parser.add_argument("--frontend-only", action="store_true", help="Run only frontend tests")
    parser.add_argument("--no-headless", action="store_true", help="Run frontend tests with visible browser")
    parser.add_argument("--circuit", help="Test specific circuit only (backend tests)")
    parser.add_argument("--report", help="Save test report to file")
    parser.add_argument("--workspace", help="Workspace root path", 
                       default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging to console")
    
    args = parser.parse_args()
    
    # Set up paths
    workspace_root = Path(args.workspace)
    backend_path = workspace_root / "backend"
    frontend_path = workspace_root / "frontend"
    
    # Setup logging
    logger, log_filepath = setup_logging(workspace_root)
    
    # Adjust console log level based on verbose flag
    if args.verbose:
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.DEBUG)
    
    # Start logging
    log_section(logger, "QUANTUM STATE VISUALIZER - TEST RUNNER")
    logger.info(f"Workspace: {workspace_root}")
    logger.info(f"Backend Path: {backend_path}")
    logger.info(f"Frontend Path: {frontend_path}")
    logger.info(f"Log File: {log_filepath}")
    logger.debug(f"Command line arguments: {vars(args)}")
    
    # Validate paths
    if not backend_path.exists():
        logger.error(f"✗ Backend path not found: {backend_path}")
        sys.exit(1)
    
    if not frontend_path.exists():
        logger.error(f"✗ Frontend path not found: {frontend_path}")
        sys.exit(1)
    
    # Track started processes
    started_backend = None
    started_frontend = None
    
    try:
        # Start services if needed
        if args.auto_start:
            if not args.frontend_only:
                logger.info("Checking backend service...")
                started_backend = start_backend_if_needed(str(backend_path), args.backend_url, logger)
                if started_backend is None and not check_service_health(args.backend_url, "Backend", logger):
                    logger.error("✗ Failed to start backend and backend is not running")
                    sys.exit(1)
            
            if not args.backend_only:
                logger.info("Checking frontend service...")
                started_frontend = start_frontend_if_needed(str(frontend_path), args.frontend_url, logger)
                if started_frontend is None:
                    # Check if frontend is actually running
                    try:
                        import requests
                        response = requests.get(args.frontend_url, timeout=5)
                        if response.status_code != 200:
                            logger.warning("✗ Frontend is not accessible")
                    except:
                        logger.warning("✗ Failed to start frontend and frontend is not running")
                        if not args.backend_only:
                            logger.info("Consider running frontend manually or use --backend-only flag")
        
        # Run tests
        test_results = []
        
        if not args.frontend_only:
            logger.info("Running backend tests...")
            backend_results = run_backend_tests(args.backend_url, logger, args.circuit)
            test_results.append(backend_results)
        
        if not args.backend_only:
            logger.info("Running frontend tests...")
            frontend_results = run_frontend_tests(
                args.frontend_url, 
                args.backend_url, 
                logger,
                not args.no_headless
            )
            test_results.append(frontend_results)
        
        # Generate report
        logger.info("Generating test report...")
        report = generate_test_report(test_results, logger, args.report)
        
        # Final summary
        total_failed = sum(r.get("failed", 0) for r in test_results)
        if total_failed > 0:
            logger.info(f"\n✗ Tests completed with {total_failed} failures")
            logger.info(f"Full details available in: {log_filepath}")
            sys.exit(1)
        else:
            logger.info(f"\n✓ All tests passed!")
            logger.info(f"Full details available in: {log_filepath}")
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.warning("\n\nTest run interrupted by user")
        sys.exit(1)
    
    finally:
        # Clean up started processes
        if started_backend:
            logger.info("Stopping backend...")
            started_backend.terminate()
            try:
                started_backend.wait(timeout=5)
                logger.debug("Backend process terminated cleanly")
            except subprocess.TimeoutExpired:
                logger.warning("Backend process did not terminate cleanly, killing...")
                started_backend.kill()
        
        if started_frontend:
            logger.info("Stopping frontend...")
            started_frontend.terminate()
            try:
                started_frontend.wait(timeout=5)
                logger.debug("Frontend process terminated cleanly")
            except subprocess.TimeoutExpired:
                logger.warning("Frontend process did not terminate cleanly, killing...")
                started_frontend.kill()
        
        logger.info(f"Test run completed. Full log saved to: {log_filepath}")

if __name__ == "__main__":
    main()
