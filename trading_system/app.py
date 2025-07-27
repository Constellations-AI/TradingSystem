"""
Main Streamlit Trading System Interface
Clean, focused interface with market intelligence, technical analysis, and trading decisions
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import asyncio
from datetime import datetime
import json

# Import our agents and models
from trader_system_archive.market_intelligence_agent import MarketIntelligenceAgent
from agents.technical_analysis import TechnicalAnalysisAgent
from agents.traders import get_all_traders, create_trader
from models.portfolio import Portfolio

# Page configuration
st.set_page_config(
    page_title="AI Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = Portfolio()

if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = 'AAPL'

# Helper function for async operations in Streamlit
def run_async(coro):
    """Run async function in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# Sidebar
st.sidebar.title("🤖 AI Trading System")
st.sidebar.markdown("---")

# Ticker selection
st.session_state.selected_ticker = st.sidebar.text_input(
    "Stock Ticker", 
    value=st.session_state.selected_ticker,
    help="Enter stock symbol (e.g., AAPL, TSLA, MSFT)"
).upper()

# Trader selection
selected_traders = st.sidebar.multiselect(
    "Select Traders",
    options=['Warren', 'Cathie', 'Pavel'],
    default=['Warren', 'Cathie', 'Pavel'],
    help="Choose which AI traders to analyze"
)

