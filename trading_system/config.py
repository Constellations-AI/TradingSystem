# Trading System Configuration
# Safe to commit - no secrets here!

# Trading schedule settings
RUN_EVERY_N_MINUTES = 5  # Check every 5 minutes for Pavel's frequent trading
RUN_EVEN_WHEN_MARKET_IS_CLOSED = False

# Market override (for testing/portfolio building)
FORCE_MARKET_OPEN = False  # Chris Camillo has built his portfolio

# Trading schedules for each trader
REBALANCE_SCHEDULE = {
    "warren": "daily",      # Once per day
    "camillo": "daily",     # Once per day  
    "pavel": "3x_daily"     # 3 times per day
}