"""
Simple test to validate backend structure and imports.
This will help identify any structural issues before installing dependencies.
"""

import sys
import os

def test_imports():
    """Test if all backend modules can be imported structurally"""
    
    # Add backend to path
    backend_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, backend_path)
    
    try:
        # Test basic imports (will fail without qiskit, but structure should be OK)
        print("Testing module structure...")
        
        # Test schema imports
        try:
            from schemas import SimulationRequest, SimulationResponse
            print("✅ Schemas import successfully")
        except ImportError as e:
            if "qiskit" in str(e) or "pydantic" in str(e):
                print("⚠️  Schemas structure OK (missing dependencies)")
            else:
                print(f"❌ Schema structure error: {e}")
        
        # Test pipeline base
        try:
            from pipelines.base import SimulationPipeline
            print("✅ Pipeline base imports successfully")
        except ImportError as e:
            print(f"❌ Pipeline base error: {e}")
        
        # Test utils structure
        try:
            import utils
            print("✅ Utils module structure OK")
        except ImportError as e:
            if "qiskit" in str(e):
                print("⚠️  Utils structure OK (missing qiskit)")
            else:
                print(f"❌ Utils structure error: {e}")
        
        # Test pipeline imports
        pipeline_modules = ['unitary', 'exact_density', 'trajectory']
        for module in pipeline_modules:
            try:
                exec(f"from pipelines.{module} import *")
                print(f"✅ Pipeline {module} structure OK")
            except ImportError as e:
                if "qiskit" in str(e):
                    print(f"⚠️  Pipeline {module} structure OK (missing qiskit)")
                else:
                    print(f"❌ Pipeline {module} structure error: {e}")
        
        # Test main app structure
        try:
            from main import app
            print("✅ FastAPI app structure OK")
        except ImportError as e:
            if "fastapi" in str(e) or "qiskit" in str(e):
                print("⚠️  FastAPI app structure OK (missing dependencies)")
            else:
                print(f"❌ FastAPI app structure error: {e}")
        
        print("\n📋 Structure validation complete!")
        print("💡 Install dependencies with: pip install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def check_file_structure():
    """Check if all required files exist"""
    
    backend_path = os.path.dirname(os.path.abspath(__file__))
    
    required_files = [
        'main.py',
        'schemas.py', 
        'utils.py',
        'requirements.txt',
        'Dockerfile',
        'README.md',
        '__init__.py',
        'pipelines/__init__.py',
        'pipelines/base.py',
        'pipelines/unitary.py',
        'pipelines/exact_density.py',
        'pipelines/trajectory.py'
    ]
    
    print("Checking file structure...")
    all_present = True
    
    for file in required_files:
        file_path = os.path.join(backend_path, file)
        if os.path.exists(file_path):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            all_present = False
    
    if all_present:
        print("\n✅ All required files present!")
    else:
        print("\n❌ Some files are missing!")
    
    return all_present

if __name__ == "__main__":
    print("🔍 Quantum State Visualizer Backend - Structure Validation")
    print("=" * 60)
    
    # Check files first
    files_ok = check_file_structure()
    
    print("\n" + "=" * 60)
    
    # Test imports if files are present
    if files_ok:
        test_imports()
    else:
        print("⚠️  Skipping import tests due to missing files")
