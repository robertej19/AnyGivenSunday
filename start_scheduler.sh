#!/bin/bash

# Start the scheduler service
echo "Starting DraftKings standings scheduler..."
echo "This will run every 60 seconds. Press Ctrl+C to stop."
echo "Logs will be saved to scheduler.log"
echo ""

python3 scheduler.py
