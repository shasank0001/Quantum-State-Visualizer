#!/usr/bin/env python3
"""
Environment setup script for QubitLens Backend
"""

import subprocess
import sys
import os

def create_virtual_environment():
    """Create a Python virtual environment"""
    print("🔧 Setting up Python virtual environment...")
    
    try:
        # Create virtual environment
        subprocess.check_call([sys.executable, '-m', 'venv', 'venv'])
        print("✅ Virtual environment created successfully!")
        
        # Get activation commands for different shells
        if os.name == 'nt':  # Windows
            activate_script = "venv\\Scripts\\activate.bat"
            pip_path = "venv\\Scripts\\pip"
        else:  # Unix/Linux/macOS
            activate_script = "source venv/bin/activate"
            pip_path = "venv/bin/pip"
        
        print(f"💡 To activate the virtual environment, run:")
        print(f"   {activate_script}")
        
        return pip_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return None

def install_dependencies(pip_path=None):
    """Install project dependencies"""
    print("📦 Installing project dependencies...")
    
    pip_cmd = pip_path if pip_path else "pip"
    
    try:
        # Upgrade pip first
        subprocess.check_call([pip_cmd, 'install', '--upgrade', 'pip'])
        
        # Install requirements
        subprocess.check_call([pip_cmd, 'install', '-r', 'requirements.txt'])
        
        print("✅ Dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def verify_installation():
    """Verify that key packages are installed"""
    print("🔍 Verifying installation...")
    
    required_packages = {
        'fastapi': 'FastAPI web framework',
        'uvicorn': 'ASGI server',
        'qiskit': 'Quantum computing framework',
        'numpy': 'Numerical computing',
        'pydantic': 'Data validation'
    }
    
    all_good = True
    
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            all_good = False
    
    return all_good

def display_next_steps():
    """Display next steps for the user"""
    print("\n" + "="*60)
    print("🚀 Setup Complete!")
    print("="*60)
    print("Next steps:")
    print("1. Activate virtual environment (if created)")
    print("2. Start the backend server:")
    print("   python start.py")
    print("   OR")
    print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print("3. Access API documentation at: http://localhost:8000/docs")
    print("4. Test health endpoint at: http://localhost:8000/health")
    print("="*60)

def main():
    """Main setup function"""
    print("🔧 QubitLens Backend - Environment Setup")
    print("="*60)
    
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    print(f"📁 Working directory: {backend_dir}")
    
    # Ask user about virtual environment
    create_venv = input("Create virtual environment? (recommended) [Y/n]: ").lower().strip()
    
    pip_path = None
    if create_venv != 'n':
        pip_path = create_virtual_environment()
        if not pip_path:
            print("⚠️  Continuing with system Python...")
    
    # Install dependencies
    if install_dependencies(pip_path):
        # Verify installation
        if verify_installation():
            display_next_steps()
        else:
            print("⚠️  Some packages failed to install. Please check the output above.")
    else:
        print("❌ Setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
