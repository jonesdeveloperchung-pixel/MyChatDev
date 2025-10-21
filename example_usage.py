import asyncio
from workflow.graph_workflow import GraphWorkflow
from config.settings import DEFAULT_CONFIG
from config.llm_profiles import AVAILABLE_LLMS_BY_PROFILE # Import profiles

async def main():
    # Initialize workflow with a specific profile (e.g., 'high_reasoning')
    # You can choose 'high_reasoning', 'medium_reasoning', or 'low_reasoning'
    llm_configs = AVAILABLE_LLMS_BY_PROFILE['high_reasoning']
    workflow = GraphWorkflow(DEFAULT_CONFIG, llm_configs)
    
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
    print("Requirements:", final_state.deliverables['requirements'])
    print("Design:", final_state.deliverables['design'])
    print("Code:", final_state.deliverables['code'])
    print("Test Results:", final_state.deliverables['test_results'])
    print("Review Feedback:", final_state.deliverables['review_feedback'])
    print("Strategic Guidance:", final_state.deliverables['strategic_guidance'])

if __name__ == "__main__":
    asyncio.run(main())