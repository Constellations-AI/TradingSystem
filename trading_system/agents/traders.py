"""
Trading Agents - Warren Buffett, Chris Camillo, and Pavel Krejci (Day Trader)
Each agent has distinct personality, strategy, and decision-making process
"""
import os
from typing import Dict, List, Optional
from datetime import datetime
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

from agents.market_intelligence_agent import MarketIntelligenceAgent
from agents.technical_analysis_agent import TechnicalAnalysisAgent

# Load environment variables
load_dotenv(override=True)


class TraderPersonality:
    """Base class for trader personalities"""
    
    def __init__(self, name: str):
        self.name = name
        self.openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.market_intelligence = MarketIntelligenceAgent()
        self.technical_analysis = TechnicalAnalysisAgent()
        
    async def make_trading_decision(self, ticker: str) -> Dict:
        """Base method for making trading decisions"""
        raise NotImplementedError("Subclasses must implement make_trading_decision")
    
    async def get_daily_briefing(self) -> Dict:
        """Get personalized daily briefing"""
        result = await self.market_intelligence.analyze("Give me my daily briefing", self.name.lower())
        if result['status'] == 'success':
            return {
                'trader_personality': self.name.lower(),
                'timestamp': result['timestamp'],
                'ai_briefing': result['analysis']
            }
        else:
            return {'error': result.get('error', 'Unknown error')}
    
    async def research_stock(self, ticker: str) -> Dict:
        """Conduct deep research on a specific stock"""
        result = await self.market_intelligence.analyze(f"Research {ticker} stock for potential investment", self.name.lower())
        if result['status'] == 'success':
            return {
                'ticker': ticker,
                'ai_research_report': result['analysis'],
                'timestamp': result['timestamp']
            }
        else:
            return {'error': result.get('error', 'Unknown error')}


class WarrenBuffettAgent(TraderPersonality):
    """
    Warren Buffett - Value Investor
    Focus: Long-term value, fundamentals, economic moats, patient investing
    """
    
    def __init__(self):
        super().__init__("Warren")
        self.style = "Value Investing"
        self.time_horizon = "Long-term (5+ years)"
        self.risk_tolerance = "Conservative"
        
    async def make_trading_decision(self, ticker: str, portfolio_context: Dict = None) -> Dict:
        """Warren's value-focused trading decision"""
        try:
            # Get market intelligence and technical analysis
            market_result = await self.market_intelligence.analyze("Give me my daily briefing", "warren")
            market_briefing = market_result.get('analysis', 'No briefing available') if market_result['status'] == 'success' else 'Briefing unavailable'
            tech_analysis = await self.technical_analysis.analyze_ticker(ticker, timeframe="1D", days=200)
            
            # Warren's decision-making prompt
            decision_prompt = f"""
            You are Warren Buffett making an investment decision about {ticker}.
            
            Your Investment Philosophy:
            - Buy wonderful companies at reasonable prices
            - Focus on businesses with economic moats
            - Long-term value creation (5+ year holding period)
            - Price is what you pay, value is what you get
            - Be fearful when others are greedy, greedy when others are fearful
            - Only invest in businesses you understand
            
            Market Intelligence:
            {market_briefing}
            
            Technical Analysis:
            - Current Price: ${tech_analysis.get('current_price', 'N/A')}
            - Price Change: {tech_analysis.get('price_change', {}).get('percent', 'N/A')}%
            - Trading Signals: {tech_analysis.get('trading_signals', {}).get('strength', 'neutral')}
            
            Current Portfolio Context:
            {json.dumps(portfolio_context or {}, indent=2)}
            
            Make a decision following Warren's approach:
            1. Assess the business quality and competitive moat
            2. Evaluate if the price represents good value
            3. Consider long-term prospects (ignore short-term noise)
            4. Decide: BUY, SELL, or HOLD with rationale
            5. If buying, suggest position size (% of portfolio)
            
            Format your response as:
            {{
                "decision": "BUY/SELL/HOLD",
                "conviction": "HIGH/MEDIUM/LOW",
                "position_size_percent": 0-20,
                "rationale": "Detailed explanation of reasoning",
                "key_factors": ["factor1", "factor2", "factor3"],
                "timeline": "Expected holding period",
                "risk_assessment": "Key risks to monitor"
            }}
            """
            
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are Warren Buffett, the legendary value investor. Make decisions based on fundamental value, business quality, and long-term thinking."},
                    {"role": "user", "content": decision_prompt}
                ],
                temperature=0.2,  # Low temperature for consistent, conservative decisions
                max_tokens=800
            )
            
            # Parse the JSON response
            try:
                decision_data = json.loads(response.choices[0].message.content)
            except:
                # Fallback if JSON parsing fails
                decision_data = {
                    "decision": "HOLD",
                    "conviction": "LOW",
                    "rationale": response.choices[0].message.content,
                    "error": "JSON parsing failed"
                }
            
            return {
                "trader": "Warren Buffett",
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "decision_data": decision_data,
                "market_context": market_briefing,
                "technical_context": tech_analysis
            }
            
        except Exception as e:
            return {"error": f"Warren's decision failed: {e}"}


