"""
LangSmith Configuration for Trading System
Initializes LangSmith tracing for all LangGraph agents
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

def init_langsmith():
    """Initialize LangSmith with API key from environment"""
    try:
        # LangSmith is automatically initialized via environment variables
        # when langsmith is imported and the env vars are set
        import langsmith
        
        # Get API key from environment
        api_key = os.getenv("LANGSMITH_API_KEY")
        project = os.getenv("LANGSMITH_PROJECT")
        endpoint = os.getenv("LANGSMITH_ENDPOINT")
        tracing_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
        
        if not api_key:
            print("⚠️ LANGSMITH_API_KEY not found in environment variables")
            return False
        
        if not tracing_enabled:
            print("ℹ️ LangSmith tracing is disabled (LANGSMITH_TRACING=false)")
            return False
        
        # Set environment variables for LangChain tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project or "trading-system"
        if endpoint:
            os.environ["LANGCHAIN_ENDPOINT"] = endpoint
        
        print(f"✅ LangSmith initialized successfully - Project: {project}")
        return True
        
    except ImportError:
        print("❌ langsmith not installed. Run: pip install langsmith")
        return False
    except Exception as e:
        print(f"❌ Error initializing LangSmith: {e}")
        return False

def is_langsmith_enabled():
    """Check if LangSmith is properly configured"""
    api_key = os.getenv("LANGSMITH_API_KEY")
    tracing_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    return api_key is not None and tracing_enabled

# Auto-initialize when module is imported
if __name__ != "__main__":
    if is_langsmith_enabled():
        init_langsmith()
    else:
        print("ℹ️ LangSmith not configured - check LANGSMITH_API_KEY and LANGSMITH_TRACING")