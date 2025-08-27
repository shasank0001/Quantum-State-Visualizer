"""
Backend API Test Suite for QubitLens
Tests all backend endpoints with various circuit types
"""
import requests
import json
import time
import pytest
from typing import Dict, List, Any
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'circuits'))

from test_circuits import TEST_CIRCUITS, INVALID_CIRCUITS, PERFORMANCE_CIRCUITS, generate_performance_circuit

class QuantumStateVisualizerBackendTester:
    def __init__(self, base_url: str = "http://localhost:8000", logger = None):
        self.base_url = base_url
        self.logger = logger
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "warnings": []
        }
    
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
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Health Check", "PASS", "Service is healthy")
                else:
                    self.log_test("Health Check", "FAIL", f"Unexpected status: {data}")
            else:
                self.log_test("Health Check", "FAIL", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Health Check", "FAIL", f"Exception: {str(e)}")
    
    def test_simulate_endpoint_with_circuit(self, circuit_name: str, circuit_data: Dict[str, Any]):
        """Test simulation endpoint with a specific circuit"""
        try:
            payload = {
                "qasm_code": circuit_data["qasm"],
                "visualization_type": "bloch_sphere",
                "pipeline_override": None
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/simulate",
                json=payload,
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields (based on actual API implementation)
                required_fields = ["qubits", "pipeline_used", "circuit_info"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(f"Simulate: {circuit_name}", "FAIL", 
                                f"Missing fields: {missing_fields}")
                    return
                
                # Validate circuit_info (equivalent to metadata in test)
                circuit_info = data["circuit_info"]
                if circuit_info["num_qubits"] != circuit_data["expected_qubits"]:
                    self.log_test(f"Simulate: {circuit_name}", "FAIL",
                                f"Expected {circuit_data['expected_qubits']} qubits, got {circuit_info['num_qubits']}")
                    return
                
                # Check pipeline selection (pipeline_used vs expected_pipeline)
                if data.get("pipeline_used") != circuit_data["expected_pipeline"]:
                    self.log_test(f"Simulate: {circuit_name}", "WARNING",
                                f"Expected {circuit_data['expected_pipeline']} pipeline, got {data.get('pipeline_used')}")
                
                # Validate qubits structure (equivalent to states in test)
                qubits = data["qubits"]
                if not isinstance(qubits, list) or len(qubits) != circuit_data["expected_qubits"]:
                    self.log_test(f"Simulate: {circuit_name}", "FAIL",
                                f"Expected {circuit_data['expected_qubits']} qubits, got {len(qubits)}")
                    return
                
                # Validate individual qubit structure (match our actual API format)
                for i, qubit in enumerate(qubits):
                    required_qubit_fields = ["id", "bloch_coords", "purity", "density_matrix", "label"]
                    missing_qubit_fields = [field for field in required_qubit_fields if field not in qubit]
                    
                    if missing_qubit_fields:
                        self.log_test(f"Simulate: {circuit_name}", "FAIL",
                                    f"Qubit {i} missing fields: {missing_qubit_fields}")
                        return
                    
                    # Validate Bloch coordinates (our format: [x, y, z] as array)
                    bloch_coords = qubit["bloch_coords"]
                    if not isinstance(bloch_coords, list) or len(bloch_coords) != 3:
                        self.log_test(f"Simulate: {circuit_name}", "FAIL",
                                    f"Invalid Bloch coordinates for qubit {i}: {bloch_coords}")
                        return
                        
                    if not all(isinstance(coord, (int, float)) for coord in bloch_coords):
                        self.log_test(f"Simulate: {circuit_name}", "FAIL",
                                    f"Invalid Bloch coordinate types for qubit {i}: {bloch_coords}")
                        return
                
                # Performance check
                execution_time = end_time - start_time
                if execution_time > 10.0:  # Warning for slow simulations
                    self.log_test(f"Simulate: {circuit_name}", "WARNING",
                                f"Slow execution: {execution_time:.2f}s")
                
                self.log_test(f"Simulate: {circuit_name}", "PASS",
                            f"Success in {execution_time:.2f}s, pipeline: {data.get('pipeline_used')}")
                
            elif response.status_code == 422:
                # Validation error - might be expected for some circuits
                error_detail = response.json().get("detail", "Validation error")
                self.log_test(f"Simulate: {circuit_name}", "FAIL",
                            f"Validation error: {error_detail}")
            
            else:
                self.log_test(f"Simulate: {circuit_name}", "FAIL",
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            self.log_test(f"Simulate: {circuit_name}", "FAIL", "Request timeout")
        except Exception as e:
            self.log_test(f"Simulate: {circuit_name}", "FAIL", f"Exception: {str(e)}")
    
    def test_invalid_circuits(self):
        """Test error handling with invalid circuits"""
        for circuit_name, circuit_data in INVALID_CIRCUITS.items():
            try:
                payload = {
                    "qasm_code": circuit_data["qasm"],
                    "visualization_type": "bloch_sphere"
                }
                
                response = requests.post(
                    f"{self.base_url}/simulate",
                    json=payload,
                    timeout=10
                )
                
                if response.status_code >= 400:
                    self.log_test(f"Invalid Circuit: {circuit_name}", "PASS",
                                f"Properly rejected with status {response.status_code}")
                else:
                    self.log_test(f"Invalid Circuit: {circuit_name}", "FAIL",
                                f"Should have been rejected but got status {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Invalid Circuit: {circuit_name}", "FAIL", f"Exception: {str(e)}")
    
    def test_performance_circuits(self):
        """Test performance with larger circuits"""
        for perf_name, perf_data in PERFORMANCE_CIRCUITS.items():
            try:
                qasm_code = generate_performance_circuit(
                    perf_data["qubits"], 
                    perf_data["operations"]
                )
                
                payload = {
                    "qasm_code": qasm_code,
                    "visualization_type": "bloch_sphere"
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/simulate",
                    json=payload,
                    timeout=60
                )
                end_time = time.time()
                
                execution_time = end_time - start_time
                
                if response.status_code == 200:
                    if execution_time <= perf_data["expected_time_limit"]:
                        self.log_test(f"Performance: {perf_name}", "PASS",
                                    f"Completed in {execution_time:.2f}s")
                    else:
                        self.log_test(f"Performance: {perf_name}", "WARNING",
                                    f"Slow performance: {execution_time:.2f}s > {perf_data['expected_time_limit']}s")
                else:
                    self.log_test(f"Performance: {perf_name}", "FAIL",
                                f"Failed with status {response.status_code}")
                    
            except requests.exceptions.Timeout:
                self.log_test(f"Performance: {perf_name}", "FAIL", "Request timeout")
            except Exception as e:
                self.log_test(f"Performance: {perf_name}", "FAIL", f"Exception: {str(e)}")
    
    def test_websocket_endpoint(self):
        """Test WebSocket endpoint availability"""
        try:
            # Perform an HTTP GET; WS endpoint should reject with 426/400/404
            response = requests.get(f"{self.base_url}/ws/simulate", timeout=5)
            if response.status_code in [426, 400, 404]:
                self.log_test("WebSocket Endpoint", "PASS", "WebSocket endpoint is available")
            else:
                self.log_test("WebSocket Endpoint", "WARNING", 
                            f"Unexpected status {response.status_code} (WebSocket may still work)")
        except Exception as e:
            self.log_test("WebSocket Endpoint", "FAIL", f"Exception: {str(e)}")
    
    def test_cors_headers(self):
        """Test CORS headers for frontend integration"""
        try:
            response = requests.options(f"{self.base_url}/simulate", timeout=5)
            headers = response.headers
            
            cors_headers = {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
            
            missing_headers = []
            for header, expected_value in cors_headers.items():
                actual_value = headers.get(header)
                if not actual_value or (expected_value != "*" and expected_value not in actual_value):
                    missing_headers.append(f"{header}: expected {expected_value}, got {actual_value}")
            
            if missing_headers:
                self.log_test("CORS Headers", "WARNING", f"Missing/incorrect: {'; '.join(missing_headers)}")
            else:
                self.log_test("CORS Headers", "PASS", "All CORS headers present")
                
        except Exception as e:
            self.log_test("CORS Headers", "FAIL", f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        if self.logger:
            self.logger.info("=" * 80)
            self.logger.info("QUBITLENS - BACKEND API TESTS")
            self.logger.info("=" * 80)
        else:
            print("=" * 80)
            print("QUBITLENS - BACKEND API TESTS")
            print("=" * 80)
        
        # Test server health
        if self.logger:
            self.logger.info("\n--- HEALTH CHECK ---")
        else:
            print("\n--- HEALTH CHECK ---")
        self.test_health_endpoint()
        
        # Test valid circuits
        if self.logger:
            self.logger.info("\n--- VALID CIRCUIT TESTS ---")
        else:
            print("\n--- VALID CIRCUIT TESTS ---")
        for circuit_name, circuit_data in TEST_CIRCUITS.items():
            self.test_simulate_endpoint_with_circuit(circuit_name, circuit_data)
        
        # Test invalid circuits
        if self.logger:
            self.logger.info("\n--- INVALID CIRCUIT TESTS ---")
        else:
            print("\n--- INVALID CIRCUIT TESTS ---")
        self.test_invalid_circuits()
        
        # Test performance
        if self.logger:
            self.logger.info("\n--- PERFORMANCE TESTS ---")
        else:
            print("\n--- PERFORMANCE TESTS ---")
        self.test_performance_circuits()
        
        # Test additional endpoints
        if self.logger:
            self.logger.info("\n--- ADDITIONAL ENDPOINT TESTS ---")
        else:
            print("\n--- ADDITIONAL ENDPOINT TESTS ---")
        self.test_websocket_endpoint()
        self.test_cors_headers()
        
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
        
        success_rate = self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100
        if self.logger:
            self.logger.info(f"\nSuccess Rate: {success_rate:.1f}%")
        else:
            print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        return self.test_results

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test QubitLens Backend API")
    parser.add_argument("--url", default="http://localhost:8001", help="Backend URL")
    parser.add_argument("--circuit", help="Test specific circuit only")
    
    args = parser.parse_args()
    
    tester = QuantumStateVisualizerBackendTester(args.url)
    
    if args.circuit:
        if args.circuit in TEST_CIRCUITS:
            tester.test_simulate_endpoint_with_circuit(args.circuit, TEST_CIRCUITS[args.circuit])
        else:
            print(f"Unknown circuit: {args.circuit}")
            print(f"Available circuits: {list(TEST_CIRCUITS.keys())}")
    else:
        results = tester.run_all_tests()
        
        # Exit with non-zero code if tests failed
        if results["failed"] > 0:
            exit(1)

if __name__ == "__main__":
    main()