class ChrisCamilloAgent(TraderPersonality):
    """
    Chris Camillo - Social Arbitrage Investor
    Focus: Cultural signals, consumer sentiment, viral narratives
    """
    
    def __init__(self):
        super().__init__("Camillo")
        self.style = "Social Arbitrage"
        self.time_horizon = "Short to Medium-term (days to months)"
        self.risk_tolerance = "Moderate-High"
        
    async def make_trading_decision(self, ticker: str, portfolio_context: Dict = None) -> Dict:
        """Chris Camillo's social arbitrage trading decision"""
        try:
            # Get market intelligence and technical analysis
            market_result = await self.market_intelligence.analyze("Give me my daily briefing", "camillo")
            market_briefing = market_result.get('analysis', 'No briefing available') if market_result['status'] == 'success' else 'Briefing unavailable'
            tech_analysis = await self.technical_analysis.analyze_ticker(ticker, timeframe="1D", days=90)
            
            # Chris Camillo's decision-making prompt
            decision_prompt = f"""
            You are Chris Camillo making an investment decision about {ticker}.
            
            Your Investment Philosophy:
            - Invest based on emerging trends before Wall Street catches on
            - Use real-time sentiment and behavior to predict market reactions
            - Focus on qualitative edge from social, cultural, and retail data
            - Trade fast-moving narratives with asymmetric potential
            - Use unconventional data: social media buzz, Google Trends, influencer activity
            - Target overlooked companies benefiting from emerging behaviors
            
            Market Intelligence:
            {market_briefing}
            
            Technical Analysis:
            - Current Price: ${tech_analysis.get('current_price', 'N/A')}
            - Price Change: {tech_analysis.get('price_change', {}).get('percent', 'N/A')}%
            - Trading Signals: {tech_analysis.get('trading_signals', {}).get('strength', 'neutral')}
            - Volume Trend: {tech_analysis.get('volume_analysis', {}).get('volume_trend', 'unknown')}
            
            Current Portfolio Context:
            {json.dumps(portfolio_context or {}, indent=2)}
            
            Make a decision following Chris Camillo's approach:
            1. Identify emerging cultural trends and consumer sentiment
            2. Assess social media buzz and viral potential
            3. Evaluate timing before mainstream adoption
            4. Consider narrative strength and influencer activity
            5. Decide: BUY, SELL, or HOLD based on trend momentum
            6. If buying, suggest position size (moderate due to trend risk)
            
            Format your response as:
            {{
                "decision": "BUY/SELL/HOLD",
                "conviction": "HIGH/MEDIUM/LOW",
                "position_size_percent": 0-15,
                "rationale": "Social arbitrage explanation",
                "key_factors": ["cultural trend", "social sentiment", "viral potential"],
                "timeline": "Expected timeframe for thesis to play out",
                "risk_assessment": "Technology and execution risks"
            }}
            """
            
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are Chris Camillo, focused on social arbitrage investing. Make decisions based on cultural signals, consumer sentiment, and emerging trends."},
                    {"role": "user", "content": decision_prompt}
                ],
                temperature=0.4,  # Slightly higher for innovative thinking
                max_tokens=800
            )
            
            # Parse the JSON response
            try:
                decision_data = json.loads(response.choices[0].message.content)
            except:
                decision_data = {
                    "decision": "HOLD",
                    "conviction": "LOW",
                    "rationale": response.choices[0].message.content,
                    "error": "JSON parsing failed"
                }
            
            return {
                "trader": "Chris Camillo",
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "decision_data": decision_data,
                "market_context": market_briefing,
                "technical_context": tech_analysis
            }
            
        except Exception as e:
            return {"error": f"Chris Camillo's decision failed: {e}"}


