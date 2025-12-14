"""
Logging Configuration Module
=============================
Configures logging for the entire application with colored console output
and detailed formatting.
"""

import logging
import sys
from datetime import datetime

# Create logger
logger = logging.getLogger("hospital_bulk_api")
logger.setLevel(logging.INFO)

# Create console handler with formatting
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create detailed formatter
formatter = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(console_handler)

# Prevent duplicate logs
logger.propagate = False
