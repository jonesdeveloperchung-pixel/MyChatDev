# 🧪 MyChatDev Test Plan

## 📋 Overview
Comprehensive testing strategy for MyChatDev covering unit, integration, and end-to-end tests for all modules.

## 🎯 Test Objectives
- Validate module functionality against design specs
- Confirm inter-module integration and data flow
- Ensure SQLite operations are reliable and error-tolerant
- Capture edge cases and failure modes
- Verify API endpoints and UI components work correctly

## 📊 Test Coverage Status

### ✅ Completed Tests
- **LLM Manager** (`tests/test_llm_manager.py`) - Unit tests for model availability, response generation
- **Database** (`tests/test_database.py`) - Database operations and schema
- **API Integration** (`tests/integration/test_api_database.py`) - FastAPI with database
- **MCP Components** (`tests/unit/test_mcp_sandbox.py`, etc.) - MCP sandbox functionality

### 🔄 In Progress Tests
- **Workflow Service** - Basic integration test exists (`test_system.py`)
- **CLI** (`tests/test_cli.py`) - Needs expansion for new commands

### ❌ Missing Critical Tests

#### Unit Tests Needed
- **Config Management** (`src/config/settings.py`, `src/config/llm_profiles.py`)
- **Graph Workflow** (`src/workflow/graph_workflow.py`) - Core workflow logic
- **API Endpoints** (`src/api.py`) - Individual endpoint validation
- **Utility Functions** (`src/utils/`) - Logging, prompts

#### Integration Tests Needed
- **Workflow Service** (`src/workflow_service.py`) - Complete workflow execution
- **CLI Commands** - Profile management, config operations
- **API + Workflow** - End-to-end API workflow execution

#### E2E Tests Needed
- **Full System** - CLI to deliverables generation
- **UI Integration** - Flutter app with FastAPI backend
- **Error Recovery** - System behavior under failure conditions

## 🧩 Module Test Coverage

### Core Workflow (`src/workflow/`)
| Component | Unit Tests | Integration Tests | Status |
|-----------|------------|-------------------|--------|
| `graph_workflow.py` | ❌ Missing | ❌ Missing | **HIGH PRIORITY** |
| `workflow_service.py` | ❌ Missing | ✅ Basic | **MEDIUM PRIORITY** |
| `quality_gate.py` | ✅ Done | ❌ Missing | **LOW PRIORITY** |
| `sandbox_*.py` | ✅ Done | ✅ Done | **COMPLETE** |

### Configuration (`src/config/`)
| Component | Unit Tests | Integration Tests | Status |
|-----------|------------|-------------------|--------|
| `settings.py` | ❌ Missing | ❌ Missing | **HIGH PRIORITY** |
| `llm_profiles.py` | ❌ Missing | ❌ Missing | **HIGH PRIORITY** |

### API Layer (`src/`)
| Component | Unit Tests | Integration Tests | Status |
|-----------|------------|-------------------|--------|
| `api.py` | ❌ Missing | ✅ Partial | **MEDIUM PRIORITY** |
| `cli.py` | ❌ Missing | ❌ Missing | **MEDIUM PRIORITY** |
| `database.py` | ✅ Done | ✅ Done | **COMPLETE** |

### Models (`src/models/`)
| Component | Unit Tests | Integration Tests | Status |
|-----------|------------|-------------------|--------|
| `llm_manager.py` | ✅ Done | ✅ Done | **COMPLETE** |

## 🔗 Integration Test Scenarios

### Scenario 1: Complete Workflow Execution
- **Modules:** `workflow_service.py` + `graph_workflow.py` + `database.py`
- **Test Steps:**
  1. Initialize workflow with valid config and profile
  2. Execute workflow with sample prompt
  3. Verify database records created/updated
  4. Validate deliverables generated
- **Expected Outcome:** Successful workflow completion with all deliverables
- **Status:** ✅ Basic version exists in `test_system.py`

### Scenario 2: API Workflow Management
- **Modules:** `api.py` + `workflow_service.py` + `database.py`
- **Test Steps:**
  1. Start workflow via `/workflow/start` endpoint
  2. Monitor status via `/workflow/status/{run_id}`
  3. Retrieve results via `/workflow/runs`
- **Expected Outcome:** API correctly manages workflow lifecycle
- **Status:** ❌ Missing

### Scenario 3: CLI Profile Management
- **Modules:** `cli.py` + `llm_profiles.py` + `settings.py`
- **Test Steps:**
  1. List profiles via `profile list`
  2. Add custom profile via `profile add`
  3. Delete profile via `profile delete`
- **Expected Outcome:** Profile operations work correctly
- **Status:** ❌ Missing

## 🗃️ Database Validation Tests

### SQLite Configuration ✅ COMPLETE
- [x] Schema initialized correctly
- [x] CRUD operations verified
- [x] Invalid query handling tested
- [x] Migration paths documented

## 🧼 Edge Cases & Error Handling

| Case ID | Description | Trigger | Expected Behavior | Status |
|---------|-------------|---------|-------------------|--------|
| EC001 | Missing Ollama server | Workflow start with no Ollama | Graceful error message | ❌ Missing |
| EC002 | Invalid LLM model | Profile with non-existent model | Clear error with model name | ❌ Missing |
| EC003 | Database connection failure | Corrupted/locked database | Fallback or clear error | ❌ Missing |
| EC004 | Workflow interruption | Process killed mid-execution | Partial state recovery | ❌ Missing |
| EC005 | Invalid user prompt | Empty or malformed input | Input validation error | ❌ Missing |

## 📈 Test Implementation Priority

### Phase 1: Critical Unit Tests (Week 1)
1. **Config Management Tests** - `test_config_settings.py`, `test_llm_profiles.py`
2. **Graph Workflow Tests** - `test_graph_workflow_complete.py`
3. **API Endpoint Tests** - `test_api_endpoints.py`

### Phase 2: Integration Tests (Week 2)
1. **Workflow Service Integration** - `test_workflow_service_integration.py`
2. **CLI Integration** - `test_cli_integration.py`
3. **API + Database Integration** - Expand existing tests

### Phase 3: E2E Tests (Week 3)
1. **Full System E2E** - `test_e2e_system.py`
2. **Error Recovery E2E** - `test_e2e_error_scenarios.py`
3. **Performance Tests** - `test_performance.py`

## 🛠️ Test Infrastructure

### Required Test Dependencies
```python
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-mock>=3.10.0
httpx>=0.24.0  # For API testing
```

### Test Configuration
- **Test Database:** `sqlite:///./test_data/test_db.sqlite`
- **Test Deliverables:** `test_deliverables/`
- **Mock Ollama:** Use `pytest-mock` for LLM interactions
- **Fixtures:** Shared fixtures in `tests/conftest.py`

## 📊 Success Criteria

### Unit Tests
- **Coverage:** >90% for all core modules
- **Performance:** All tests complete in <30 seconds
- **Reliability:** 100% pass rate on clean environment

### Integration Tests
- **Workflow:** Complete workflow execution in test environment
- **API:** All endpoints respond correctly with valid/invalid inputs
- **Database:** All CRUD operations work under concurrent access

### E2E Tests
- **System:** Full CLI workflow produces expected deliverables
- **UI:** Flutter app successfully communicates with API
- **Recovery:** System handles failures gracefully

## 📎 References
- [Design Specifications](./README.md)
- [Development Log](./DEVELOPMENT_LOG.md)
- [Database Schema](./src/database.py)
- [API Documentation](./src/api.py)