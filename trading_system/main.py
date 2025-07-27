"""
Main entry point for the AI Trading System
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'OPENAI_API_KEY',
        'ALPHAVANTAGE_API_KEY',
        'POLYGON_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease add these to your .env file")
        return False
    
    print("✅ All required environment variables are set")
    return True

def main():
    """Main function to run the trading system"""
    print("🤖 AI Trading System")
    print("=" * 40)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    print("\n🚀 Starting Streamlit interface...")
    print("📊 Market Intelligence: Alpha Vantage")
    print("📈 Technical Analysis: Polygon")
    print("🎯 AI Traders: Warren, Cathie, Pavel")
    print("\n" + "=" * 40)
    
    # Run Streamlit app
    os.system("streamlit run app.py")

if __name__ == "__main__":
    main()