class PavelTraderAgent(TraderPersonality):
    """
    Pavel Krejci - Day Trader
    Focus: Momentum, technicals, quick profits, high frequency trading
    """
    
    def __init__(self):
        super().__init__("Pavel")
        self.style = "Day Trading"
        self.time_horizon = "Intraday (minutes to hours)"
        self.risk_tolerance = "High Frequency"
        
    async def make_trading_decision(self, ticker: str, portfolio_context: Dict = None) -> Dict:
        """Pavel's momentum-focused trading decision"""
        try:
            # Get market intelligence and detailed technical analysis
            market_result = await self.market_intelligence.analyze("Give me my daily briefing", "pavel")
            market_briefing = market_result.get('analysis', 'No briefing available') if market_result['status'] == 'success' else 'Briefing unavailable'
            tech_analysis = await self.technical_analysis.analyze_ticker(ticker, timeframe="1D", days=30)
            tech_recommendation = await self.technical_analysis.get_trading_recommendation(ticker, "pavel")
            
            # Pavel's decision-making prompt
            decision_prompt = f"""
            You are Pavel Krejci, an expert day trader making a quick trading decision about {ticker}.
            
            Your Trading Philosophy:
            - Momentum-based trading with tight risk management
            - Technical analysis over fundamentals
            - Quick entries and exits (minutes to hours)
            - Focus on volume, volatility, and chart patterns
            - Risk 1-2% per trade, target 2:1 or 3:1 reward/risk
            - Trade the trend, cut losses quickly
            
            Market Intelligence (for context):
            {market_briefing}
            
            Technical Analysis:
            - Current Price: ${tech_analysis.get('current_price', 'N/A')}
            - Price Change: {tech_analysis.get('price_change', {}).get('percent', 'N/A')}%
            - RSI: {tech_analysis.get('technical_indicators', {}).get('rsi', 'N/A')}
            - Trading Signals: {tech_analysis.get('trading_signals', {})}
            - Volume Analysis: {tech_analysis.get('volume_analysis', {})}
            - Support/Resistance: {tech_analysis.get('support_resistance', {})}
            
            AI Technical Recommendation:
            {tech_recommendation.get('recommendation', 'No recommendation available')}
            
            Current Portfolio Context:
            {json.dumps(portfolio_context or {}, indent=2)}
            
            Make a decision following Pavel's approach:
            1. Identify momentum and trend direction
            2. Check volume confirmation
            3. Find entry/exit levels with tight stops
            4. Assess risk/reward ratio
            5. Decide: BUY, SELL, or HOLD with specific levels
            6. Position size based on volatility and stop distance
            
            Format your response as:
            {{
                "decision": "BUY/SELL/HOLD",
                "conviction": "HIGH/MEDIUM/LOW",
                "position_size_percent": 1-5,
                "entry_price": "Specific entry level",
                "stop_loss": "Specific stop level",
                "target_price": "Specific target level",
                "rationale": "Technical and momentum analysis",
                "key_factors": ["momentum", "volume", "technical levels"],
                "timeline": "Expected trade duration",
                "risk_reward_ratio": "X:1 ratio"
            }}
            """
            
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are Pavel Krejci, an expert day trader. Make decisions based on technical analysis, momentum, and precise risk management."},
                    {"role": "user", "content": decision_prompt}
                ],
                temperature=0.6,  # Higher temperature for quick, adaptive decisions
                max_tokens=800
            )
            
            # Parse the JSON response
            try:
                decision_data = json.loads(response.choices[0].message.content)
            except:
                decision_data = {
                    "decision": "HOLD",
                    "conviction": "LOW",
                    "rationale": response.choices[0].message.content,
                    "error": "JSON parsing failed"
                }
            
            return {
                "trader": "Pavel Krejci",
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "decision_data": decision_data,
                "market_context": market_briefing,
                "technical_context": tech_analysis,
                "technical_recommendation": tech_recommendation
            }
            
        except Exception as e:
            return {"error": f"Pavel's decision failed: {e}"}


# Factory function to create traders
def create_trader(personality: str) -> TraderPersonality:
    """Create a trader instance based on personality"""
    personalities = {
        'warren': WarrenBuffettAgent,
        'camillo': ChrisCamilloAgent,
        'pavel': PavelTraderAgent
    }
    
    trader_class = personalities.get(personality.lower())
    if not trader_class:
        raise ValueError(f"Unknown personality: {personality}")
    
    return trader_class()


# Convenience function to get all traders
def get_all_traders() -> Dict[str, TraderPersonality]:
    """Get instances of all trader personalities"""
    return {
        'warren': WarrenBuffettAgent(),
        'camillo': ChrisCamilloAgent(),
        'pavel': PavelTraderAgent()
    }