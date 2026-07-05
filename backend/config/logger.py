import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Create a logs directory if it doesn't exist
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def setup_logger():
    # Create a master logger for FinAudit
    logger = logging.getLogger("FinAudit")
    
    # Set the lowest level of logs we want to capture
    logger.setLevel(logging.INFO)

    # Prevent logs from duplicating if this is called multiple times
    if logger.handlers:
        return logger

    # Define the exact format of the log messages
    # Example output: 2026-05-08 22:15:41 - [app.py] - INFO - User requested EMI calculation
    formatter = logging.Formatter(
        fmt="%(asctime)s - [%(filename)s] - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Setup Terminal Output (Console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Setup File Output (Saves to logs/finaudit.log)
    # RotatingFileHandler keeps the file from getting too big (max 5MB per file, keeps 3 backups)
    file_handler = RotatingFileHandler(
        filename=os.path.join(LOG_DIR, "finaudit.log"),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Attach handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Instantiate it so we can import it directly everywhere
logger = setup_logger()