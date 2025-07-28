"""
Trading Floor - Orchestrates all trader agents with proper scheduling and market hours
"""

import asyncio
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv
import os
import json
import pytz

from data.polygon import PolygonClient
from accounts import get_trader_account
from agents.market_intelligence_agent import MarketIntelligenceAgent
from agents.technical_analysis_agent import TechnicalAnalysisAgent
from agents.flash_trading_evaluator import create_flash_evaluator
from agents.trader_personality import warren_strategy, pavel_strategy, camillo_strategy
from openai import AsyncOpenAI

load_dotenv(override=True)

# Initialize LangSmith for tracing all trading activity
try:
    from langsmith_config import init_langsmith, is_langsmith_enabled
    if is_langsmith_enabled():
        init_langsmith()
        print("✅ LangSmith initialized for trading floor")
    else:
        print("ℹ️ LangSmith not configured - check LANGSMITH_API_KEY and LANGSMITH_TRACING")
except ImportError:
    print("ℹ️ LangSmith not available for trading floor")

# Import configuration - use absolute path to avoid conflicts
import os
import sys

# Debug info for Railway
current_dir = os.path.dirname(__file__)
config_py_path = os.path.join(current_dir, 'config.py')
config_dir_path = os.path.join(current_dir, 'config')

print(f"🔍 Current directory: {current_dir}")
print(f"🔍 Looking for config.py at: {config_py_path}")
print(f"🔍 config.py exists: {os.path.exists(config_py_path)}")
print(f"🔍 config/ directory exists: {os.path.exists(config_dir_path)}")
print(f"🔍 Files in current dir: {os.listdir(current_dir)}")

if os.path.exists(config_py_path):
    print("✅ Found config.py, loading it...")
    import importlib.util
    spec = importlib.util.spec_from_file_location("trading_config", config_py_path)
    trading_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trading_config)
    
    RUN_EVERY_N_MINUTES = trading_config.RUN_EVERY_N_MINUTES
    RUN_EVEN_WHEN_MARKET_IS_CLOSED = trading_config.RUN_EVEN_WHEN_MARKET_IS_CLOSED
    FORCE_MARKET_OPEN = trading_config.FORCE_MARKET_OPEN
    REBALANCE_SCHEDULE = trading_config.REBALANCE_SCHEDULE
    print(f"✅ Config loaded: FORCE_MARKET_OPEN={FORCE_MARKET_OPEN}")
else:
    # Fallback to hardcoded values if config.py not found
    print("❌ config.py not found, using fallback values")
    RUN_EVERY_N_MINUTES = 5
    RUN_EVEN_WHEN_MARKET_IS_CLOSED = False
    FORCE_MARKET_OPEN = True
    REBALANCE_SCHEDULE = {
        "warren": "daily",
        "camillo": "daily", 
        "pavel": "3x_daily"
    }
    print(f"⚠️ Using fallback: FORCE_MARKET_OPEN={FORCE_MARKET_OPEN}")


def get_eastern_time() -> datetime:
    """Get current time in US Eastern timezone (handles EST/EDT automatically)"""
    eastern = pytz.timezone('US/Eastern')
    return datetime.now(eastern)