# Refresh button
if st.sidebar.button("🔄 Refresh Analysis", type="primary"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Trader Personalities")
st.sidebar.markdown("""
**Warren Buffett**: Value investing, long-term focus
**Cathie Wood**: Innovation, disruptive growth
**Pavel**: Day trading, momentum, technical analysis
""")

# Main interface
st.title("📈 AI Trading System")
st.markdown(f"### Analysis for **{st.session_state.selected_ticker}**")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Market Intelligence", "📈 Technical Analysis", "🤖 Trading Decisions", "💼 Portfolio"])

# Tab 1: Market Intelligence
with tab1:
    st.header("📊 Market Intelligence")
    
    # Create subtabs for different types of intelligence
    intel_tab1, intel_tab2 = st.tabs(["🌍 Market Overview", "🔍 Stock Research"])
    
    # Market Overview Tab
    with intel_tab1:
        with st.spinner("Getting market intelligence..."):
            try:
                market_agent = MarketIntelligenceAgent()
                
                # Market Overview
                st.subheader("🌍 Market Overview")
                result = run_async(market_agent.analyze("Get me the daily market overview", "general"))
                
                if result['status'] == 'success':
                    # Extract market data from tool results
                    tool_data = result.get('tool_results', {})
                    overview_text = tool_data.get('get_market_overview', 'No market data available')
                    
                    # Parse the overview text for display
                    st.text_area("Market Overview", overview_text, height=400)
                    
                    # Show AI analysis
                    st.subheader("🤖 AI Analysis")
                    st.write(result['analysis'])
                else:
                    st.error(f"Failed to load market intelligence: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"Market intelligence error: {e}")
    
    # Stock Research Tab
    with intel_tab2:
        st.subheader("🔍 Deep Stock Research")
        
        # Research controls
        col1, col2 = st.columns([3, 1])
        
        with col1:
            research_ticker = st.text_input(
                "Stock to Research",
                value=st.session_state.selected_ticker,
                help="Enter stock symbol for deep research"
            ).upper()
        
        with col2:
            research_personality = st.selectbox(
                "Trader Perspective",
                options=["General", "Warren", "Cathie", "Pavel"],
                help="Research perspective"
            )
        
        if st.button("🔍 Conduct Research", type="primary"):
            with st.spinner(f"Researching {research_ticker}..."):
                try:
                    market_agent = MarketIntelligenceAgent()
                    user_id = research_personality.lower() if research_personality != "General" else "general"
                    
                    query = f"Research {research_ticker} stock for potential investment"
                    result = run_async(market_agent.analyze(query, user_id))
                    
                    if result['status'] == 'success':
                        # Display research results
                        st.success(f"Research completed for {research_ticker}")
                        
                        # Extract tool results
                        tool_data = result.get('tool_results', {})
                        research_text = tool_data.get('research_specific_stock', 'No research data available')
                        
                        # Show raw research data
                        st.subheader("📋 Research Data")
                        st.text_area("Stock Research", research_text, height=400)
                        
                        # AI Analysis Report
                        st.subheader("🤖 AI Analysis")
                        st.write(result['analysis'])
                    
                    else:
                        st.error(f"Research failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"Research error: {e}")

# Tab 2: Technical Analysis
with tab2:
    st.header("📈 Technical Analysis")
    
    with st.spinner(f"Analyzing {st.session_state.selected_ticker}..."):
        try:
            tech_agent = TechnicalAnalysisAgent()
            
            # Get technical analysis
            tech_analysis = run_async(tech_agent.analyze_ticker(st.session_state.selected_ticker))
            
            if 'error' not in tech_analysis:
                # Current price and metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Current Price",
                        f"${tech_analysis['current_price']:.2f}",
                        f"{tech_analysis['price_change']['percent']:.2f}%"
                    )
                
                with col2:
                    rsi = tech_analysis['technical_indicators'].get('rsi', 0)
                    rsi_color = "normal"
                    if rsi > 70:
                        rsi_color = "inverse"
                    elif rsi < 30:
                        rsi_color = "normal"
                    st.metric("RSI", f"{rsi:.1f}", delta_color=rsi_color)
                
                with col3:
                    signals = tech_analysis['trading_signals']
                    st.metric("Signal Strength", signals['strength'].title())
                
                with col4:
                    volume = tech_analysis['volume_analysis']
                    st.metric("Volume Trend", volume['volume_trend'].title())
                
                # Candlestick Chart
                st.subheader("📊 Price Chart")
                
                chart_timeframe = st.selectbox(
                    "Timeframe",
                    options=["1D", "1H"],
                    index=0,
                    key="chart_timeframe"
                )
                
                chart_days = st.slider("Days to Show", 10, 200, 60, key="chart_days")
                
                with st.spinner("Creating chart..."):
                    fig = tech_agent.create_candlestick_chart(
                        st.session_state.selected_ticker,
                        timeframe=chart_timeframe,
                        days=chart_days
                    )
                    
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Could not create chart - insufficient data")
                
                # Technical Details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Technical Indicators")
                    indicators = tech_analysis['technical_indicators']
                    for key, value in indicators.items():
                        if isinstance(value, (int, float)):
                            st.write(f"**{key.upper()}:** {value:.2f}")
                
                with col2:
                    st.subheader("🎯 Support & Resistance")
                    sr = tech_analysis['support_resistance']
                    if sr.get('support') and sr.get('resistance'):
                        st.write(f"**Support:** ${sr['support']:.2f}")
                        st.write(f"**Resistance:** ${sr['resistance']:.2f}")
                        st.write(f"**Distance to Support:** {sr['current_vs_support']:.2f}%")
                        st.write(f"**Distance to Resistance:** {sr['current_vs_resistance']:.2f}%")
                
                # Trading Signals
                st.subheader("📡 Trading Signals")
                signals = tech_analysis['trading_signals']['signals']
                if signals:
                    for signal in signals:
                        st.write(f"• {signal}")
                else:
                    st.write("No clear signals at this time")
                    
            else:
                st.error(f"Technical analysis failed: {tech_analysis['error']}")
                
        except Exception as e:
            st.error(f"Technical analysis error: {e}")

# Tab 3: Trading Decisions
with tab3:
    st.header("🤖 Trading Decisions")
    
    # Get all traders
    traders = get_all_traders()
    
    for trader_name in selected_traders:
        if trader_name.lower() in traders:
            trader = traders[trader_name.lower()]
            
            st.subheader(f"🎯 {trader.name} ({trader.style})")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                with st.spinner(f"Getting {trader.name}'s decision..."):
                    try:
                        # Get trading decision
                        decision = run_async(trader.make_trading_decision(st.session_state.selected_ticker))
                        
                        if 'error' not in decision:
                            decision_data = decision['decision_data']
                            
                            # Decision summary
                            decision_action = decision_data.get('decision', 'HOLD')
                            conviction = decision_data.get('conviction', 'LOW')
                            
                            # Color code the decision
                            if decision_action == 'BUY':
                                st.success(f"**Decision:** {decision_action} ({conviction} conviction)")
                            elif decision_action == 'SELL':
                                st.error(f"**Decision:** {decision_action} ({conviction} conviction)")
                            else:
                                st.info(f"**Decision:** {decision_action} ({conviction} conviction)")
                            
                            # Rationale
                            st.write("**Rationale:**")
                            st.write(decision_data.get('rationale', 'No rationale provided'))
                            
                            # Key factors
                            if 'key_factors' in decision_data:
                                st.write("**Key Factors:**")
                                for factor in decision_data['key_factors']:
                                    st.write(f"• {factor}")
                            
                            # Trading details
                            if 'position_size_percent' in decision_data:
                                st.write(f"**Position Size:** {decision_data['position_size_percent']}% of portfolio")
                            
                            if 'timeline' in decision_data:
                                st.write(f"**Timeline:** {decision_data['timeline']}")
                            
                            # Pavel-specific details
                            if trader_name == 'Pavel':
                                if 'entry_price' in decision_data:
                                    st.write(f"**Entry Price:** ${decision_data['entry_price']}")
                                if 'stop_loss' in decision_data:
                                    st.write(f"**Stop Loss:** ${decision_data['stop_loss']}")
                                if 'target_price' in decision_data:
                                    st.write(f"**Target Price:** ${decision_data['target_price']}")
                                if 'risk_reward_ratio' in decision_data:
                                    st.write(f"**Risk/Reward:** {decision_data['risk_reward_ratio']}")
                        
                        else:
                            st.error(f"Decision failed: {decision['error']}")
                    
                    except Exception as e:
                        st.error(f"Error getting {trader.name}'s decision: {e}")
            
            with col2:
                # Execute trade button
                if st.button(f"Execute {trader.name}'s Trade", key=f"execute_{trader_name}"):
                    try:
                        decision = run_async(trader.make_trading_decision(st.session_state.selected_ticker))
                        if 'error' not in decision:
                            trade = st.session_state.portfolio.simulate_trade_execution(
                                trader.name,
                                st.session_state.selected_ticker,
                                decision['decision_data']
                            )
                            if trade:
                                st.success(f"Trade executed: {trade.action} {trade.quantity} shares at ${trade.price:.2f}")
                            else:
                                st.info("No trade executed (HOLD decision)")
                        else:
                            st.error("Could not execute trade")
                    except Exception as e:
                        st.error(f"Trade execution failed: {e}")
            
            st.markdown("---")

# Tab 4: Portfolio
with tab4:
    st.header("💼 Portfolio Management")
    
    # Portfolio summary for each trader
    for trader_name in ['Warren', 'Cathie', 'Pavel']:
        try:
            summary = st.session_state.portfolio.get_portfolio_summary(trader_name)
            positions = st.session_state.portfolio.get_positions(trader_name)
            recent_trades = st.session_state.portfolio.get_trades(trader=trader_name, limit=10)
            
            st.subheader(f"📊 {trader_name}'s Portfolio")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Value",
                    f"${summary['total_value']:,.2f}",
                    f"{summary['total_pnl_percent']:.2f}%"
                )
            
            with col2:
                st.metric("Cash", f"${summary['current_cash']:,.2f}")
            
            with col3:
                st.metric("Market Value", f"${summary['market_value']:,.2f}")
            
            with col4:
                st.metric("Positions", summary['number_of_positions'])
            
            # Positions table
            if positions:
                st.write("**Current Positions:**")
                positions_data = []
                for pos in positions:
                    positions_data.append({
                        'Ticker': pos.ticker,
                        'Quantity': f"{pos.quantity:.0f}",
                        'Avg Cost': f"${pos.avg_cost:.2f}",
                        'Current Price': f"${pos.current_price:.2f}",
                        'Market Value': f"${pos.market_value:.2f}",
                        'P&L': f"${pos.unrealized_pnl:.2f}",
                        'P&L %': f"{pos.unrealized_pnl_percent:.2f}%"
                    })
                
                df_positions = pd.DataFrame(positions_data)
                st.dataframe(df_positions, use_container_width=True)
            
            # Recent trades
            if recent_trades:
                st.write("**Recent Trades:**")
                trades_data = []
                for trade in recent_trades[:5]:
                    trades_data.append({
                        'Date': trade.timestamp[:10],
                        'Action': trade.action,
                        'Ticker': trade.ticker,
                        'Quantity': f"{trade.quantity:.0f}",
                        'Price': f"${trade.price:.2f}",
                        'Conviction': trade.conviction
                    })
                
                df_trades = pd.DataFrame(trades_data)
                st.dataframe(df_trades, use_container_width=True)
            
            st.markdown("---")
            
        except Exception as e:
            st.error(f"Portfolio error for {trader_name}: {e}")

# Footer
st.markdown("---")
st.markdown("### 🤖 AI Trading System")
st.markdown("Built with Streamlit, OpenAI, Alpha Vantage, and Polygon APIs")
st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")