from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from enum import Enum
from typing import Dict, Any, Optional
from pathlib import Path
import json # For loading/dumping state files
import requests # Added for Ollama health check
from starlette.responses import StreamingResponse # Added for SSE

# Import necessary components from other modules
from src.config.settings import DEFAULT_CONFIG, SystemConfig, LLMConfig, load_user_config, save_user_config, USER_CONFIG_FILE, normalize_ollama_url, USER_PROFILES_DIR
from src.config.llm_profiles import AVAILABLE_LLMS_BY_PROFILE, load_profile_from_file
from src.workflow_service import execute_workflow
from src.database import get_workflow_run, get_all_workflow_runs # Added for database interaction

# Import helper functions from cli, making sure to resolve relative imports (only _read_prompt_from_file and DEFAULT_USER_PROMPT remain)
from src.cli import DEFAULT_USER_PROMPT, _read_prompt_from_file # Kept these as they are more general helpers, might move later

app = FastAPI()

# Add CORS middleware to allow Flutter frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for LLM configuration within a profile
class LLMConfigModel(BaseModel):
    model_id: str = Field(..., description="The ID of the LLM model (e.g., 'ollama/llama3').")
    temperature: float = Field(LLMConfig.model_fields['temperature'].default, ge=0.0, le=2.0, description="The temperature for text generation.")
    max_tokens: int = Field(LLMConfig.model_fields['max_tokens'].default, ge=1, description="The maximum number of tokens to generate.")
    # Add other LLMConfig fields as needed

# Pydantic model for a workflow execution request
class WorkflowStartRequest(BaseModel):
    user_prompt: str = Field(..., min_length=1, description="The user's prompt for the workflow.")
    profile_name: Optional[str] = Field(None, description=f"Name of a built-in LLM profile. Available: {', '.join(AVAILABLE_LLMS_BY_PROFILE.keys())}")
    profile_file_content: Optional[str] = Field(None, description="Content of a custom YAML file defining LLM configurations for roles.")
    max_iterations: Optional[int] = Field(None, ge=1, description="Maximum number of workflow iterations.")
    quality_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum quality score required to halt the workflow.")
    change_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum change magnitude to detect stagnation.")
    enable_sandbox: Optional[bool] = Field(None, description="Enable or disable the sandboxed development environment.")
    enable_human_approval: Optional[bool] = Field(None, description="Enable or disable human approval step.")
    use_mcp_sandbox: Optional[bool] = Field(None, description="Enable the MCP sandbox for isolated execution.")
    mcp_server_host: Optional[str] = Field(None, description="Hostname or IP address of the MCP server.")
    mcp_server_port: Optional[int] = Field(None, description="Port number of the MCP server.")
    ollama_host: Optional[str] = Field(None, description="URL of the Ollama host.")
    log_level: Optional[str] = Field(None, pattern=r"^(?i)(debug|info|warning|error|critical)$", description="Set the logging verbosity level.")
    dry_run: bool = Field(False, description="Simulate the workflow without executing LLM calls or saving deliverables.")
    # Add other SystemConfig parameters here as they become available and needed in the API

# Enum for Agent Roles
class AgentRole(str, Enum):
    PRODUCT_MANAGER = "product_manager"
    ARCHITECT = "architect"
    TESTER = "tester"
    PROGRAMMER = "programmer"
    REVIEWER = "reviewer"
    QUALITY_GATE = "quality_gate"
    REFLECTOR = "reflector"
    DISTILLER = "distiller" # Corresponds to summarizer in prompts

