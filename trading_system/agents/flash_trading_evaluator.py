"""
Flash Trading Evaluator Agent

An LLM-based evaluator that reviews Flash's trading decisions to ensure compliance
with day trading rules, risk management, and strategy discipline using LangGraph.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Annotated

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from database import Database


class FlashEvaluationState(TypedDict):
    """State for Flash trading evaluation process"""
    messages: Annotated[List[Any], add_messages]
    trading_context: Dict  # Current positions, market conditions, recent trades
    proposed_decision: Dict  # Flash's proposed trading decision
    evaluation_complete: bool
    approval_granted: bool
    feedback_message: str
    suggested_modification: Optional[Dict]


class TradingEvaluationResult(BaseModel):
    """Structured output for Flash trading evaluation"""
    approval_granted: bool = Field(description="Whether to approve Flash's proposed trade")
    confidence_level: str = Field(description="HIGH, MEDIUM, or LOW confidence in evaluation")
    feedback_message: str = Field(description="Detailed feedback on the trading decision")
    risk_assessment: str = Field(description="Assessment of risk level: LOW, MEDIUM, HIGH, EXTREME")
    reasoning: str = Field(description="Detailed reasoning for the evaluation decision")
    
    class Config:
        extra = "forbid"


class FlashTradingEvaluatorTools:
    """Tools for evaluating Flash's trading decisions"""
    
    def __init__(self, session_id: str, db: Database):
        self.session_id = session_id
        self.db = db
    
    def get_tools(self):
        """Return all tools for Flash trading evaluation"""
        return [
            self.analyze_current_positions,
            self.check_day_trading_rules,
            self.assess_risk_management,
            self.evaluate_market_momentum,
            self.check_position_sizing
        ]
    
    @tool
    def analyze_current_positions(self, trader_data: str) -> str:
        """
        Analyze Flash's current positions for overlap, concentration risk, and strategy alignment
        
        Args:
            trader_data: JSON string containing current holdings, balance, and recent trades
        """
        try:
            data = json.loads(trader_data)
            holdings = data.get('holdings', {})
            balance = data.get('balance', 0)
            recent_trades = data.get('recent_trades', [])
            
            analysis = []
            
            # Position concentration analysis
            total_positions = len(holdings)
            if total_positions > 3:
                analysis.append("⚠️ CONCENTRATION RISK: Flash holds more than 3 positions, violating day trading focus")
            
            # Symbol overlap analysis
            symbols_traded_today = set()
            for trade in recent_trades:
                if trade.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d')):
                    symbols_traded_today.add(trade.get('symbol', ''))
            
            current_symbols = set(holdings.keys())
            overlapping_symbols = current_symbols.intersection(symbols_traded_today)
            
            if overlapping_symbols:
                analysis.append(f"📈 SYMBOL OVERLAP: Already traded today: {', '.join(overlapping_symbols)}")
            
            # Cash utilization
            portfolio_value = balance + sum([qty * 100 for qty in holdings.values()])  # Rough estimate
            cash_ratio = balance / portfolio_value if portfolio_value > 0 else 1
            
            if cash_ratio < 0.2:
                analysis.append("💰 LOW CASH: Less than 20% cash remaining for new opportunities")
            
            return "POSITION ANALYSIS:\n" + "\n".join(analysis) if analysis else "✅ Position analysis looks good"
            
        except Exception as e:
            return f"Error analyzing positions: {e}"
    
    @tool  
    def check_day_trading_rules(self, market_time_data: str) -> str:
        """
        Check compliance with Flash's day trading rules including position closure timing
        
        Args:
            market_time_data: JSON string with current market time and proposed trade type
        """
        try:
            from trading_floor import get_eastern_time, is_market_open
            
            data = json.loads(market_time_data)
            proposed_action = data.get('proposed_action', '')
            
            now_et = get_eastern_time()
            current_hour_decimal = now_et.hour + now_et.minute / 60
            
            violations = []
            
            # Market close proximity check (Flash must close positions by market close)
            if current_hour_decimal >= 15.75:  # After 3:45 PM ET
                if proposed_action == 'BUY':
                    violations.append("🚨 RULE VIOLATION: No new BUY orders after 3:45 PM - Flash must close positions!")
                elif proposed_action == 'HOLD':
                    violations.append("🚨 RULE VIOLATION: No HOLD decisions after 3:45 PM - must SELL to close positions!")
            
            # Market hours compliance
            if not is_market_open():
                violations.append("🚨 MARKET CLOSED: Cannot execute day trades outside market hours")
            
            # Day trading window optimal times
            optimal_times = [
                (9.5, 10.5),   # Market open volatility
                (10.0, 10.5),  # 10 AM Flash trading window
                (13.0, 13.5),  # 1 PM Flash trading window  
                (15.5, 16.0)   # 3:30 PM Flash trading window
            ]
            
            in_optimal_window = any(start <= current_hour_decimal <= end for start, end in optimal_times)
            if not in_optimal_window:
                violations.append(f"⚠️ TIMING: Outside optimal Flash trading windows (current: {now_et.strftime('%H:%M')} ET)")
            
            return "DAY TRADING RULES:\n" + "\n".join(violations) if violations else "✅ Day trading rules compliance OK"
            
        except Exception as e:
            return f"Error checking day trading rules: {e}"
    
    @tool
    def assess_risk_management(self, trade_data: str) -> str:
        """
        Assess if the proposed trade follows Flash's strict risk management rules
        
        Args:
            trade_data: JSON string with proposed trade details and current account status
        """
        try:
            data = json.loads(trade_data)
            proposed_trade = data.get('proposed_trade', {})
            account_balance = data.get('account_balance', 0)
            current_pnl = data.get('current_pnl', 0)
            
            risk_issues = []
            
            # Daily loss limit check (-2% of account value)
            daily_loss_limit = -200  # -2% of $10,000 starting balance
            if current_pnl < daily_loss_limit:
                risk_issues.append(f"🚨 DAILY LOSS LIMIT EXCEEDED: {current_pnl:.2f} < {daily_loss_limit}")
            
            # Position sizing check (max 1% account risk per trade)
            if proposed_trade.get('decision') == 'BUY':
                quantity = proposed_trade.get('quantity', 0)
                symbol = proposed_trade.get('symbol', '')
                estimated_price = 100  # Rough estimate - would need real price
                trade_value = quantity * estimated_price
                max_position_size = account_balance * 0.1  # 10% max position size for day trading
                
                if trade_value > max_position_size:
                    risk_issues.append(f"⚠️ POSITION SIZE: Trade value ${trade_value:.2f} exceeds 10% of account")
            
            # Stop loss verification
            if 'stop_loss' not in proposed_trade or not proposed_trade.get('stop_loss'):
                risk_issues.append("🚨 NO STOP LOSS: Flash requires strict stop losses on all positions")
            
            return "RISK MANAGEMENT:\n" + "\n".join(risk_issues) if risk_issues else "✅ Risk management compliance OK"
            
        except Exception as e:
            return f"Error assessing risk management: {e}"
    
    @tool
    def evaluate_market_momentum(self, market_data: str) -> str:
        """
        Evaluate if current market conditions support Flash's momentum trading strategy
        
        Args:
            market_data: JSON string with market conditions and technical indicators
        """
        try:
            data = json.loads(market_data)
            symbol = data.get('symbol', '')
            
            # Placeholder for momentum evaluation
            # In real implementation, would check:
            # - Volume spikes
            # - Price momentum
            # - Technical breakouts
            # - News catalysts
            
            momentum_factors = []
            
            # Volume check (placeholder)
            volume_spike = data.get('volume_spike', False)
            if not volume_spike:
                momentum_factors.append("⚠️ LOW VOLUME: No significant volume spike detected for momentum play")
            
            # Price momentum check (placeholder)
            price_momentum = data.get('price_momentum', 'neutral')
            if price_momentum == 'weak':
                momentum_factors.append("⚠️ WEAK MOMENTUM: Price action not supporting Flash's momentum strategy")
            
            return "MOMENTUM ANALYSIS:\n" + "\n".join(momentum_factors) if momentum_factors else "✅ Market momentum supports Flash strategy"
            
        except Exception as e:
            return f"Error evaluating market momentum: {e}"
    
    @tool
    def check_position_sizing(self, sizing_data: str) -> str:
        """
        Verify position sizing follows Flash's volatility-based approach
        
        Args:
            sizing_data: JSON string with trade size, account value, and symbol volatility
        """
        try:
            data = json.loads(sizing_data)
            proposed_quantity = data.get('quantity', 0)
            account_value = data.get('account_value', 10000)
            symbol_volatility = data.get('volatility', 'medium')
            
            sizing_issues = []
            
            # Base position sizing (Flash should use smaller sizes for higher volatility)
            volatility_multipliers = {'low': 1.0, 'medium': 0.7, 'high': 0.5}
            max_position_pct = 0.1 * volatility_multipliers.get(symbol_volatility, 0.7)  # 10% base, adjusted for volatility
            
            estimated_trade_value = proposed_quantity * 100  # Rough estimate
            max_trade_value = account_value * max_position_pct
            
            if estimated_trade_value > max_trade_value:
                sizing_issues.append(f"⚠️ OVERSIZED: Position ${estimated_trade_value:.2f} exceeds volatility-adjusted limit ${max_trade_value:.2f}")
            
            return "POSITION SIZING:\n" + "\n".join(sizing_issues) if sizing_issues else "✅ Position sizing appropriate for volatility"
            
        except Exception as e:
            return f"Error checking position sizing: {e}"


