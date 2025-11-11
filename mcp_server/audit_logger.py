import json
import datetime
from pathlib import Path

class AuditLogger:
    """Logs all MCP operations for security and compliance"""
    
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, actor: str, action: str, target: str, result: dict, llm_intent: str = None):
        """Log an action with timestamp and details"""
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "actor": actor,
            "action": action,
            "target": target,
            "result": result,
            "llm_intent": llm_intent
        }
        
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            # Log to stderr if file logging fails
            print(f"Audit logging failed: {e}", file=__import__('sys').stderr)