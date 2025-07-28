#!/usr/bin/env python3
"""
Test script to verify LangSmith is working correctly
"""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv(override=True)

def test_langsmith_setup():
    """Test basic LangSmith setup"""
    print("🧪 Testing LangSmith Setup...")
    
    # Check API key
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("❌ LANGSMITH_API_KEY not found in environment")
        print("ℹ️ Add LANGSMITH_API_KEY to your .env file")
        return False
    
    print(f"✅ LANGSMITH_API_KEY found: {api_key[:8]}...")
    
    # Check tracing enabled
    tracing_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    if not tracing_enabled:
        print("❌ LANGSMITH_TRACING is not enabled")
        print("ℹ️ Set LANGSMITH_TRACING=true in your .env file")
        return False
    
    print("✅ LANGSMITH_TRACING is enabled")
    
    # Check project
    project = os.getenv("LANGSMITH_PROJECT")
    if project:
        print(f"✅ LANGSMITH_PROJECT: {project}")
    else:
        print("⚠️ LANGSMITH_PROJECT not set, using default")
    
    # Test import
    try:
        import langsmith
        print("✅ langsmith imported successfully")
    except ImportError:
        print("❌ langsmith not installed")
        print("ℹ️ Run: pip install langsmith")
        return False
    
    # Test LangChain environment setup
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGCHAIN_PROJECT"] = project or "trading-system"
    print("✅ LangChain environment variables set")
    
    return True

async def test_agent_tracing():
    """Test agent tracing with LangSmith"""
    print("\n🧪 Testing Agent Tracing...")
    
    try:
        from agents.market_intelligence_agent import MarketIntelligenceAgent
        
        # Create agent
        agent = MarketIntelligenceAgent()
        await agent.setup()
        
        # Run a simple query that should be traced
        print("📊 Running market intelligence query...")
        result = await agent.run_superstep(
            message="What's the current market sentiment?",
            success_criteria="Provide a brief market overview",
            history=[],
            debug=True
        )
        
        print("✅ Agent call completed successfully")
        print(f"📝 Result length: {len(str(result))} characters")
        print("🔍 Check LangSmith dashboard for traces")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent tracing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 LangSmith Integration Test\n")
    
    # Test basic setup
    if not test_langsmith_setup():
        print("\n❌ Basic setup failed - fix issues above first")
        return
    
    # Test agent tracing
    await test_agent_tracing()
    
    print("\n✅ LangSmith integration test completed!")
    print("📊 Check your LangSmith dashboard for traces")

if __name__ == "__main__":
    asyncio.run(main())