"""
Example usage of the Cooperative LLM System.

This script contains three *high‑level* example workflows that show how the
`SimpleCooperativeLLM` class can be used to generate production‑ready code
for a variety of common application types:

1. A web‑scraper application
2. A REST API service (FastAPI)
3. A data‑processing pipeline (Airflow + Pandas)

The `run_all_examples()` helper orchestrates the three examples and prints a
nice summary of how well each one performed according to the workflow’s
quality metrics.

All examples are fully asynchronous; you can run each one individually or
run them all at once.
"""

import asyncio
from workflow.simple_workflow import SimpleCooperativeLLM
from config.settings import DEFAULT_CONFIG, SystemConfig
from utils.logging_config import setup_logging


# --------------------------------------------------------------------------- #
# 1️⃣  Web Scraper Example
# --------------------------------------------------------------------------- #
async def example_web_scraper() -> "State":
    """
    Demonstrate creating a production‑ready web‑scraper.

    The prompt describes a feature‑rich scraper that must handle rate limiting,
    obey robots.txt, store data in SQLite, and be configurable via JSON.
    """
    # Configure a dedicated logger for this example
    logger = setup_logging("INFO")
    logger.info("Starting web scraper example")

    # Prompt that will be fed into the cooperative workflow
    user_input = """
    Create a Python web scraper that can:
    1. Extract product information from e-commerce websites
    2. Handle rate limiting and respect robots.txt
    3. Store data in a SQLite database with proper schema
    4. Include comprehensive error handling and logging
    5. Be configurable for different websites through JSON config
    6. Support concurrent scraping with thread safety
    7. Include data validation and cleaning
    8. Generate reports on scraped data

    The scraper should be production‑ready with:
    - Proper documentation and docstrings
    - Unit tests for core functionality
    - Configuration management
    - Monitoring and alerting capabilities
    - Data export functionality (CSV, JSON)
    """

    # A custom configuration for this particular example
    config = SystemConfig(
        max_iterations=3,      # Run the iterative improvement loop 3 times
        quality_threshold=0.85,
        change_threshold=0.05,
        enable_compression=True   # Compress messages to reduce LLM token usage
    )

    # Initialise the workflow with the custom config
    workflow = SimpleCooperativeLLM(config)

    # Execute the workflow – this returns the final `State` object
    final_state = await workflow.run(user_input)

    # Pretty‑print a small summary of the result
    print("\n" + "=" * 60)
    print("🎉 WEB SCRAPER PROJECT COMPLETED!")
    print(
        f"📊 Quality Score: {final_state.quality_evaluations[-1]['quality_score']:.2f}"
    )
    print(f"🔄 Iterations: {final_state.iteration_count}")
    print("=" * 60)

    return final_state


# --------------------------------------------------------------------------- #
# 2️⃣  REST API Service Example
# --------------------------------------------------------------------------- #
async def example_api_service() -> "State":
    """
    Demonstrate creating a FastAPI‑based REST API service.

    The prompt includes a full set of requirements from CRUD operations to
    Dockerisation and CI/CD pipeline configuration.
    """
    user_input = """
    Create a FastAPI-based REST API service that:
    1. Manages a library book catalog system
    2. Supports CRUD operations for books, authors, and categories
    3. Implements user authentication and authorization
    4. Includes data validation with Pydantic models
    5. Uses SQLAlchemy ORM with PostgreSQL
    6. Implements caching with Redis
    7. Includes comprehensive API documentation
    8. Has proper error handling and logging
    9. Supports pagination and filtering
    10. Includes rate limiting and security headers

    Requirements:
    - Docker containerisation
    - Database migrations
    - Unit and integration tests
    - CI/CD pipeline configuration
    - Monitoring and health checks
    """

    # Reuse the global DEFAULT_CONFIG – the API service is more complex,
    # so the defaults are usually sufficient.
    workflow = SimpleCooperativeLLM(DEFAULT_CONFIG)

    final_state = await workflow.run(user_input)

    print("\n" + "=" * 60)
    print("🎉 API SERVICE PROJECT COMPLETED!")
    print(
        f"📊 Quality Score: {final_state.quality_evaluations[-1]['quality_score']:.2f}"
    )
    print(f"🔄 Iterations: {final_state.iteration_count}")
    print("=" * 60)

    return final_state


