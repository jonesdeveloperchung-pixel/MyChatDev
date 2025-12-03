# DEVELOPMENT_LOG

## 2025年12月2日 - UI Development Initialization

### Objective
Initiate the development of a Flutter-based UI for MyChatDev, ensuring full configurability of backend CLI parameters and compliance of UI agent roles with backend definitions.

### Key Decisions & Progress

1.  **UI Plan Approved:** The proposal for a new Flutter UI (`ui/flutter_app/`) to integrate with a FastAPI backend (`src/api.py`) has been approved. The plan ensures all CLI parameters will be configurable via the Flutter app.
2.  **UI Role Compliance:** A strategy has been approved to dynamically fetch agent roles from the FastAPI backend, ensuring the UI accurately reflects backend definitions. This involved:
    *   Defining authoritative backend roles in `src/api.py`.
    *   Implementing a `/roles` endpoint in FastAPI to serve these roles.
    *   Updating `ui/flutter_app/lib/widgets/chat_message.dart` to use dynamic string roles and a simplified message sender type.
    *   Updating `ui/flutter_app/lib/main.dart` to fetch these roles via HTTP, map them to Flutter `IconData` and `Color` objects, and dynamically populate the agent display.
3.  **Core Workflow Refactoring:** The core workflow execution logic has been refactored into `src/workflow_service.py`, with `execute_workflow` as a reusable function now consumed by both `src/cli.py` and `src/main.py`. This significantly improves modularity and prepares the backend for API integration.
4.  **FastAPI `/workflow/start` Endpoint Implemented:** The `/workflow/start` POST endpoint has been added to `src/api.py`, capable of receiving workflow parameters (user prompt, config, profiles) and triggering the `execute_workflow` function.
5.  **FastAPI `/workflow/stop` Decision (MVP Scope):** For the current MVP phase, the `/workflow/stop` endpoint will be implemented as a placeholder. Gracefully interrupting an ongoing `execute_workflow` would require significant architectural changes to the core `GraphWorkflow` and agent logic, as Python's `asyncio.Task` cancellation is cooperative. This more complex functionality is deferred to a later phase (e.g., Phase 3: Advanced Features & Refinements) to avoid blocking immediate progress on core API functionality.
6.  **Project Scaffolding:**
    *   Created `ui/flutter_app` directory for the new Flutter project.
    *   Scaffolded a new Flutter project within `ui/flutter_app`.
    *   Created `src/api.py` for the FastAPI backend.
    *   Implemented a basic FastAPI application structure and the `/roles` endpoint in `src/api.py`.
    *   Created `run_api.py` as an entry point to run the FastAPI server using `uvicorn`.
    *   Confirmed `fastapi` and `uvicorn` are present in `requirements.txt`.
    *   Created `ui/flutter_app/lib/widgets` directory.
    *   Migrated core UI widgets (`agent_card.dart`, `chat_log.dart`, `chat_message.dart`, `loading_indicator.dart`, `project_stats_chart.dart`) from the `Flutter-UI-prototype-for-ChatDev-X` directory to `ui/flutter_app/lib/widgets`.
    *   Added `http` dependency to `ui/flutter_app/pubspec.yaml` and installed it.
    *   Modified `ui/flutter_app/lib/main.dart` to dynamically fetch and display agent roles from the FastAPI `/roles` endpoint, replacing mock data.

6.  **Phase 2 Commencement and Key UI Implementations:**
    *   **LLM Profile Management UI:**
        *   Implemented UI to display existing LLM profiles fetched from the `/profiles` GET endpoint.
        *   Implemented UI for adding new LLM profiles via a dialog with form fields, integrating with the `/profiles` POST endpoint.
        *   Implemented UI for deleting LLM profiles, including a confirmation dialog and integration with the `/profiles` DELETE endpoint.
    *   **Workflow Control & Status UI:**
        *   Integrated "開始開發 (Start)" and "停止 (Stop)" buttons with the `/workflow/start` (POST) and `/workflow/stop` (POST) API endpoints, respectively.
        *   Implemented a polling mechanism to fetch real-time workflow status (current phase, steps, LOC, active agent) from the `/workflow/status/{run_id}` GET endpoint and update the UI accordingly.
        *   Integrated a custom Server-Sent Events (SSE) client to stream real-time logs and messages from the `/workflow/stream` GET endpoint into the chat log.
    *   **Main Screen & Navigation:**
        *   Implemented the main `ChatDevXScreen` layout and sidebar navigation.
        *   Implemented placeholder content for various navigation items (Dashboard, Past Tasks, etc.).
        *   Built forms/widgets for user prompt input, domain, language, and LLM profile selection, with dynamic population from the `/profiles` API for LLM profiles.
    *   **Error Handling and User Feedback:**
        *   Added basic error handling and user feedback mechanisms (e.g., Snackbars) for API interactions like adding and deleting LLM profiles.
        *   Implemented a loading indicator that appears when a workflow is active.

### Next Steps (Based on the Approved Development Phases):

*   **Phase 1: Core API & CLI Integration (Backend Focus):**
    *   Refactor core workflow execution logic into a reusable module.
    *   Implement API endpoints for workflow start/stop/status/deliverables.
    *   Implement API endpoints for profile and config management.
    *   Integrate real-time communication (WebSockets/SSE) for workflow updates.
    *   Implement comprehensive error handling and validation.
