"""Test script to verify quality improvements."""

import asyncio
from workflow.simple_workflow import SimpleCooperativeLLM
from config.settings import SystemConfig
from config.llm_profiles import AVAILABLE_LLMS_BY_PROFILE
from utils.logging_config import setup_logging


async def test_quality_improvements():
    """Test that the system runs multiple iterations and improves quality."""
    
    logger = setup_logging("INFO")
    logger.info("Testing quality improvements")
    
    # Simple test that should produce good results
    user_input = """
    Create a simple Python calculator program that:
    1. Has a command-line interface
    2. Supports basic operations (+, -, *, /)
    3. Handles division by zero errors
    4. Includes input validation
    """
    
    # Use optimized profile with stricter quality requirements
    config = SystemConfig(
        max_iterations=3,
        quality_threshold=0.8,
        change_threshold=0.05,
        enable_compression=False  # Disable compression for testing
    )
    
    llm_configs = AVAILABLE_LLMS_BY_PROFILE["optimized"]
    
    try:
        workflow = SimpleCooperativeLLM(config, llm_configs)
        logger.info("Starting quality improvement test...")
        
        final_state = await workflow.run(user_input)
        
        # Analyze results
        logger.info("=== QUALITY TEST RESULTS ===")
        logger.info(f"Iterations completed: {final_state.iteration_count}")
        logger.info(f"Quality evaluations: {len(final_state.quality_evaluations)}")
        
        if final_state.quality_evaluations:
            final_quality = final_state.quality_evaluations[-1].get("quality_score", 0)
            logger.info(f"Final quality score: {final_quality:.2f}")
            
            # Check if quality improved over iterations
            if len(final_state.quality_evaluations) > 1:
                first_quality = final_state.quality_evaluations[0].get("quality_score", 0)
                logger.info(f"Quality improvement: {first_quality:.2f} → {final_quality:.2f}")
                
                if final_quality > first_quality:
                    logger.info("✅ Quality improved over iterations")
                else:
                    logger.warning("⚠️ Quality did not improve")
            
            # Check if minimum iterations were met
            if final_state.iteration_count >= 2:
                logger.info("✅ Minimum iterations requirement met")
            else:
                logger.warning("⚠️ Did not meet minimum iterations requirement")
            
            # Check final quality
            if final_quality >= 0.8:
                logger.info("✅ Quality threshold achieved")
                return True
            else:
                logger.warning(f"⚠️ Quality threshold not met: {final_quality:.2f} < 0.8")
                return False
        else:
            logger.error("❌ No quality evaluations found")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_quality_improvements())
    if success:
        print("\n🎉 Quality improvement test PASSED!")
    else:
        print("\n❌ Quality improvement test FAILED!")