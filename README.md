# MyChatDev - Cooperative LLM System with Ollama

A Python program that enables cooperative interaction between multiple locally hosted LLMs using Ollama, orchestrated through LangGraph workflows.

## 🏗️ Architecture

The system implements a software development workflow where different LLMs take on specialized roles:

- **Product Manager** (gemma3:4b) - Requirements analysis
- **System Architect** (phi4:14b) - System design  
- **Programmer** (qwen2.5-coder) - Code implementation
- **Tester** (deepseek-coder:6.7b) - Testing and validation
- **Code Reviewer** (llama3.2) - Quality review and feedback

## 📁 Project Structure

```
MyChatDev/
├── main.py                    # Entry point and orchestration
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── config/
│   └── settings.py           # Configuration management
├── models/
│   └── llm_manager.py        # LLM communication and management
├── workflow/
│   ├── graph_nodes.py        # LangGraph node implementations
│   └── quality_gate.py       # Quality control and gatekeeper
├── utils/
│   ├── logging_config.py     # Logging configuration
│   └── prompts.py           # Centralized prompt management
└── tests/
    └── test_llm_manager.py   # Unit tests
```

## 🚀 Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure Ollama is running:**
   ```bash
   ollama serve
   ```

3. **Verify required models are available:**
   ```bash
   ollama list
   ```

## 🎯 Usage

### Basic Usage

```python
import asyncio
from workflow.simple_workflow import SimpleCooperativeLLM
from config.settings import DEFAULT_CONFIG

async def main():
    # Initialize workflow
    workflow = SimpleCooperativeLLM(DEFAULT_CONFIG)
    
    # Define your requirements
    user_input = """
    Create a Python web scraper that can:
    1. Extract product information from e-commerce websites
    2. Handle rate limiting and respect robots.txt
    3. Store data in a SQLite database
    4. Include error handling and logging
    """
    
    # Execute workflow
    final_state = await workflow.run(user_input)
    
    # Access deliverables
    print("Requirements:", final_state.requirements)
    print("Design:", final_state.design)
    print("Code:", final_state.code)

asyncio.run(main())
```

### Running the Complete System

```bash
python main.py
```

## 🔧 Configuration

### LLM Model Assignment

Edit `config/settings.py` to customize model assignments:

```python
AVAILABLE_LLMS = {
    "product_manager": LLMConfig(
        name="Product Manager",
        model_id="gemma3:4b",  # Change to your preferred model
        role="product_manager",
        temperature=0.3
    ),
    # ... other roles
}
```

### System Parameters

```python
DEFAULT_CONFIG = SystemConfig(
    ollama_host="http://localhost:11434",
    max_iterations=5,           # Maximum workflow iterations
    quality_threshold=0.8,      # Quality score to halt execution
    change_threshold=0.1,       # Minimum change threshold
    enable_compression=True,    # Enable message compression
    compression_threshold=5000, # Characters before compression
    log_level="INFO"
)
```

## 🎛️ Quality Gate System

The system includes an intelligent quality gate that monitors:

- **Quality Score**: Overall deliverable quality (0-1)
- **Change Magnitude**: Amount of change between iterations (0-1)
- **Automatic Halting**: Stops when quality threshold is met or changes are minimal

### Quality Gate Behavior

- **HALT** when quality_score ≥ 0.8 OR change_magnitude ≤ 0.1
- **CONTINUE** otherwise (up to max_iterations)

## 📊 Logging and Debugging

### Comprehensive Logging

- **Node Execution**: Detailed logs for each workflow step
- **Timestamps**: All operations timestamped
- **Input/Output Tracking**: Size and content logging
- **Error Handling**: Detailed error reporting

### Log Files

Logs are saved to `logs/coop_llm_YYYYMMDD_HHMMSS.log`

### Debug Information

```python
# Enable debug logging
from utils.logging_config import setup_logging
logger = setup_logging("DEBUG")
```

## 📦 Deliverables

The system generates:

- **requirements_specification.md** - Analyzed requirements
- **system_design.md** - Architectural design
- **source_code.py** - Implementation code
- **test_results.md** - Testing and validation results
- **review_feedback.md** - Code review feedback
- **complete_state.json** - Full workflow state

## 🧪 Testing

Run unit tests:

```bash
pytest tests/
```

Run specific test:

```bash
pytest tests/test_llm_manager.py::TestLLMManager::test_generate_response_success
```

## 🔄 Workflow Process

1. **Requirements Analysis** - Product Manager analyzes user input
2. **System Design** - Architect creates technical design
3. **Code Implementation** - Programmer writes the code
4. **Testing & Debugging** - Tester validates implementation
5. **Review & Refinement** - Reviewer provides feedback
6. **Quality Gate** - Automated quality assessment
7. **Output Generation** - Final deliverable compilation

## 🎨 Design Principles

- **Modularity**: Clear separation of concerns
- **Extensibility**: Easy to add new LLMs and workflows
- **Loose Coupling**: Minimal dependencies between components
- **Single Responsibility**: Each module has one clear purpose
- **Error Resilience**: Comprehensive error handling
- **Observability**: Detailed logging and monitoring

## 🔧 Extending the System

### Adding New LLM Roles

1. **Define LLM Config** in `config/settings.py`:
   ```python
   "new_role": LLMConfig(
       name="New Role",
       model_id="your-model:tag",
       role="new_role"
   )
   ```

2. **Add Prompt Template** in `utils/prompts.py`:
   ```python
   NEW_ROLE = """Your role-specific prompt template..."""
   ```

3. **Create Node Function** in `workflow/graph_nodes.py`:
   ```python
   async def new_role_node(self, state: WorkflowState) -> WorkflowState:
       # Implementation
   ```

4. **Update Graph** in `_build_graph()` method

### Custom Quality Metrics

Extend `workflow/quality_gate.py` to add custom quality assessments:

```python
def custom_quality_check(self, state: WorkflowState) -> float:
    # Your custom quality logic
    return quality_score
```

## 🚨 Troubleshooting

### Common Issues

1. **Model Not Available**
   ```bash
   ollama pull model-name:tag
   ```

2. **Connection Error**
   - Ensure Ollama is running: `ollama serve`
   - Check host configuration in settings

3. **Memory Issues**
   - Enable compression: `enable_compression=True`
   - Reduce `compression_threshold`
   - Use smaller models for non-critical roles

### Performance Optimization

- Use lightweight models for summarization
- Enable message compression for long workflows
- Adjust temperature settings for consistency vs creativity
- Monitor iteration counts and quality thresholds

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the logs in `logs/` directory
- Review configuration in `config/settings.py`
- Run tests to verify functionality
- Enable debug logging for detailed troubleshooting