*   **Phase 2: Flutter UI Development & Backend Connection (Frontend Focus):**
    *   Implement API client in Flutter.
    *   Develop UI for Dashboard, New Task, Workflow Status, LLM Profiles, Global Settings, Past Workflows.
    *   Integrate real-time updates into the UI.
    *   Implement loading/error states in UI.
*   **Testing:** Conduct unit, integration, and E2E tests for each phase.

## 2025年12月3日 - Database Integration for API Endpoints

### Objective
Integrate SQLite database for persistent storage of workflow run data, and modify FastAPI endpoints to utilize this database for status and history retrieval.

### Key Decisions & Progress
1.  **Added `database_url` to `SystemConfig`**: Modified `src/config/settings.py` to include a `database_url` field, defaulting to `sqlite:///./data/db.sqlite`.
2.  **Created `src/database.py`**: Implemented functions for SQLite connection, schema initialization, and CRUD operations for `workflow_runs` table.
3.  **Integrated Database with `workflow_service.py`**: Modified `src/workflow_service.py` to:
    *   Call `initialize_db` at the start of `execute_workflow`.
    *   Insert a new `workflow_run` record when a workflow begins.
    *   Update the `workflow_run` record on successful completion or error.
4.  **Updated FastAPI Endpoints in `src/api.py`**:
    *   `/workflow/status/{run_id}`: Modified to fetch workflow run details from the SQLite database.
    *   `/workflow/runs`: Modified to fetch all workflow runs from the SQLite database.
    *   Resolved duplicate endpoint definitions and `WorkflowRunSummary` Pydantic models.
    *   Corrected `SyntaxError` in f-strings within `/workflow/stream` endpoint.
    *   Corrected `AttributeError` by properly accessing `LLMConfig` defaults in `LLMConfigModel`.
    *   Corrected `TypeError` by ensuring `Path` objects are converted to strings before JSON serialization in `test_api_database.py` fixture.
5.  **Centralized `USER_PROFILES_DIR`**: Moved `USER_PROFILES_DIR` definition to `src/config/settings.py` and updated `src/api.py` and `src/cli.py` to import it from there.
6.  **Created and Passed Integration Tests**: Developed `tests/integration/test_api_database.py` to validate the database integration with FastAPI endpoints. All tests passed successfully.

## Phase 3 Roadmap & Future Priorities

Having achieved MVP Complete status, the following features have been identified and prioritized for the next phase of development.

### 🚨 High Priority (Immediate / Next Phase)
*Focus: Usability, Control, and Reliability*

1.  **🛑 Workflow Cancellation (`/workflow/stop`)**
    *   **Status:** `501 Not Implemented`.
    *   **Goal:** Implement backend logic to gracefully interrupt async `execute_workflow` tasks and clean up resources.
    *   **Reason:** Critical for user control; users currently cannot stop a runaway or unwanted process without killing the server.

2.  **🔄 Workflow Resumption**
    *   **Status:** Missing.
    *   **Goal:** Enable resuming a stopped, failed, or completed workflow from a specific node or state using stored database history.
    *   **Reason:** Improves efficiency by preventing the need to restart long workflows from scratch due to minor errors.

3.  **🌐 Error Recovery Mechanisms**
    *   **Status:** Basic.
    *   **Goal:** Implement advanced self-healing, automatic retries with backoff strategies for network/LLM failures, and robust error boundaries.
    *   **Reason:** Enhances system reliability and robustness against transient external issues.

### 🚀 Medium Priority (Feature Expansion)
*Focus: Scalability, Extensibility, and Core Value*

4.  **🧠 Advanced Memory/Context Management**
    *   **Status:** Limited.
    *   **Goal:** Integrate a persistent vector database (RAG) or long-term memory module to allow agents to "learn" from past projects and retain context across sessions.
    *   **Reason:** significantly improves the "intelligence" and utility of the system for repeated use.

5.  **📂 Large File Handling**
    *   **Status:** Known Limitation.
    *   **Goal:** Implement chunking, streaming, and optimized storage for handling large source files and deliverables.
    *   **Reason:** Necessary for real-world software development tasks which often involve substantial codebases.

6.  **🔌 Plugin System**
    *   **Status:** Planned.
    *   **Goal:** Create an architecture for registering custom workflow nodes, alternative LLM providers, and CLI sub-commands.
    *   **Reason:** Fosters community growth and allows users to extend functionality without modifying core code.

### 📉 Low Priority (Enterprise / Future)
*Focus: Broad Scaling and Administrative Features*

7.  **⚡ Distributed/Concurrent Workflow Execution**
    *   **Status:** Sequential only.
    *   **Goal:** Implement job queues (e.g., Celery, Redis) and worker pools to manage multiple simultaneous heavy workflows.
    *   **Reason:** Required for scaling to multiple users or massive batch jobs, but not critical for single-user local usage.

8.  **🔐 Multi-User Authentication & Authorization**
    *   **Status:** None.
    *   **Goal:** Add login, user management, and role-based access control (RBAC) for API and UI.
    *   **Reason:** Essential for hosted/shared deployments but adds unnecessary complexity for a local tool.

9.  **📊 Advanced Analytics & Reporting**
    *   **Status:** Basic.
    *   **Goal:** Provide historical trend analysis, detailed performance metrics charts, and exportable reports.
    *   **Reason:** "Nice to have" for insights but doesn't directly impact the core code generation capability.
