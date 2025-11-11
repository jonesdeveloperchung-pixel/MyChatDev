from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional, List
import uvicorn

from mcp_server.context_manager import ContextManager
from mcp_server.file_ops_engine import FileOpsEngine
from mcp_server.exec_engine import ExecEngine
from mcp_server.audit_logger import AuditLogger
from mcp_server.instruction_router import InstructionRouter

class MCPInstruction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: str
    target: str
    path: str = ""
    args: Optional[List[str]] = None
    content: Optional[str] = None
    command: Optional[str] = None
    llm_intent: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    
class MCPServer:
    """FastAPI-based MCP server"""
    
    def __init__(self, config):
        self.app = FastAPI(title="MCP Server", version="1.0.0")
        self.config = config
        
        # Initialize components
        self.context_manager = ContextManager(config.sandbox_dir)
        self.file_ops = FileOpsEngine(self.context_manager)
        self.exec_engine = ExecEngine(self.context_manager, config.command_whitelist)
        self.audit_logger = AuditLogger(config.audit_log_path)
        self.router = InstructionRouter(self.file_ops, self.exec_engine, self.audit_logger)
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.post("/mcp")
        async def process_instruction(instruction: MCPInstruction):
            try:
                result = self.router.route(instruction.model_dump())
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "context": self.context_manager.get_context()}
    
    def run(self, host: str = "127.0.0.1", port: int = 8000):
        uvicorn.run(self.app, host=host, port=port)

if __name__ == "__main__":
    import argparse
    from src.config.settings import SystemConfig # Assuming SystemConfig is needed

    parser = argparse.ArgumentParser(description="MCP Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address for the server")
    parser.add_argument("--port", type=int, default=8000, help="Port for the server")
    args = parser.parse_args()

    config = SystemConfig() # Instantiate with default values
    server = MCPServer(config)
    server.run(host=args.host, port=args.port)