# Define display names, descriptions, icons, and colors for each role
ROLE_DEFINITIONS = {
    AgentRole.PRODUCT_MANAGER: {
        "display_name": "Product Manager",
        "description": "Analyzes initial requirements and consults system memory.",
        "icon": "person_outline", # Placeholder for material icon name
        "color": "blue"
    },
    AgentRole.ARCHITECT: {
        "display_name": "System Architect",
        "description": "Creates the high-level technical design.",
        "icon": "layers_outlined",
        "color": "green"
    },
    AgentRole.TESTER: {
        "display_name": "Tester",
        "description": "Generates and executes tests within a sandboxed environment.",
        "icon": "bug_report_outlined",
        "color": "teal"
    },
    AgentRole.PROGRAMMER: {
        "display_name": "Programmer",
        "description": "Writes, compiles, and tests code in a sandboxed environment.",
        "icon": "code",
        "color": "purple"
    },
    AgentRole.REVIEWER: {
        "display_name": "Code Reviewer",
        "description": "Performs holistic review of validated code for logic, style, and maintainability.",
        "icon": "rate_review_outlined",
        "color": "red"
    },
    AgentRole.QUALITY_GATE: {
        "display_name": "Quality Gate",
        "description": "Performs a rubric-based quality assessment.",
        "icon": "check_circle_outline",
        "color": "orange"
    },
    AgentRole.REFLECTOR: {
        "display_name": "Reflector",
        "description": "Performs root-cause analysis and proposes strategic guidance.",
        "icon": "lightbulb_outline",
        "color": "yellow"
    },
    AgentRole.DISTILLER: {
        "display_name": "Distiller",
        "description": "Intelligently compresses content to preserve context.",
        "icon": "compress",
        "color": "grey"
    },
}

@app.get("/")
async def read_root():
    return {"message": "MyChatDev API is running!"}

@app.get("/roles")
async def get_roles():
    """Returns a list of all defined agent roles with their display names, descriptions, icons, and colors."""
    roles_data = []
    for role_enum, details in ROLE_DEFINITIONS.items():
        roles_data.append({
            "name": role_enum.value,
            "display_name": details["display_name"],
            "description": details["description"],
            "icon": details["icon"],
            "color": details["color"]
        })
    return roles_data

