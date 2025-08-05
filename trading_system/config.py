# Trading System Configuration
# Safe to commit - no secrets here!

# Trading schedule settings
RUN_EVERY_N_MINUTES = 10  # Reduced from 5 to 10 minutes to save resources
RUN_EVEN_WHEN_MARKET_IS_CLOSED = False

# Market override (for testing/portfolio building) 
FORCE_MARKET_OPEN = False  # Changed to False - let market hours control trading

# Trading schedules for each trader
REBALANCE_SCHEDULE = {
    "warren": "daily",      # Once per day
    "camillo": "daily",     # Once per day  
    "pavel": "3x_daily"     # 3 times per day
}