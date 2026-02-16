import logging
import json
import os
from datetime import datetime

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

class StructuredLogger:
    def __init__(self, name="ai_router"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # File handler (JSON lines for machine readability)
        file_handler = logging.FileHandler("logs/app.jsonl")
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Console handler (for development visibility)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)

    def log_request(self, query: str, route: str, latency_ms: float, metadata: dict = None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "query_processed",
            "query_length": len(query),
            "route": route,
            "latency_ms": round(latency_ms, 2),
            "metadata": metadata or {}
        }
        self.logger.info(json.dumps(log_entry))

    def log_error(self, error_msg: str, context: dict = None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "error",
            "message": error_msg,
            "context": context or {}
        }
        self.logger.error(json.dumps(log_entry))

logger = StructuredLogger()