@app.get("/system/ollama_status")
async def check_ollama_status():
    """
    Checks if the Ollama service is running and reachable.
    Returns the status and version if available.
    """
    current_config = load_user_config()
    ollama_host = current_config.ollama_host
    
    # Ensure scheme if missing (though settings usually handles this)
    if not ollama_host.startswith("http"):
        ollama_host = f"http://{ollama_host}"
        
    try:
        # Ollama usually has a root endpoint that returns a generic message or /api/version
        response = requests.get(f"{ollama_host}/api/version", timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            return {"is_running": True, "version": data.get("version", "unknown"), "host": ollama_host}
        else:
             # Fallback check for root if version endpoint fails
            root_response = requests.get(f"{ollama_host}/", timeout=2.0)
            if root_response.status_code == 200:
                 return {"is_running": True, "version": "unknown", "host": ollama_host}
            return {"is_running": False, "error": f"HTTP {response.status_code}", "host": ollama_host}
    except requests.exceptions.RequestException as e:
        return {"is_running": False, "error": str(e), "host": ollama_host}

@app.post("/workflow/start", response_model=Dict[str, Any])
async def start_workflow(request: WorkflowStartRequest):
    """
    Triggers the MyChatDev cooperative LLM workflow.
    All CLI parameters can be configured via this endpoint.
    """
    # Determine user input
    user_input = request.user_prompt

    # Determine LLM configurations
    llm_configs: Dict[str, LLMConfig] = {}
    if request.profile_file_content:
        try:
            # Create a temporary file to load profile content
            temp_profile_path = Path("temp_profile.yaml")
            temp_profile_path.write_text(request.profile_file_content, encoding="utf-8")
            llm_configs = load_profile_from_file(temp_profile_path)
            temp_profile_path.unlink() # Clean up temp file
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error loading custom profile from content: {e}")
    elif request.profile_name:
        if request.profile_name not in AVAILABLE_LLMS_BY_PROFILE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown profile '{request.profile_name}'. Available profiles: {', '.join(AVAILABLE_LLMS_BY_PROFILE.keys())}")
        llm_configs = AVAILABLE_LLMS_BY_PROFILE[request.profile_name]
    else:
        # Default to a sensible profile if none specified
        llm_configs = AVAILABLE_LLMS_BY_PROFILE["High_Reasoning"] # Or another suitable default

    # Construct SystemConfig from request arguments and defaults
    try:
        ollama_host = normalize_ollama_url(request.ollama_host) if request.ollama_host else DEFAULT_CONFIG.ollama_host
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid Ollama host URL: {e}")

    system_config = SystemConfig(
        ollama_host=ollama_host,
        max_iterations=request.max_iterations if request.max_iterations is not None else DEFAULT_CONFIG.max_iterations,
        quality_threshold=request.quality_threshold if request.quality_threshold is not None else DEFAULT_CONFIG.quality_threshold,
        change_threshold=request.change_threshold if request.change_threshold is not None else DEFAULT_CONFIG.change_threshold,
        log_level=request.log_level.upper() if request.log_level else DEFAULT_CONFIG.log_level,
        enable_sandbox=request.enable_sandbox if request.enable_sandbox is not None else DEFAULT_CONFIG.enable_sandbox,
        enable_human_approval=request.enable_human_approval if request.enable_human_approval is not None else DEFAULT_CONFIG.enable_human_approval,
        use_mcp_sandbox=request.use_mcp_sandbox if request.use_mcp_sandbox is not None else DEFAULT_CONFIG.use_mcp_sandbox,
        mcp_server_host=request.mcp_server_host if request.mcp_server_host is not None else DEFAULT_CONFIG.mcp_server_host,
        mcp_server_port=request.mcp_server_port if request.mcp_server_port is not None else DEFAULT_CONFIG.mcp_server_port,
        # Ensure all SystemConfig fields are covered. If a field is not in request, it defaults to DEFAULT_CONFIG.
    )

    # Execute the workflow
    try:
        final_state = None
        async for event in execute_workflow(
            user_input=user_input,
            system_config=system_config,
            llm_configs=llm_configs,
            dry_run=request.dry_run
        ):
            if event.get('event_type') == 'workflow_end':
                final_state = event
                break
        
        if final_state:
            return final_state
        else:
            return {"message": "Workflow completed", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Workflow execution failed: {e}")

class WorkflowStopRequest(BaseModel):
    run_id: str = Field(..., description="The ID of the workflow run to stop.")

@app.post("/workflow/stop", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def stop_workflow(request: WorkflowStopRequest):
    """
    Placeholder endpoint to stop an active workflow.
    Stopping a running workflow is not supported in the current MVP phase.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Stopping an active workflow is not yet supported. This feature will be implemented in a later phase."
    )

# Base directory for deliverables
DELIVERABLES_BASE_DIR = Path("deliverables")

@app.get("/workflow/status/{run_id}", response_model=Dict[str, Any])
async def get_workflow_status(run_id: str):
    """
    Retrieves the status of a workflow run from the database.
    """
    # Load current system config to get database URL
    current_config = load_user_config()

    workflow_run = get_workflow_run(run_id, current_config.database_url)

    if not workflow_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow run '{run_id}' not found in database.")
    
    # The database stores config_used as a JSON string, so we need to parse it back to a dict
    if workflow_run.get('config_used'):
        workflow_run['config_used'] = json.loads(workflow_run['config_used'])

    return workflow_run

class DeliverableItem(BaseModel):
    name: str
    type: str
    size_bytes: int
    download_url: str

@app.get("/workflow/deliverables/{run_id}", response_model=Dict[str, Any])
async def get_workflow_deliverables(run_id: str):
    """
    Lists all deliverables for a specific workflow run.
    """
    workflow_dir = DELIVERABLES_BASE_DIR / run_id

    if not workflow_dir.is_dir():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow run '{run_id}' not found.")
    
    deliverables_list = []
    for item in workflow_dir.iterdir():
        if item.is_file():
            deliverables_list.append(DeliverableItem(
                name=item.name,
                type=item.suffix.lstrip('.'),
                size_bytes=item.stat().st_size,
                download_url=f"/workflow/deliverables/{run_id}/{item.name}"
            ))
    return {"run_id": run_id, "deliverables": deliverables_list}

@app.get("/workflow/deliverables/{run_id}/{file_name}")
async def download_deliverable(run_id: str, file_name: str):
    """
    Downloads a specific deliverable file from a workflow run.
    """
    workflow_dir = DELIVERABLES_BASE_DIR / run_id
    file_path = workflow_dir / file_name

    if not workflow_dir.is_dir():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow run '{run_id}' not found.")

    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Deliverable file '{file_name}' not found in run '{run_id}'.")
    
    # Security check: Ensure the file being accessed is within the deliverables directory
    # and not some arbitrary path. Path.resolve() helps here.
    if not file_path.resolve().is_relative_to(workflow_dir.resolve()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path.")

    from starlette.responses import FileResponse
    return FileResponse(file_path, filename=file_name)


class WorkflowRunSummary(BaseModel):
    id: int
    run_id: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    user_prompt: Optional[str] = None
    config_used: Optional[str] = None
    review_feedback: Optional[str] = None
    deliverables_path: Optional[str] = None


@app.get("/workflow/runs", response_model=Dict[str, Any])
async def get_workflow_runs():
    """
    Lists all available workflow runs with summary information from the database.
    """
    current_config = load_user_config()
    all_runs = get_all_workflow_runs(current_config.database_url)
    
    # Convert sqlite3.Row objects to dicts and then to Pydantic models
    runs_list = []
    for run in all_runs:
        run_dict = dict(run) # Convert sqlite3.Row to dict
        runs_list.append(WorkflowRunSummary(
            id=run_dict['id'],
            run_id=run_dict['run_id'],
            status=run_dict['status'],
            start_time=run_dict['start_time'],
            end_time=run_dict['end_time'],
            user_prompt=run_dict['user_prompt'],
            config_used=run_dict['config_used'],
            review_feedback=run_dict['review_feedback'],
            deliverables_path=run_dict['deliverables_path']
        ))
    
    return {"runs": runs_list}

# --- Profile Management Endpoints ---

class ProfileLLMConfig(BaseModel):
    model_id: str
    temperature: float
    max_tokens: int

class ProfileDetailResponse(BaseModel):
    name: str
    role: str
    config: ProfileLLMConfig

class AllProfilesResponse(BaseModel):
    name: str
    source: str # e.g., "Built-in", "User-defined"
    roles: Dict[str, ProfileLLMConfig]

class ProfileCreateRequest(BaseModel):
    profile_name: str = Field(..., description="Name for the new custom profile.")
    profile_file_content: str = Field(..., description="YAML content of the LLM profile.")

@app.get("/profiles", response_model=Dict[str, Any])
async def list_profiles():
    """
    Lists all available LLM profiles (built-in and user-defined).
    """
    all_profiles_raw = {}
    
    # Load built-in profiles
    for name, config_dict in AVAILABLE_LLMS_BY_PROFILE.items():
        all_profiles_raw[name] = config_dict

    # Load user-defined profiles
    for profile_file in USER_PROFILES_DIR.glob("*.yaml"):
        try:
            profile_name = profile_file.stem
            all_profiles_raw[profile_name] = load_profile_from_file(profile_file)
        except Exception as e:
            # Log a warning but don't prevent other profiles from loading
            print(f"Warning: Could not load user profile '{profile_file.name}': {e}", file=sys.stderr)

    response_data = []
    for profile_name, role_configs in all_profiles_raw.items():
        source = "Built-in" if profile_name in AVAILABLE_LLMS_BY_PROFILE else "User-defined"
        roles_data = {}
        for role, llm_config in role_configs.items():
            roles_data[role] = ProfileLLMConfig(
                model_id=llm_config.model_id,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens
            )
        response_data.append(AllProfilesResponse(name=profile_name, source=source, roles=roles_data))
    return {"profiles": response_data}

@app.get("/profiles/{profile_name}", response_model=Dict[str, Any])
async def get_profile_details(profile_name: str):
    """
    Retrieves details for a specific LLM profile.
    """
    all_profiles_raw = {}

    # Load built-in profiles
    for name, config_dict in AVAILABLE_LLMS_BY_PROFILE.items():
        all_profiles_raw[name] = config_dict

    # Load user-defined profiles
    for profile_file in USER_PROFILES_DIR.glob("*.yaml"):
        try:
            user_profile_name = profile_file.stem
            all_profiles_raw[user_profile_name] = load_profile_from_file(profile_file)
        except Exception as e:
            print(f"Warning: Could not load user profile '{profile_file.name}': {e}", file=sys.stderr)


    if profile_name not in all_profiles_raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Profile '{profile_name}' not found.")
    
    roles_data = {}
    for role, llm_config in all_profiles_raw[profile_name].items():
        roles_data[role] = ProfileLLMConfig(
            model_id=llm_config.model_id,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens
        )
    source = "Built-in" if profile_name in AVAILABLE_LLMS_BY_PROFILE else "User-defined"
    return {"profile": AllProfilesResponse(name=profile_name, source=source, roles=roles_data)}

@app.post("/profiles", status_code=status.HTTP_201_CREATED)
async def add_profile(request: ProfileCreateRequest):
    """
    Adds a new custom LLM profile from YAML content.
    """
    profile_name = request.profile_name
    
    # Check if profile name already exists
    all_profiles_raw = {}
    for name, config_dict in AVAILABLE_LLMS_BY_PROFILE.items():
        all_profiles_raw[name] = config_dict
    for profile_file in USER_PROFILES_DIR.glob("*.yaml"):
        try:
            user_profile_name = profile_file.stem
            all_profiles_raw[user_profile_name] = load_profile_from_file(profile_file)
        except Exception:
            pass # Ignore errors for existing profiles

    if profile_name in all_profiles_raw:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Profile '{profile_name}' already exists.")

    temp_profile_path = Path(f"{profile_name}_temp_profile.yaml") # Use a unique temp name

    try:
        temp_profile_path.write_text(request.profile_file_content, encoding="utf-8")
        # _save_user_profile is a helper in src/cli, which needs to be moved or reimplemented here.
        # For now, directly save to USER_PROFILES_DIR
        target_path = USER_PROFILES_DIR / f"{profile_name}.yaml"
        # Validate the content before saving
        load_profile_from_file(temp_profile_path)
        target_path.write_bytes(temp_profile_path.read_bytes())

        return {"message": f"Profile '{profile_name}' added successfully."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error adding profile '{profile_name}': {e}")
    finally:
        if temp_profile_path.exists():
            temp_profile_path.unlink() # Clean up temp file

@app.delete("/profiles/{profile_name}")
async def delete_profile(profile_name: str):
    """
    Deletes a user-defined LLM profile. Built-in profiles cannot be deleted.
    """
    if profile_name in AVAILABLE_LLMS_BY_PROFILE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Built-in profile '{profile_name}' cannot be deleted.")
    
    try:
        # Check if the profile actually exists as a user-defined profile
        profile_file = USER_PROFILES_DIR / f"{profile_name}.yaml"
        if not profile_file.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User-defined profile '{profile_name}' not found.")
            
        profile_file.unlink() # Directly delete the file
        return {"message": f"Profile '{profile_name}' deleted successfully."}
    except HTTPException as e:
        raise e # Re-raise HTTPExceptions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting profile '{profile_name}': {e}")


# --- Config Management Endpoints ---

class SystemConfigUpdate(BaseModel):
    # Dynamically create Optional fields from SystemConfig
    ollama_host: Optional[str] = None
    max_iterations: Optional[int] = None
    quality_threshold: Optional[float] = None
    change_threshold: Optional[float] = None
    log_level: Optional[str] = Field(None, pattern=r"^(?i)(debug|info|warning|error|critical)$")
    enable_sandbox: Optional[bool] = None
    enable_human_approval: Optional[bool] = None
    use_mcp_sandbox: Optional[bool] = None
    mcp_server_host: Optional[str] = None
    mcp_server_port: Optional[int] = None
    # Add other SystemConfig fields here as needed

@app.get("/config", response_model=SystemConfig)
async def get_config():
    """
    Retrieves the current effective system configuration.
    """
    return load_user_config()

@app.post("/config", response_model=SystemConfig)
async def update_config(request: SystemConfigUpdate):
    """
    Updates system-wide configuration parameters.
    """
    current_config = load_user_config()
    updated = False

    for field, value in request.model_dump(exclude_unset=True).items():
        if value is not None:
            if field == "ollama_host":
                try:
                    value = normalize_ollama_url(value)
                except ValueError as e:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid Ollama host URL: {e}")
            
            setattr(current_config, field, value)
            updated = True
    
    if updated:
        save_user_config(current_config)
    
    return current_config

@app.post("/config/reset", status_code=status.HTTP_200_OK)
async def reset_config():
    """
    Resets user configuration to default settings.
    """
    if USER_CONFIG_FILE.is_file():
        try:
            USER_CONFIG_FILE.unlink() 
            return {"message": "User configuration reset to default settings."}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error resetting configuration: {e}")
    else:
        return {"message": "No user configuration found to reset. Already using default settings."}

# --- Workflow Streaming Endpoint ---
from starlette.responses import StreamingResponse

class StreamWorkflowQueryParams(BaseModel):
    user_prompt: str = Field(..., min_length=1, description="The user's prompt for the workflow.")
    profile_name: Optional[str] = Field(None, description=f"Name of a built-in LLM profile. Available: {', '.join(AVAILABLE_LLMS_BY_PROFILE.keys())}")
    # profile_file_content is not suitable for GET request query parameters, only POST body
    max_iterations: Optional[int] = Field(None, ge=1, description="Maximum number of workflow iterations.")
    quality_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum quality score required to halt the workflow.")
    change_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum change magnitude to detect stagnation.")
    enable_sandbox: Optional[bool] = Field(None, description="Enable or disable the sandboxed development environment.")
    enable_human_approval: Optional[bool] = Field(None, description="Enable or disable human approval step.")
    use_mcp_sandbox: Optional[bool] = Field(None, description="Enable the MCP sandbox for isolated execution.")
    mcp_server_host: Optional[str] = Field(None, description="Hostname or IP address of the MCP server.")
    mcp_server_port: Optional[int] = Field(None, description="Port number of the MCP server.")
    ollama_host: Optional[str] = Field(None, description="URL of the Ollama host.")
    log_level: Optional[str] = Field(None, pattern=r"^(?i)(debug|info|warning|error|critical)$")
    dry_run: bool = Field(False, description="Simulate the workflow without executing LLM calls or saving deliverables.")
    # Add other SystemConfig parameters here as they become available and needed in the API

@app.get("/workflow/stream")
async def stream_workflow(
    run_id: Optional[str] = None,
    user_prompt: Optional[str] = None,
    profile_name: Optional[str] = None,
    max_iterations: Optional[int] = None,
    quality_threshold: Optional[float] = None,
    change_threshold: Optional[float] = None,
    enable_sandbox: Optional[bool] = None,
    enable_human_approval: Optional[bool] = None,
    use_mcp_sandbox: Optional[bool] = None,
    mcp_server_host: Optional[str] = None,
    mcp_server_port: Optional[int] = None,
    ollama_host: Optional[str] = None,
    log_level: Optional[str] = None,
    dry_run: bool = False
):
    """
    Streams workflow execution events in real-time using Server-Sent Events (SSE).
    If run_id is provided, streams events for that specific workflow.
    Otherwise, starts a new workflow with the provided parameters.
    """
    async def event_generator():
        if run_id:
            # Stream events for existing workflow (placeholder - would need workflow tracking)
            yield f"data: {{\"event_type\": \"info\", \"message\": \"Streaming for run_id: {run_id}\"}}\n\n"
            return
        
        if not user_prompt:
            yield f"data: {{\"event_type\": \"error\", \"message\": \"user_prompt is required when run_id is not provided\"}}\n\n"
            return
            
        llm_configs: Dict[str, LLMConfig] = {}
        if profile_name:
            if profile_name not in AVAILABLE_LLMS_BY_PROFILE:
                yield f"data: {{\"event_type\": \"error\", \"message\": \"Unknown profile '{profile_name}'\"}}\n\n"
                return
            llm_configs = AVAILABLE_LLMS_BY_PROFILE[profile_name]
        else:
            llm_configs = AVAILABLE_LLMS_BY_PROFILE["High_Reasoning"] # Default

        try:
            ollama_host_resolved = normalize_ollama_url(ollama_host) if ollama_host else DEFAULT_CONFIG.ollama_host
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid Ollama host URL: {e}")

        system_config = SystemConfig(
            ollama_host=ollama_host_resolved,
            max_iterations=max_iterations if max_iterations is not None else DEFAULT_CONFIG.max_iterations,
            quality_threshold=quality_threshold if quality_threshold is not None else DEFAULT_CONFIG.quality_threshold,
            change_threshold=change_threshold if change_threshold is not None else DEFAULT_CONFIG.change_threshold,
            log_level=log_level.upper() if log_level else DEFAULT_CONFIG.log_level,
            enable_sandbox=enable_sandbox if enable_sandbox is not None else DEFAULT_CONFIG.enable_sandbox,
            enable_human_approval=enable_human_approval if enable_human_approval is not None else DEFAULT_CONFIG.enable_human_approval,
            use_mcp_sandbox=use_mcp_sandbox if use_mcp_sandbox is not None else DEFAULT_CONFIG.use_mcp_sandbox,
            mcp_server_host=mcp_server_host if mcp_server_host is not None else DEFAULT_CONFIG.mcp_server_host,
            mcp_server_port=mcp_server_port if mcp_server_port is not None else DEFAULT_CONFIG.mcp_server_port,
        )

        try:
            async for event in execute_workflow(
                user_prompt=user_prompt,
                system_config=system_config,
                llm_configs=llm_configs,
                dry_run=dry_run
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except HTTPException as e:
            yield f"data: {json.dumps({'event_type': 'error', 'detail': e.detail, 'status_code': e.status_code})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event_type': 'error', 'detail': str(e), 'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")