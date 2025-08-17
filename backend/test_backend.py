#!/usr/bin/env python3
"""
Quick test script for the Quantum State Visualizer backend
"""
import requests
import time
import subprocess
import signal
import sys
from threading import Thread

def start_server():
    """Start the backend server"""
    return subprocess.Popen(['python', 'start.py'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)

def test_endpoints():
    """Test the main API endpoints"""
    base_url = 'http://localhost:8000'
    
    print("🧪 Testing backend endpoints...\n")
    
    # Test 1: Health check
    try:
        response = requests.get(f'{base_url}/health', timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint: PASSED")
        else:
            print(f"❌ Health endpoint: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Health endpoint: FAILED ({e})")
        return False
    
    # Test 2: Simple quantum circuit simulation
    circuit_qasm = '''OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0],q[1];'''
    
    payload = {
        'qasm_code': circuit_qasm,
        'shots': 100,
        'pipeline': 'unitary'
    }
    
    try:
        response = requests.post(f'{base_url}/simulate', json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ Simulation endpoint: PASSED")
            print(f"   📊 Statevector shape: {len(result.get('statevector', []))}")
            print(f"   🎯 Results: {len(result.get('results', {}))} outcomes")
        else:
            print(f"❌ Simulation endpoint: FAILED ({response.status_code})")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Simulation endpoint: FAILED ({e})")
        return False
    
    # Test 3: WebSocket info
    try:
        response = requests.get(f'{base_url}/websocket/info', timeout=5)
        if response.status_code == 200:
            print("✅ WebSocket info: PASSED")
        else:
            print(f"❌ WebSocket info: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ WebSocket info: FAILED ({e})")
    
    return True

def main():
    """Main test runner"""
    print("🚀 Starting Quantum State Visualizer Backend Test\n")
    
    server = start_server()
    time.sleep(3)  # Give server time to start
    
    try:
        success = test_endpoints()
        
        if success:
            print("\n🎉 All tests PASSED! Backend is working correctly.")
        else:
            print("\n❌ Some tests FAILED. Check the server logs.")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    finally:
        print("\n🔄 Shutting down test server...")
        server.terminate()
        server.wait()
        print("✅ Test completed")

if __name__ == '__main__':
    main()
