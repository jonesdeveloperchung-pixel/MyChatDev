from .file_ops_engine import FileOpsEngine
from .exec_engine import ExecEngine
from .audit_logger import AuditLogger

class InstructionRouter:
    """Routes and validates MCP instructions"""
    
    def __init__(self, file_ops: FileOpsEngine, exec_engine: ExecEngine, audit_logger: AuditLogger):
        self.file_ops = file_ops
        self.exec_engine = exec_engine
        self.audit_logger = audit_logger
    
    def route(self, instruction: dict) -> dict:
        """Route instruction to appropriate engine"""
        try:
            action = instruction.get("action")
            target = instruction.get("target")
            path = instruction.get("path", "")
            
            if not action or not target:
                return {"status": "error", "message": "Missing required fields: action, target"}
            
            result = None
            
            if action == "read" and target == "file":
                result = self.file_ops.read_file(path)
            elif action == "write" and target == "file":
                content = instruction.get("content", "")
                result = self.file_ops.write_file(path, content)
            elif action == "list" and target == "folder":
                result = self.file_ops.list_files(path)
            elif action == "execute" and target == "script":
                command = instruction.get("command", path.split('.')[-1] if '.' in path else "python")
                args = instruction.get("args", [path] if path else [])
                result = self.exec_engine.execute_command(command, args)
            else:
                result = {"status": "error", "message": f"Unsupported action-target: {action}-{target}"}
            
            # Log the operation
            self.audit_logger.log(
                actor="mcp_client",
                action=f"{action}_{target}",
                target=path,
                result=result,
                llm_intent=instruction.get("llm_intent")
            )
            
            return result
            
        except Exception as e:
            error_result = {"status": "error", "message": f"Router error: {str(e)}"}
            self.audit_logger.log("mcp_client", "error", "", error_result)
            return error_result