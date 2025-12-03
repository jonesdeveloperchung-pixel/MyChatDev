## GitHub Commit Message

```
feat: Introduce Flutter UI and FastAPI backend for enhanced user experience

This commit significantly expands the MyChatDev project by introducing a new Flutter-based Web User Interface (UI) and a FastAPI backend API. This architectural enhancement aims to provide a user-friendly way to configure, run, and monitor development workflows, making the system accessible beyond the command-line interface.

Key changes and progress include:
- **FastAPI Backend API:** Implemented `src/api.py` to expose core MyChatDev functionalities via a RESTful API. This includes an initial `/roles` endpoint for dynamic agent role fetching.
- **Flutter Web UI:** Scaffolded a new Flutter project at `ui/flutter_app/` and migrated essential UI components from the previous prototype.
- **Dynamic UI Roles:** Modified the Flutter UI (`ui/flutter_app/lib/main.dart` and `ui/flutter_app/lib/widgets/chat_message.dart`) to dynamically fetch and display agent roles from the FastAPI backend, ensuring compliance with backend definitions.
- **Project Structure Update:** Updated `README.md` and project structure to reflect the inclusion of the `ui/` directory, `src/api.py`, and `run_api.py`.
- **Installation & Usage Documentation:** Revised `README.md` to guide users on installing Flutter and running both the FastAPI backend and the Flutter frontend.
- **Development Log:** `DEVELOPMENT_LOG.md` has been updated to detail these development phases and progress.

This foundational work lays the groundwork for a rich, interactive user experience, complementing the powerful CLI.
```

## GitHub Repository Description

```
MyChatDev is a cooperative LLM system orchestrating multiple agents for software development tasks. This version introduces a powerful new Flutter-based Web User Interface (UI) and a FastAPI backend API, transforming the project into a comprehensive platform accessible via both CLI and an intuitive UI. It builds upon a stable baseline with dependency fixes and architectural groundwork for integrating the Model Context Protocol (MCP) as a pluggable sandbox environment. Future development will focus on fully integrating the UI with all backend functionalities and further enhancing the core LLM workflow.
```