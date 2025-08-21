#!/usr/bin/env bash
# Demo script to show the logging functionality

echo "============================================="
echo "QUANTUM STATE VISUALIZER - LOGGING DEMO"
echo "============================================="

cd "$(dirname "$0")"

echo "1. Testing logging system..."
python3 test_logging.py

echo -e "\n2. Showing log files created..."
ls -la logs/

echo -e "\n3. Displaying latest log content..."
LATEST_LOG=$(ls -t logs/test_run_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "Content of $LATEST_LOG:"
    echo "------------------------"
    cat "$LATEST_LOG"
else
    echo "No log files found"
fi

echo -e "\n4. Test runner help (showing --verbose option)..."
python3 run_tests.py --help | grep -A5 -B5 verbose

echo -e "\n============================================="
echo "DEMO COMPLETED"
echo "Ready to run: python3 run_tests.py --verbose"
echo "Log files will be automatically created in logs/"
echo "============================================="
