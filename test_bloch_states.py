#!/usr/bin/env python3
"""
Test script to verify Bloch sphere representations for common quantum states.
Run this and take screenshots to compare with frontend display.
"""

import requests
import json

# Backend URL
BASE_URL = "http://localhost:8000"

def test_quantum_state(name, qasm_code, expected_coords):
    """Test a quantum state and print results"""
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print(f"QASM Code:")
    print(qasm_code)
    print(f"Expected Bloch Coordinates: {expected_coords}")
    print('-' * 50)
    
    payload = {
        "qasm_code": qasm_code,
        "shots": 1024
    }
    
    try:
        response = requests.post(f"{BASE_URL}/simulate", json=payload)
        if response.status_code == 200:
            result = response.json()
            for qubit in result["qubits"]:
                coords = qubit["bloch_coords"]
                print(f"Qubit {qubit['id']} ({qubit['label']}):")
                print(f"  Actual Bloch Coords: [{coords[0]:.4f}, {coords[1]:.4f}, {coords[2]:.4f}]")
                print(f"  Expected:           {expected_coords}")
                print(f"  Purity: {qubit['purity']:.6f}")
                print(f"  Pipeline Used: {result['pipeline_used']}")
                
                # Check if close to expected
                tolerance = 1e-3
                matches = all(abs(coords[i] - expected_coords[i]) < tolerance for i in range(3))
                print(f"  ✅ Match Expected: {matches}")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Request Error: {e}")

def main():
    print("🔬 Quantum State Bloch Sphere Test Suite")
    print("This will test various quantum states and their Bloch representations")
    
    # Test 1: |0⟩ state (initial, no gates)
    test_quantum_state(
        name="|0⟩ Initial State",
        qasm_code="""OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];""",
        expected_coords=[0.0, 0.0, 1.0]  # Points up (+Z axis)
    )
    
    # Test 2: |+⟩ state (H gate applied to |0⟩)
    test_quantum_state(
        name="|+⟩ Superposition State (H gate)",
        qasm_code="""OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
h q[0];""",
        expected_coords=[1.0, 0.0, 0.0]  # Points along +X axis
    )
    
    # Test 3: |1⟩ state (X gate applied to |0⟩)
    test_quantum_state(
        name="|1⟩ Excited State (X gate)",
        qasm_code="""OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
x q[0];""",
        expected_coords=[0.0, 0.0, -1.0]  # Points down (-Z axis)
    )
    
    # Test 4: |i⟩ state (H then S gate)
    test_quantum_state(
        name="|i⟩ State (H + S gates)",
        qasm_code="""OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
h q[0];
s q[0];""",
        expected_coords=[0.0, 1.0, 0.0]  # Points along +Y axis
    )
    
    # Test 5: |-⟩ state (H then Z gate)  
    test_quantum_state(
        name="|-⟩ State (H + Z gates)",
        qasm_code="""OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
h q[0];
z q[0];""",
        expected_coords=[-1.0, 0.0, 0.0]  # Points along -X axis
    )
    
    # Test 6: Bell State (2 qubits)
    test_quantum_state(
        name="Bell State (2 qubits)",
        qasm_code="""OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0], q[1];""",
        expected_coords="Each qubit should be maximally mixed: [0, 0, 0]"
    )

    print(f"\n{'='*50}")
    print("🎯 Instructions for Frontend Testing:")
    print("1. Open your browser to http://localhost:8080")
    print("2. Copy each QASM code above into the editor")
    print("3. Click 'Run Simulation'")
    print("4. Check if the displayed Bloch coordinates match the expected values")
    print("5. Take screenshots of any discrepancies")
    print("6. Pay special attention to the H gate test - it should show [1.0000, 0.0000, 0.0000]")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
