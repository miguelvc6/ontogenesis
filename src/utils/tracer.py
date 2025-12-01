import json
import time
import os
import uuid
from typing import Any, Dict, Optional, List
from datetime import datetime

class Tracer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Tracer, cls).__new__(cls)
            cls._instance.trace_file = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "traces.jsonl")
            # Ensure data directory exists
            os.makedirs(os.path.dirname(cls._instance.trace_file), exist_ok=True)
            cls._instance.current_trace_id = str(uuid.uuid4())
            cls._instance.span_stack: List[Dict[str, Any]] = []
        return cls._instance

    def start_trace(self, trace_id: Optional[str] = None):
        self.current_trace_id = trace_id or str(uuid.uuid4())
        self.span_stack = []
        self.log_event("trace_start", {"trace_id": self.current_trace_id})

    def start_span(self, name: str, inputs: Optional[Dict[str, Any]] = None) -> str:
        span_id = str(uuid.uuid4())
        span = {
            "span_id": span_id,
            "name": name,
            "start_time": time.time(),
            "inputs": inputs or {}
        }
        self.span_stack.append(span)
        self.log_event("span_start", {
            "trace_id": self.current_trace_id,
            "span_id": span_id,
            "parent_span_id": self.span_stack[-2]["span_id"] if len(self.span_stack) > 1 else None,
            "name": name,
            "inputs": inputs
        })
        return span_id

    def end_span(self, outputs: Optional[Any] = None, error: Optional[str] = None):
        if not self.span_stack:
            return
        
        span = self.span_stack.pop()
        duration = time.time() - span["start_time"]
        
        self.log_event("span_end", {
            "trace_id": self.current_trace_id,
            "span_id": span["span_id"],
            "name": span["name"],
            "duration_ms": duration * 1000,
            "outputs": outputs,
            "error": error
        })

    def log_event(self, event_type: str, data: Dict[str, Any]):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            **data
        }
        with open(self.trace_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

# Global accessor
tracer = Tracer()
