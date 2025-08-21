#!/usr/bin/env python3
"""
Simple test to demonstrate the logging functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run_tests import setup_logging
from pathlib import Path

def test_logging():
    """Test the logging setup"""
    workspace_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logger, log_filepath = setup_logging(workspace_root)
    
    logger.info("Testing logging system...")
    logger.debug("This is a debug message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print(f"Log file created at: {log_filepath}")
    
    # Test log section
    from run_tests import log_section
    log_section(logger, "TEST SECTION")
    logger.info("Section content goes here")
    
    print("Logging test completed!")

if __name__ == "__main__":
    test_logging()
