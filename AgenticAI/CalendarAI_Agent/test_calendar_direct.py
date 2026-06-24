#!/usr/bin/env python3
"""Direct test of calendar event creation without agent."""

import sys
import os
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current dir to path
sys.path.insert(0, os.path.dirname(__file__))

# Load env
from dotenv import load_dotenv
load_dotenv()

# Import tool
try:
    from tools.calendar import create_calendar_event
    logger.info("✓ create_calendar_event imported successfully")
except Exception as e:
    logger.error(f"✗ Failed to import create_calendar_event: {e}", exc_info=True)
    sys.exit(1)

# Test 1: Create event with end_time
print("\n" + "="*80)
print("TEST 1: Create event with explicit end time")
print("="*80)
try:
    result = create_calendar_event.func(
        title="Dentista - Test",
        start_time="2026-07-25 15:30",
        end_time="2026-07-25 16:30"
    )
    print(f"Result: {result}")
    if "htmlLink" in result or "Link:" in result:
        print("✓ SUCCESS: Event appears to be created (htmlLink found)")
    else:
        print("⚠ WARNING: No htmlLink in result - may indicate failure")
except Exception as e:
    logger.error(f"✗ Test 1 failed: {type(e).__name__}: {e}", exc_info=True)

# Test 2: Create event without end_time
print("\n" + "="*80)
print("TEST 2: Create event without end time (should default to +1hr)")
print("="*80)
try:
    result = create_calendar_event.func(
        title="Smart working - Test",
        start_time="2026-05-20 10:00"
    )
    print(f"Result: {result}")
    if "htmlLink" in result or "Link:" in result:
        print("✓ SUCCESS: Event appears to be created (htmlLink found)")
    else:
        print("⚠ WARNING: No htmlLink in result - may indicate failure")
except Exception as e:
    logger.error(f"✗ Test 2 failed: {type(e).__name__}: {e}", exc_info=True)

print("\n" + "="*80)
print("Tests completed")
print("="*80)