class FlashTradingEvaluator:
    """
    LLM-based evaluator for Flash's trading decisions using LangGraph architecture
    """
    
    def __init__(self, db_path: str = "trading_system.db"):
        self.flash_evaluator_llm = None
        self.flash_evaluator_llm_with_tools = None
        self.tools = None
        self.graph = None
        self.evaluator_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.db = Database(db_path)
    
    async def setup(self):
        """Initialize the Flash trading evaluator"""
        import os
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        # Initialize LLMs
        self.flash_evaluator_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,  # Low temperature for consistent evaluation
            max_tokens=1000,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Build the evaluation graph
        await self._build_graph()
    
    def _flash_evaluation_tools(self, session_id: str):
        """Create Flash-specific evaluation tools for a session"""
        tools_instance = FlashTradingEvaluatorTools(session_id, self.db)
        return tools_instance.get_tools()
    
    async def flash_evaluator_node(self, state: FlashEvaluationState):
        """Main evaluation node for Flash trading decisions"""
        try:
            # Create session-specific tools
            session_id = str(uuid.uuid4())
            tools = self._flash_evaluation_tools(session_id)
            
            # Bind tools to LLM
            self.flash_evaluator_llm_with_tools = self.flash_evaluator_llm.bind_tools(tools)
            
            # Create evaluation prompt
            system_prompt = """You are Flash's trading supervisor and risk manager. Your job is to evaluate Flash's proposed trading decisions against his strict day trading rules and risk management principles.

FLASH'S CORE RULES (NEVER VIOLATE):
1. No overnight positions - close everything before market close (4 PM ET)
2. Strict stop losses at -0.5% to -1% maximum  
3. Maximum 1% account risk per trade
4. Daily loss limit: -2% of account value
5. Focus on high-volume stocks with clear momentum
6. Position sizing based on volatility

EVALUATION PROCESS:
1. Use the provided tools to analyze the trading context
2. Check compliance with Flash's day trading rules
3. Assess risk management and position sizing
4. Evaluate market momentum and timing
5. Provide clear approval or rejection with detailed reasoning

CRITICAL: If it's after 3:45 PM ET, Flash should ONLY be SELLING to close positions. No new BUY orders or HOLD decisions.

Be strict but fair. Allow reasonable trading decisions that align with Flash's aggressive day trading style while preventing rule violations that could lead to significant losses."""
            
            # Get the latest messages
            messages = state.get("messages", [])
            
            # Add system prompt as first message if not present
            if not messages or not any(isinstance(msg, AIMessage) and "trading supervisor" in str(msg.content) for msg in messages):
                messages = [AIMessage(content=system_prompt)] + messages
            
            # Invoke LLM with tools
            response = await self.flash_evaluator_llm_with_tools.ainvoke(messages)
            
            # Update state with response
            updated_state = {
                **state,
                "messages": messages + [response]
            }
            
            return updated_state
            
        except Exception as e:
            error_msg = f"Flash evaluator error: {e}"
            return {
                **state,
                "messages": state.get("messages", []) + [AIMessage(content=error_msg)],
                "evaluation_complete": True,
                "approval_granted": False,
                "feedback_message": error_msg
            }
    
    def flash_evaluation_router(self, state: FlashEvaluationState):
        """Route based on whether tools were called"""
        messages = state.get("messages", [])
        if not messages:
            return "flash_evaluator"
        
        last_message = messages[-1]
        
        # If the last message contains tool calls, go to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        
        # If we have tool results, go to final evaluation
        tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
        if tool_messages:
            return "final_evaluation"
        
        # If no tool calls and no tool results, end evaluation
        return "final_evaluation"
    
    async def final_evaluation_node(self, state: FlashEvaluationState):
        """Final evaluation decision with structured output"""
        try:
            # Create structured output LLM
            structured_llm = self.flash_evaluator_llm.with_structured_output(TradingEvaluationResult)
            
            # Create evaluation prompt with tool results
            messages = state.get("messages", [])
            tool_results = [msg.content for msg in messages if isinstance(msg, ToolMessage)]
            
            evaluation_prompt = f"""
Based on the tool analysis results below, make your final evaluation of Flash's proposed trading decision.

TOOL ANALYSIS RESULTS:
{chr(10).join(tool_results)}

PROPOSED TRADE:
{json.dumps(state.get('proposed_decision', {}), indent=2)}

TRADING CONTEXT:
{json.dumps(state.get('trading_context', {}), indent=2)}

Make your final decision on whether to approve Flash's trade. Be decisive and provide clear reasoning.
"""
            
            # Get structured evaluation
            evaluation_result = await structured_llm.ainvoke([HumanMessage(content=evaluation_prompt)])
            
            # Update state with final evaluation
            return {
                **state,
                "evaluation_complete": True,
                "approval_granted": evaluation_result.approval_granted,
                "feedback_message": evaluation_result.feedback_message,
                "suggested_modification": None,  # Remove this field for now
                "messages": messages + [AIMessage(content=f"EVALUATION COMPLETE: {evaluation_result.feedback_message}")]
            }
            
        except Exception as e:
            error_msg = f"Final evaluation error: {e}"
            return {
                **state,
                "evaluation_complete": True,
                "approval_granted": False,
                "feedback_message": error_msg,
                "messages": state.get("messages", []) + [AIMessage(content=error_msg)]
            }
    
    async def _build_graph(self):
        """Build the Flash trading evaluation graph"""
        # Define the state graph
        workflow = StateGraph(FlashEvaluationState)
        
        # Add nodes
        workflow.add_node("flash_evaluator", self.flash_evaluator_node)
        workflow.add_node("tools", ToolNode(self._flash_evaluation_tools("default")))
        workflow.add_node("final_evaluation", self.final_evaluation_node)
        
        # Set entry point
        workflow.set_entry_point("flash_evaluator")
        
        # Conditional routing from flash_evaluator
        workflow.add_conditional_edges(
            "flash_evaluator",
            self.flash_evaluation_router,
            {
                "tools": "tools", 
                "final_evaluation": "final_evaluation"
            }
        )
        
        # From tools, go directly to final evaluation (no loop back)
        workflow.add_edge("tools", "final_evaluation")
        
        # Final evaluation ends the process
        workflow.add_edge("final_evaluation", "__end__")
        
        # Compile the graph
        self.graph = workflow.compile(checkpointer=self.memory)
    
    async def evaluate_trade_decision(self, 
                                    proposed_decision: Dict,
                                    trading_context: Dict,
                                    session_id: str = None) -> Dict:
        """
        Evaluate Flash's proposed trading decision
        
        Args:
            proposed_decision: Flash's proposed trade (decision, symbol, quantity, etc.)
            trading_context: Current account state, market conditions, recent trades
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Dict with approval_granted, feedback_message, and suggested_modification
        """
        if not self.graph:
            await self.setup()
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        try:
            # Create initial state
            initial_state = {
                "messages": [
                    HumanMessage(content=f"""
Please evaluate this trading decision for Flash:

PROPOSED DECISION:
{json.dumps(proposed_decision, indent=2)}

CURRENT TRADING CONTEXT:
{json.dumps(trading_context, indent=2)}

Use your tools to thoroughly analyze this decision against Flash's day trading rules and risk management principles.
""")
                ],
                "trading_context": trading_context,
                "proposed_decision": proposed_decision,
                "evaluation_complete": False,
                "approval_granted": False,
                "feedback_message": "",
                "suggested_modification": None
            }
            
            # Run the evaluation process with increased recursion limit
            config = {
                "configurable": {"thread_id": session_id},
                "recursion_limit": 50
            }
            final_state = await self.graph.ainvoke(initial_state, config)
            
            # Return evaluation results
            return {
                "approval_granted": final_state.get("approval_granted", False),
                "feedback_message": final_state.get("feedback_message", "Evaluation failed"),
                "suggested_modification": final_state.get("suggested_modification"),
                "session_id": session_id
            }
            
        except Exception as e:
            return {
                "approval_granted": False,
                "feedback_message": f"Flash evaluator system error: {e}",
                "suggested_modification": None,
                "session_id": session_id
            }


# Factory function for easy integration
async def create_flash_evaluator(db_path: str = "trading_system.db") -> FlashTradingEvaluator:
    """Create and setup a Flash trading evaluator"""
    evaluator = FlashTradingEvaluator(db_path)
    await evaluator.setup()
    return evaluator


if __name__ == "__main__":
    # Test the Flash trading evaluator
    async def test_evaluator():
        print("🧪 Testing Flash Trading Evaluator...")
        
        evaluator = await create_flash_evaluator()
        
        # Test case: Bad decision after market hours
        test_decision = {
            "decision": "BUY",
            "symbol": "AAPL", 
            "quantity": 100,
            "rationale": "Strong momentum play"
        }
        
        test_context = {
            "current_time": "2025-07-24 15:50:00",  # After 3:45 PM
            "holdings": {"NVDA": 50},
            "balance": 5000,
            "current_pnl": -150
        }
        
        result = await evaluator.evaluate_trade_decision(test_decision, test_context)
        
        print(f"Approval granted: {result['approval_granted']}")
        print(f"Feedback: {result['feedback_message']}")
        
        print("✅ Flash evaluator test complete")
    
    asyncio.run(test_evaluator())