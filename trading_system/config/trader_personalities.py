"""
Trader Personality Configuration
Central repository for all trader personality definitions and characteristics
"""

TRADER_PERSONALITIES = {
    "warren": {
        "name": "Warren Buffett",
        "style": "Value Investing",
        "time_horizon": "Long-term (5+ years)",
        "risk_tolerance": "Conservative",
        "focus": "Focus on fundamental analysis, earnings quality, long-term value opportunities, and economic indicators that affect intrinsic business value.",
        "topics": ["earnings", "financial_markets", "economy_macro"],
        "analysis_prompt": """
        You are analyzing for Warren Buffett, the legendary value investor.
        Focus on:
        - Long-term value and fundamentals
        - Business quality and economic moats
        - Patient investing approach
        - Price vs intrinsic value analysis
        """
    },
    "camillo": {
        "name": "Chris Camillo", 
        "style": "Social Arbitrage",
        "time_horizon": "Short to Medium-term (days to months)",
        "risk_tolerance": "Moderate-High",
        "focus": "Focus on emerging trends, cultural signals, consumer sentiment, and viral narratives before Wall Street catches on.",
        "topics": ["technology", "consumer_trends", "social_media"],
        "analysis_prompt": """
        You are analyzing for Chris Camillo, focused on social arbitrage investing.
        Focus on:
        - Emerging trends and cultural signals
        - Consumer sentiment and viral narratives
        - Social media buzz and influencer activity
        - Unconventional data sources and early indicators
        """
    },
    "pavel": {
        "name": "Pavel Krejci",
        "style": "Day Trading", 
        "time_horizon": "Intraday (minutes to hours)",
        "risk_tolerance": "High Frequency",
        "focus": "Focus on immediate market catalysts, earnings surprises, momentum shifts, and short-term trading opportunities with high volatility.",
        "topics": ["earnings", "financial_markets", "mergers_and_acquisitions"],
        "analysis_prompt": """
        You are analyzing for Pavel Krejci, an expert day trader.
        Focus on:
        - Short-term momentum and technical catalysts
        - Quick opportunities with high volatility
        - Immediate market-moving events
        - Rapid entry/exit strategies
        """
    },
    "general": {
        "name": "General",
        "style": "Balanced Analysis",
        "time_horizon": "Variable",
        "risk_tolerance": "Moderate",
        "focus": "Balanced market analysis suitable for any trading style.",
        "topics": ["financial_markets"],
        "analysis_prompt": """
        You are providing general market analysis.
        Focus on:
        - Balanced perspective suitable for any trading style
        - Comprehensive market overview
        - Key opportunities and risks
        - Factual data-driven insights
        """
    }
}

def get_trader_personality(user_id: str) -> dict:
    """
    Get trader personality configuration by user ID
    
    Args:
        user_id: Trader identifier (warren, camillo, pavel, general, or any external user ID)
    
    Returns:
        Dictionary containing trader personality configuration
    """
    # For internal users, map directly to personality
    if user_id.lower() in TRADER_PERSONALITIES:
        return TRADER_PERSONALITIES[user_id.lower()]
    
    # For external users, default to general for now
    # In the future, this could lookup user preferences from a database
    return TRADER_PERSONALITIES["general"]

def get_all_trader_personalities() -> dict:
    """Get all available trader personalities"""
    return TRADER_PERSONALITIES

def get_trader_topics(user_id: str) -> list:
    """Get the topics of interest for a specific trader"""
    personality = get_trader_personality(user_id)
    return personality.get("topics", ["financial_markets"])

def get_trader_analysis_prompt(user_id: str) -> str:
    """Get the analysis prompt for a specific trader"""
    personality = get_trader_personality(user_id)
    return personality.get("analysis_prompt", "Provide general market analysis.")