def is_market_open() -> bool:
    """Check if the market is currently open using smart logic + Polygon API"""
    # Check for force override first
    if FORCE_MARKET_OPEN:
        return True
        
    # Always use Eastern Time for market hours regardless of system timezone
    now_et = get_eastern_time()
    
    # Quick local checks first (no API calls needed)
    if now_et.weekday() >= 5:  # Weekend (Saturday=5, Sunday=6)
        return False
    
    # Check if we're within potential market hours (9:30 AM - 4:00 PM ET)
    current_hour_decimal = now_et.hour + now_et.minute / 60
    if not (9.5 <= current_hour_decimal <= 16.0):  # 9:30 AM to 4:00 PM ET
        return False
    
    # If we pass basic checks, verify with Polygon API first
    try:
        polygon = PolygonClient()
        market_status = polygon.get_market_status()
        is_open = market_status.get("market") == "open"
        print(f"✅ Polygon API: Market is {'open' if is_open else 'closed'}")
        return is_open
    except Exception as e:
        print(f"❌ Polygon market status failed: {e}")
        
        # Fallback to Alpha Vantage
        try:
            import requests
            alphavantage_key = os.getenv("ALPHAVANTAGE_API_KEY")
            if not alphavantage_key:
                print("❌ No Alpha Vantage API key found")
                return False
                
            url = f'https://www.alphavantage.co/query?function=MARKET_STATUS&apikey={alphavantage_key}'
            response = requests.get(url, timeout=10)
            data = response.json()
            
            # Check US market status from Alpha Vantage response
            markets = data.get("markets", [])
            for market in markets:
                if market.get("region") == "United States" and market.get("market_type") == "Equity":
                    status = market.get("current_status", "closed").lower()
                    is_open = status == "open"
                    print(f"✅ Alpha Vantage fallback: US market is {status}")
                    return is_open
            
            print("❌ Alpha Vantage: Could not find US equity market status")
            return False
            
        except Exception as av_error:
            print(f"❌ Alpha Vantage fallback also failed: {av_error}")
            # Conservative approach - if both APIs fail during potential market hours, assume closed
            print("🔒 Both APIs failed, defaulting to market closed for safety")
            return False


def should_trade_now(trader_name: str) -> bool:
    """Determine if a trader should trade based on their schedule"""
    # Always use Eastern Time regardless of system timezone
    now_et = get_eastern_time()
    hour = now_et.hour
    
    if trader_name == "flash":
        # Pavel trades 3x daily: 10 AM ET, 1 PM ET, 3:30 PM ET
        flash_hours = [10, 13, 15.5]  # All times in Eastern Time
        current_hour_decimal = hour + now_et.minute / 60
        
        # Check if we're within 30 minutes of any flash trading time
        for flash_hour in flash_hours:
            if abs(current_hour_decimal - flash_hour) <= 0.5:  # Within 30 minutes
                return True
        return False
    
    elif trader_name in ["warren", "camillo"]:
        # Warren and Camillo trade once daily around market close (3:30-4:00 PM ET)
        return 15.5 <= hour + now_et.minute / 60 <= 16.0
    
    return False


def should_rebalance_now(trader_name: str) -> bool:
    """Determine if a trader should rebalance based on their schedule"""
    # Always use Eastern Time regardless of system timezone
    now_et = get_eastern_time()
    hour = now_et.hour
    
    if trader_name == "flash":
        # Pavel rebalances 3x daily: 10:30 AM ET, 1:30 PM ET, 3:45 PM ET
        flash_rebalance_hours = [10.5, 13.5, 15.75]  # Offset from trading times
        current_hour_decimal = hour + now_et.minute / 60
        
        # Check if we're within 15 minutes of any flash rebalancing time
        for rebalance_hour in flash_rebalance_hours:
            if abs(current_hour_decimal - rebalance_hour) <= 0.25:  # Within 15 minutes
                return True
        return False
    
    elif trader_name in ["warren", "camillo"]:
        # Warren and Camillo rebalance once daily after market close (4:15-4:30 PM ET)
        return 16.25 <= hour + now_et.minute / 60 <= 16.5
    
    return False