# --------------------------------------------------------------------------- #
# 3️⃣  Data Pipeline Example
# --------------------------------------------------------------------------- #
async def example_data_pipeline() -> "State":
    """
    Demonstrate building a data‑processing pipeline with Airflow.

    The prompt describes ingestion, cleaning, validation, and reporting,
    including modern tooling like Great Expectations.
    """
    user_input = """
    Create a data processing pipeline that:
    1. Ingests data from multiple sources (CSV, JSON, APIs)
    2. Performs data cleaning and transformation
    3. Validates data quality and completeness
    4. Stores processed data in a data warehouse
    5. Generates automated reports and visualizations
    6. Supports real‑time and batch processing
    7. Includes error handling and retry mechanisms
    8. Has monitoring and alerting capabilities
    9. Supports data lineage tracking
    10. Includes data privacy and security measures

    Technical requirements:
    - Apache Airflow for orchestration
    - Pandas/Polars for data processing
    - Great Expectations for data validation
    - Docker for containerisation
    - Comprehensive logging and monitoring
    """

    workflow = SimpleCooperativeLLM(DEFAULT_CONFIG)

    final_state = await workflow.run(user_input)

    print("\n" + "=" * 60)
    print("🎉 DATA PIPELINE PROJECT COMPLETED!")
    print(
        f"📊 Quality Score: {final_state.quality_evaluations[-1]['quality_score']:.2f}"
    )
    print(f"🔄 Iterations: {final_state.iteration_count}")
    print("=" * 60)

    return final_state


# --------------------------------------------------------------------------- #
# 4️⃣  Orchestrate All Examples
# --------------------------------------------------------------------------- #
async def run_all_examples() -> None:
    """
    Execute all three example workflows sequentially and print a
    consolidated results table.
    """
    print("🚀 RUNNING ALL COOPERATIVE LLM EXAMPLES")
    print("=" * 60)

    # List of (name, coroutine) tuples for easier iteration
    examples = [
        ("Web Scraper", example_web_scraper),
        ("API Service", example_api_service),
        ("Data Pipeline", example_data_pipeline),
    ]

    results = {}  # Will store the status of each example

    for name, example_func in examples:
        print(f"\n🔄 Starting {name} example...")
        try:
            result = await example_func()
            results[name] = {
                "status": "success",
                "iterations": result.iteration_count,
                # If the workflow produced no quality metrics, default to 0
                "quality_score": (
                    result.quality_evaluations[-1]["quality_score"]
                    if result.quality_evaluations
                    else 0
                ),
            }
        except Exception as e:
            # Capture any exception so the summary still prints
            print(f"❌ Error in {name}: {e}")
            results[name] = {"status": "error", "error": str(e)}

    # ---- Summary -------------------------------------------------------- #
    print("\n" + "=" * 60)
    print("📊 EXAMPLES SUMMARY")
    print("=" * 60)

    for name, result in results.items():
        if result["status"] == "success":
            print(
                f"✅ {name}: Quality {result['quality_score']:.2f}, "
                f"Iterations {result['iterations']}"
            )
        else:
            print(f"❌ {name}: {result['error']}")

    print("=" * 60)


# --------------------------------------------------------------------------- #
# Entry point – run either a single example or all of them
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Uncomment one of the following lines to run a specific example
    # asyncio.run(example_web_scraper())
    # asyncio.run(example_api_service())
    # asyncio.run(example_data_pipeline())

    # Or run them all in sequence
    asyncio.run(run_all_examples())