class Trader:
    """Trader class that integrates with Market Intelligence and Technical Analysis agents"""
    
    def __init__(self, name: str):
        self.name = name.lower()
        self.account = get_trader_account(self.name)
        self.market_intelligence = MarketIntelligenceAgent()
        self.technical_analysis = TechnicalAnalysisAgent()
        self.openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Pavel gets a trading evaluator for discipline
        self.flash_evaluator = None
        
        # Set strategy based on trader personality
        self.strategy = self._get_trader_strategy()
        
    def _get_trader_strategy(self) -> str:
        """Get strategy string for this trader"""
        strategies = {
            "warren": warren_strategy,
            "camillo": camillo_strategy,
            "pavel": pavel_strategy
        }
        return strategies.get(self.name, "")
        
    async def setup_agents(self):
        """Initialize the agents"""
        await self.market_intelligence.setup()
        await self.technical_analysis.setup()
        
        # Setup Pavel evaluator if this is Pavel
        if self.name == "flash" and not self.flash_evaluator:
            self.flash_evaluator = await create_flash_evaluator()
        
    async def run_market_intelligence(self, query: str) -> str:
        """Run Market Intelligence Agent superstep"""
        try:
            result = await self.market_intelligence.run_superstep(
                message=query,
                success_criteria="Provide comprehensive market analysis relevant to my trading strategy",
                history=[],
                debug=False
            )
            
            # Extract the assistant's response from the result
            for msg in reversed(result):
                if msg["role"] == "assistant" and "Evaluator Feedback" not in msg["content"]:
                    return msg["content"]
            
            return "No market intelligence analysis available"
            
        except Exception as e:
            return f"Market intelligence error: {e}"
    
    async def run_technical_analysis(self, query: str) -> str:
        """Run Technical Analysis Agent superstep"""
        try:
            result = await self.technical_analysis.run_superstep(
                message=query,
                success_criteria="Provide actionable technical analysis with specific recommendations",
                history=[],
                debug=False
            )
            
            # Extract the assistant's response from the result
            for msg in reversed(result):
                if msg["role"] == "assistant" and "Evaluator Feedback" not in msg["content"]:
                    return msg["content"]
            
            return "No technical analysis available"
            
        except Exception as e:
            return f"Technical analysis error: {e}"
    
    def _create_trade_prompt(self, market_intel: str, tech_analysis: str, is_rebalancing: bool) -> str:
        """Create trading prompt based on analysis and trader personality"""
        action_type = "rebalancing" if is_rebalancing else "trading"
        account_report = self.account.report()
        current_holdings = list(self.account.holdings.keys())
        
        # Check if we need to build portfolio
        portfolio_building_mode = self.needs_portfolio_building()
        
        if portfolio_building_mode:
            prompt = f"""
{self.strategy}

🏗️ PORTFOLIO BUILDING MODE:
You currently have {len(current_holdings)} stocks but need {10 if self.name in ['warren', 'cathie'] else 3} stocks total.
Current holdings: {current_holdings}

MARKET INTELLIGENCE:
{market_intel}

TECHNICAL ANALYSIS:
{tech_analysis}

CURRENT ACCOUNT STATUS:
{account_report}

INSTRUCTIONS:
Find ONE new stock to buy that fits your strategy and you don't already own. Focus on diversification across different sectors.

Respond with a JSON object containing:
{{
    "decision": "BUY" or "HOLD",
    "symbol": "TICKER" (if BUY - must be different from current holdings),
    "quantity": number (if BUY),
    "rationale": "Why this stock adds value to your portfolio",
    "conviction": "HIGH" or "MEDIUM" or "LOW"
}}

You are building a portfolio - be proactive about finding quality opportunities!
"""
        else:
            prompt = f"""
{self.strategy}

CURRENT SITUATION:
You are now making a {action_type} decision.

MARKET INTELLIGENCE:
{market_intel}

TECHNICAL ANALYSIS:
{tech_analysis}

CURRENT ACCOUNT STATUS:
{account_report}

INSTRUCTIONS:
{"Examine your existing portfolio and decide if you need to rebalance positions based on your strategy." if is_rebalancing else "Look for new trading opportunities based on your strategy."}

Respond with a JSON object containing:
{{
    "decision": "BUY" or "SELL" or "HOLD",
    "symbol": "TICKER" (if BUY/SELL),
    "quantity": number (if BUY/SELL),
    "rationale": "Detailed explanation of your reasoning",
    "conviction": "HIGH" or "MEDIUM" or "LOW"
}}

Make only ONE decision per response. Focus on quality over quantity.
"""
        return prompt
    
    async def make_simple_trading_decision(self, is_rebalancing: bool = False) -> Dict:
        """Make a trading decision using research agents - no hard-coded picks"""
        try:
            # Force all traders to use their research agents and trading strategies
            return await self.make_trading_decision(is_rebalancing=is_rebalancing)
                
        except Exception as e:
            return {
                "decision": "HOLD",
                "rationale": f"Trading decision error: {e}",
                "conviction": "LOW"
            }

    async def make_trading_decision(self, is_rebalancing: bool = False) -> Dict:
        """Make trading decision based on agent analysis"""
        try:
            action_type = "rebalancing" if is_rebalancing else "trading"
            
            # Get analysis from both agents
            if is_rebalancing:
                market_query = f"Analyze market conditions affecting my current portfolio holdings: {list(self.account.holdings.keys())}"
                tech_query = f"Technical analysis of my current holdings for rebalancing: {list(self.account.holdings.keys())}"
            else:
                market_query = "Give me today's market briefing and identify new investment opportunities"
                tech_query = "Analyze current market movers and recommend stocks with strong technical setups"
            
            print(f"🔍 {self.name.title()}: Getting market intelligence...")
            try:
                market_intel = await asyncio.wait_for(
                    self.run_market_intelligence(market_query), 
                    timeout=60.0  # 60 second timeout
                )
                print(f"📈 {self.name.title()}: Market intel: {market_intel[:150]}...")
            except asyncio.TimeoutError:
                market_intel = f"Market intelligence timed out for {self.name}"
                print(f"⚠️ {self.name.title()}: Market intel timed out, using fallback")
            except Exception as e:
                market_intel = f"Market intelligence error: {str(e)}"
                print(f"❌ {self.name.title()}: Market intel error: {e}")
            
            print(f"🔍 {self.name.title()}: Getting technical analysis...")
            try:
                tech_analysis = await asyncio.wait_for(
                    self.run_technical_analysis(tech_query), 
                    timeout=60.0  # 60 second timeout
                )
                print(f"📊 {self.name.title()}: Tech analysis: {tech_analysis[:150]}...")
            except asyncio.TimeoutError:
                tech_analysis = f"Technical analysis timed out for {self.name}"
                print(f"⚠️ {self.name.title()}: Tech analysis timed out, using fallback")
            except Exception as e:
                tech_analysis = f"Technical analysis error: {str(e)}"
                print(f"❌ {self.name.title()}: Tech analysis error: {e}")
            
            # Create trading prompt
            prompt = self._create_trade_prompt(market_intel, tech_analysis, is_rebalancing)
            
            # Ensure LangSmith tracing for OpenAI calls
            try:
                from langsmith_config import ensure_langchain_tracing
                ensure_langchain_tracing()
            except Exception as e:
                print(f"⚠️ LangSmith tracing setup warning: {e}")
            
            # Get decision from LLM (this should be traced by LangSmith)
            response = await self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse decision
            try:
                content = response.choices[0].message.content.strip()
                
                # Handle JSON wrapped in markdown code blocks
                if "```json" in content:
                    import re
                    # Use regex to extract JSON block more reliably
                    json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(1).strip()
                    else:
                        # Fallback: find first JSON object
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            content = content[json_start:json_end]
                
                decision_data = json.loads(content)
                print(f"🎯 {self.name.title()}: Initial decision: {decision_data.get('decision')} {decision_data.get('symbol', 'N/A')}")
                
            except json.JSONDecodeError as e:
                print(f"⚠️ {self.name.title()}: JSON parsing failed: {e}")
                print(f"📝 Raw content: {response.choices[0].message.content}")
                # Fallback if JSON parsing fails
                decision_data = {
                    "decision": "HOLD",
                    "rationale": response.choices[0].message.content,
                    "conviction": "LOW"
                }
            
            # Pavel's decisions go through the evaluator
            if self.name == "flash" and self.flash_evaluator:
                print(f"🔍 {self.name.title()}: Sending decision to evaluator...")
                
                # Prepare trading context for evaluator
                trading_context = {
                    "current_time": get_eastern_time().isoformat(),
                    "holdings": dict(self.account.holdings),
                    "balance": self.account.balance,
                    "current_pnl": self.account.get_profit_loss(),
                    "recent_trades": self.account.list_transactions()[-10:],  # Last 10 trades
                    "market_intel": market_intel,
                    "tech_analysis": tech_analysis
                }
                
                # Get evaluator feedback
                try:
                    evaluation = await self.flash_evaluator.evaluate_trade_decision(
                        decision_data, trading_context
                    )
                    
                    if evaluation["approval_granted"]:
                        print(f"✅ {self.name.title()}: Evaluator APPROVED the trade")
                        decision_data["evaluator_feedback"] = evaluation["feedback_message"]
                    else:
                        print(f"❌ {self.name.title()}: Evaluator REJECTED the trade")
                        print(f"📝 Reason: {evaluation['feedback_message']}")
                        
                        # Use suggested modification or force HOLD
                        if evaluation.get("suggested_modification"):
                            decision_data = evaluation["suggested_modification"]
                            decision_data["evaluator_feedback"] = f"Modified by evaluator: {evaluation['feedback_message']}"
                            print(f"🔄 {self.name.title()}: Using evaluator's suggested modification")
                        else:
                            decision_data = {
                                "decision": "HOLD",
                                "rationale": f"Evaluator rejection: {evaluation['feedback_message']}",
                                "conviction": "LOW",
                                "evaluator_feedback": evaluation["feedback_message"]
                            }
                            
                except Exception as e:
                    print(f"❌ {self.name.title()}: Evaluator error: {e}")
                    decision_data["evaluator_feedback"] = f"Evaluator error: {e}"
            
            # Add metadata
            decision_data.update({
                "trader": self.name,
                "action_type": action_type,
                "timestamp": get_eastern_time().isoformat(),
                "market_intel": market_intel[:200] + "..." if len(market_intel) > 200 else market_intel,
                "tech_analysis": tech_analysis[:200] + "..." if len(tech_analysis) > 200 else tech_analysis
            })
            
            return decision_data
            
        except Exception as e:
            return {
                "trader": self.name,
                "action_type": action_type,
                "decision": "HOLD",
                "rationale": f"Error in decision making: {e}",
                "conviction": "LOW",
                "timestamp": datetime.now().isoformat()
            }
    
    async def execute_decision(self, decision: Dict) -> str:
        """Execute trading decision on the account"""
        print(f"🔍 {self.name.title()} execute_decision called with: {decision.get('decision')} {decision.get('symbol')} {decision.get('quantity')}")
        
        if decision["decision"] == "HOLD":
            return f"{self.name}: No trades executed - {decision['rationale']}"
        
        try:
            symbol = decision.get("symbol", "")
            quantity = decision.get("quantity", 0)
            rationale = decision.get("rationale", "")
            
            print(f"🔍 {self.name.title()}: Parsed - symbol={symbol}, quantity={quantity}, decision={decision['decision']}")
            
            if decision["decision"] == "BUY" and symbol and quantity > 0:
                # Check if we can afford the requested quantity
                from accounts import get_current_price
                current_price = get_current_price(symbol)
                max_affordable = int(self.account.balance // current_price) if current_price > 0 else 0
                
                if max_affordable == 0:
                    return f"{self.name}: Cannot afford any shares of {symbol} at ${current_price:.2f}"
                
                # Buy what we can afford, up to the requested quantity
                actual_quantity = min(quantity, max_affordable)
                result = self.account.buy_shares(symbol, actual_quantity, rationale)
                
                if actual_quantity < quantity:
                    return f"{self.name}: BUY executed (partial) - {result} (wanted {quantity}, bought {actual_quantity})"
                else:
                    return f"{self.name}: BUY executed - {result}"
                
            elif decision["decision"] == "SELL" and symbol and quantity > 0:
                result = self.account.sell_shares(symbol, quantity, rationale)
                return f"{self.name}: SELL executed - {result}"
            else:
                return f"{self.name}: Invalid decision parameters - {decision}"
                
        except Exception as e:
            return f"{self.name}: Trade execution failed - {e}"
    
    def needs_portfolio_building(self) -> bool:
        """Check if trader needs to build out their portfolio"""
        portfolio_targets = {
            "warren": 10,   # Warren likes a diversified value portfolio
            "camillo": 10,   # Camillo focuses on innovation themes across sectors  
            "flash": 3      # Pavel is a day trader with fewer positions
        }
        
        target_stocks = portfolio_targets.get(self.name, 5)
        current_stocks = len(self.account.holdings)
        
        return current_stocks < target_stocks

    async def run_portfolio_building_cycle(self) -> str:
        """Keep researching and buying stocks until portfolio target is reached"""
        try:
            print(f"🏗️ {self.name.title()}: PORTFOLIO BUILDING MODE - Need {10 if self.name in ['warren', 'cathie'] else 3} stocks, have {len(self.account.holdings)}")
            
            max_attempts = 3  # Try up to 3 times per cycle
            trades_made = 0
            
            for attempt in range(max_attempts):
                if not self.needs_portfolio_building():
                    break
                    
                print(f"🔍 {self.name.title()}: Portfolio building attempt {attempt + 1}/{max_attempts}")
                
                # Setup agents if not already done  
                await self.setup_agents()
                
                # Use the existing make_trading_decision - it now has portfolio building logic
                decision = await self.make_trading_decision(is_rebalancing=False)
                
                if decision.get('decision') == 'BUY':
                    result = await self.execute_decision(decision)
                    trades_made += 1
                    print(f"✅ {self.name.title()}: Portfolio building trade - {result}")
                else:
                    print(f"⏭️ {self.name.title()}: No buy decision this cycle")
                
                # Small delay between attempts
                await asyncio.sleep(1)
            
            portfolio_size = len(self.account.holdings)
            if self.needs_portfolio_building():
                return f"{self.name}: Portfolio building - made {trades_made} trades. Portfolio: {portfolio_size} stocks (still building)"
            else:
                return f"{self.name}: 🎉 Portfolio target reached! {portfolio_size} stocks. Made {trades_made} trades this cycle."
                
        except Exception as e:
            return f"{self.name}: Error during portfolio building - {e}"

    async def run(self) -> str:
        """Run one trading cycle for this trader"""
        try:
            # Check if any trader needs to build their portfolios
            if self.needs_portfolio_building():
                # Warren and Camillo get dedicated building cycles
                if self.name in ['warren', 'camillo']:
                    return await self.run_portfolio_building_cycle()
                
                # Pavel gets forced trading when portfolio building needed
                elif self.name == 'pavel':
                    print(f"🏗️ {self.name.title()}: Portfolio building needed - forcing trade")
                    is_rebalancing = should_rebalance_now(self.name)
                    should_trade = True  # Force trading for portfolio building
                    
                    action_type = "rebalancing" if is_rebalancing else "portfolio_building"
                    print(f"🔄 {self.name.title()} {action_type}...")
                    
                    # Setup agents if not already done
                    await self.setup_agents()
                    
                    # Make and execute decision
                    print(f"🧠 {self.name.title()} making decision...")
                    decision = await self.make_trading_decision(is_rebalancing)
                    print(f"📊 {self.name.title()} decision: {decision.get('decision', 'UNKNOWN')} - {decision.get('symbol', 'N/A')}")
                    
                    print(f"⚡ {self.name.title()} executing trade...")
                    result = await self.execute_decision(decision)
                    print(f"✅ {self.name.title()} result: {result}")
                    
                    return f"{self.name}: Portfolio building - {result}"
            
            # Normal trading/rebalancing logic for complete portfolios
            is_rebalancing = should_rebalance_now(self.name)
            should_trade = should_trade_now(self.name)
            
            if not (is_rebalancing or should_trade):
                return f"{self.name}: Not scheduled to trade/rebalance at this time"
            
            action_type = "rebalancing" if is_rebalancing else "trading"
            print(f"🔄 {self.name.title()} {action_type}...")
            
            # Setup agents if not already done
            await self.setup_agents()
            
            # Make and execute decision
            print(f"🧠 {self.name.title()} making decision...")
            decision = await self.make_trading_decision(is_rebalancing)
            print(f"📊 {self.name.title()} decision: {decision.get('decision', 'UNKNOWN')} - {decision.get('symbol', 'N/A')}")
            
            print(f"⚡ {self.name.title()} executing trade...")
            result = await self.execute_decision(decision)
            print(f"✅ {self.name.title()} result: {result}")
            
            return f"{self.name}: {action_type} completed - {result}"
            
        except Exception as e:
            return f"{self.name}: Error during trading - {e}"


def create_traders() -> List[Trader]:
    """Create all trader instances"""
    trader_names = ["warren", "camillo", "pavel"]
    return [Trader(name) for name in trader_names]


async def run_trading_cycle():
    """Run one complete trading cycle for all traders"""
    if not is_market_open() and not RUN_EVEN_WHEN_MARKET_IS_CLOSED:
        print("🔒 Market is closed, skipping trading cycle")
        return
    
    print(f"🚀 Starting trading cycle at {get_eastern_time().strftime('%Y-%m-%d %H:%M:%S ET')}")
    
    # Create all traders
    traders = create_traders()
    
    # Update portfolio value time series for all traders (for graph accuracy)
    print("📊 Updating portfolio values for performance tracking...")
    for trader in traders:
        try:
            trader.account.update_portfolio_value_series()
        except Exception as e:
            print(f"⚠️ Error updating portfolio value for {trader.name}: {e}")
    
    # Run all traders in parallel (restored from before sequential fix)
    print("🤖 Starting all traders in parallel...")
    results = await asyncio.gather(*[trader.run() for trader in traders])
    
    # Print results
    for result in results:
        if "Not scheduled" not in result:  # Only print active trading
            print(f"✅ {result}")


async def run_trading_floor():
    """Main trading floor loop"""
    print(f"🏢 Trading Floor started - running every {RUN_EVERY_N_MINUTES} minutes")
    print(f"📅 Schedule:")
    print(f"   Warren & Camillo: Daily trading (3:30-4:00 PM), Daily rebalancing (4:15-4:30 PM)")
    print(f"   Pavel: 3x daily trading (10 AM, 1 PM, 3:30 PM), 3x daily rebalancing (10:30 AM, 1:30 PM, 3:45 PM)")
    
    while True:
        try:
            await run_trading_cycle()
        except Exception as e:
            print(f"❌ Error in trading cycle: {e}")
        
        print(f"💤 Sleeping for {RUN_EVERY_N_MINUTES} minutes...")
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    # Test the trading floor
    print("🧪 Testing Trading Floor...")
    
    # Test market hours
    if is_market_open():
        print("✅ Market is open - ready for trading!")
    else:
        print("🔒 Market is closed")
    
    # Test trader schedules
    traders = create_traders()
    for trader in traders:
        should_trade = should_trade_now(trader.name)
        should_rebalance = should_rebalance_now(trader.name)
        print(f"{trader.name.title()}: Trade={should_trade}, Rebalance={should_rebalance}")
    
    print("\n🚀 Starting trading floor (Ctrl+C to stop)...")
    try:
        asyncio.run(run_trading_floor())
    except KeyboardInterrupt:
        print("\n🛑 Trading floor stopped")