#!/usr/bin/env python3
"""
Trading System Dashboard - Real-time view of all trader accounts and agent interactions
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import json
from datetime import datetime, timedelta
from accounts import get_trader_account, get_all_trader_accounts
from data.polygon import PolygonClient
import asyncio

st.set_page_config(
    page_title="Trading System Dashboard", 
    page_icon="📈", 
    layout="wide"
)

# Initialize session state
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False

def get_database_connection():
    """Get connection to trading system database"""
    return sqlite3.connect("trading_system.db")

def load_trader_accounts():
    """Load all trader account data"""
    try:
        accounts = get_all_trader_accounts()
        return accounts
    except Exception as e:
        st.error(f"Error loading accounts: {e}")
        return {}

def get_portfolio_history(trader_name):
    """Get portfolio value history for a trader"""
    try:
        account = get_trader_account(trader_name)
        if account.portfolio_value_time_series:
            df = pd.DataFrame(account.portfolio_value_time_series, columns=['timestamp', 'value'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading portfolio history for {trader_name}: {e}")
        return pd.DataFrame()

def get_recent_trades(trader_name, limit=10):
    """Get recent trades for a trader"""
    try:
        account = get_trader_account(trader_name)
        if account.transactions:
            trades = []
            for tx in account.transactions[-limit:]:
                trades.append({
                    'timestamp': tx.timestamp,
                    'symbol': tx.symbol,
                    'action': 'BUY' if tx.quantity > 0 else 'SELL',
                    'quantity': abs(tx.quantity),
                    'price': tx.price,
                    'total': abs(tx.total()),
                    'rationale': tx.rationale[:100] + "..." if len(tx.rationale) > 100 else tx.rationale
                })
            return pd.DataFrame(trades)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading trades for {trader_name}: {e}")
        return pd.DataFrame()

def get_agent_interactions(limit=20):
    """Get recent agent interactions from database"""
    try:
        conn = get_database_connection()
        
        # Get recent sessions from market briefings
        query = """
        SELECT 
            mb.session_id,
            mb.user_query,
            mb.briefing_content,
            mb.agent_type,
            mb.created_at,
            tu.tool_name,
            tu.tool_response
        FROM market_briefings mb
        LEFT JOIN tool_usage tu ON mb.session_id = tu.session_id
        ORDER BY mb.created_at DESC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"Error loading agent interactions: {e}")
        return pd.DataFrame()

def create_candlestick_chart(symbol, days=30):
    """Create candlestick chart for a symbol"""
    try:
        polygon = PolygonClient()
        
        # Get price data
        data = polygon.get_aggregates(symbol, timespan="day", limit=days)
        
        if not data.get("results"):
            return None
            
        bars = data["results"]
        
        # Create DataFrame
        df = pd.DataFrame(bars)
        df['t'] = pd.to_datetime(df['t'], unit='ms')
        
        # Create candlestick chart
        fig = go.Figure(data=go.Candlestick(
            x=df['t'],
            open=df['o'],
            high=df['h'], 
            low=df['l'],
            close=df['c'],
            name=symbol
        ))
        
        fig.update_layout(
            title=f"{symbol} - {days} Day Chart",
            yaxis_title="Price ($)",
            xaxis_title="Date",
            height=400
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating chart for {symbol}: {e}")
        return None

def create_portfolio_chart(trader_name):
    """Create portfolio value chart for a trader"""
    df = get_portfolio_history(trader_name)
    
    if df.empty:
        return None
        
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'], 
        y=df['value'],
        mode='lines+markers',
        name='Portfolio Value',
        line=dict(color='#1f77b4')
    ))
    
    fig.update_layout(
        title=f"{trader_name.title()}'s Portfolio Value",
        yaxis_title="Value ($)",
        xaxis_title="Date",
        height=300
    )
    
    return fig

# Main Dashboard
st.title("🏢 Trading System Dashboard")

# Sidebar controls
st.sidebar.header("🎛️ Controls")
st.session_state.debug_mode = st.sidebar.checkbox("🐛 Debug Mode", value=st.session_state.debug_mode)
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh (10s)", value=False)

if auto_refresh:
    st.rerun()

# Load account data
accounts = load_trader_accounts()

if not accounts:
    st.error("No trader accounts found! Run the trading system first.")
    st.stop()

# Top-level metrics
col1, col2, col3, col4 = st.columns(4)

total_portfolio_value = 0
total_pnl = 0
best_performer = None
best_performance = float('-inf')

for name, account in accounts.items():
    portfolio_value = account.calculate_portfolio_value()
    pnl = account.get_profit_loss()
    pnl_percent = (pnl / 10000) * 100  # 10k starting balance
    
    total_portfolio_value += portfolio_value
    total_pnl += pnl
    
    if pnl_percent > best_performance:
        best_performance = pnl_percent
        best_performer = name

with col1:
    st.metric("💰 Total Portfolio Value", f"${total_portfolio_value:,.2f}")

with col2:
    st.metric("📈 Total P&L", f"${total_pnl:,.2f}", f"{(total_pnl/30000)*100:.1f}%")

with col3:
    st.metric("🏆 Best Performer", best_performer.title() if best_performer else "None")

with col4:
    st.metric("📊 Best Performance", f"{best_performance:.1f}%" if best_performer else "0%")

# Trader Account Overview
st.header("👥 Trader Accounts")

for name, account in accounts.items():
    with st.expander(f"📊 {name.title()} - ${account.balance:,.2f}", expanded=True):
        
        col1, col2, col3 = st.columns(3)
        
        portfolio_value = account.calculate_portfolio_value()
        pnl = account.get_profit_loss()
        pnl_percent = (pnl / 10000) * 100
        
        with col1:
            st.metric("Portfolio Value", f"${portfolio_value:,.2f}")
            st.metric("Cash Balance", f"${account.balance:,.2f}")
        
        with col2:
            st.metric("P&L", f"${pnl:,.2f}", f"{pnl_percent:.1f}%")
            st.metric("Holdings", f"{len(account.holdings)} positions")
        
        with col3:
            if account.holdings:
                st.write("**Current Holdings:**")
                for symbol, quantity in account.holdings.items():
                    st.write(f"• {symbol}: {quantity} shares")
            else:
                st.write("*No current holdings*")
        
        # Portfolio chart
        portfolio_fig = create_portfolio_chart(name)
        if portfolio_fig:
            st.plotly_chart(portfolio_fig, use_container_width=True)
        
        # Recent trades
        trades_df = get_recent_trades(name, 5)
        if not trades_df.empty:
            st.write("**Recent Trades:**")
            st.dataframe(trades_df, use_container_width=True)

# Holdings Analysis
st.header("📈 Holdings Analysis")

# Get all unique holdings
all_holdings = set()
for account in accounts.values():
    all_holdings.update(account.holdings.keys())

if all_holdings:
    selected_symbol = st.selectbox("Select symbol for chart:", sorted(all_holdings))
    
    if selected_symbol:
        chart_days = st.slider("Chart period (days):", 7, 90, 30)
        fig = create_candlestick_chart(selected_symbol, chart_days)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            
            # Show which traders hold this symbol
            holders = []
            for name, account in accounts.items():
                if selected_symbol in account.holdings:
                    holders.append(f"{name.title()}: {account.holdings[selected_symbol]} shares")
            
            if holders:
                st.write(f"**Current holders of {selected_symbol}:**")
                for holder in holders:
                    st.write(f"• {holder}")
else:
    st.info("No holdings to analyze yet. Traders haven't made any purchases.")

# Agent Interactions
st.header("🤖 Agent Interactions")

interactions_df = get_agent_interactions(20)

if not interactions_df.empty:
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        agent_filter = st.selectbox("Filter by agent:", ["All"] + list(interactions_df['agent_type'].unique()))
    with col2:
        show_tools = st.checkbox("Show tool usage details", value=False)
    
    # Filter data
    filtered_df = interactions_df
    if agent_filter != "All":
        filtered_df = interactions_df[interactions_df['agent_type'] == agent_filter]
    
    for _, row in filtered_df.iterrows():
        with st.expander(f"🤖 {row['agent_type']} - {row['created_at'][:19]}", expanded=False):
            st.write(f"**Query:** {row['user_query']}")
            st.write(f"**Response:** {row['briefing_content'][:500]}...")
            
            if st.session_state.debug_mode:
                st.write("**Full Response:**")
                st.code(row['briefing_content'], language="text")
            
            if show_tools and pd.notna(row['tool_name']):
                st.write(f"**Tool Used:** {row['tool_name']}")
                if st.session_state.debug_mode and pd.notna(row['tool_response']):
                    st.write("**Tool Response:**")
                    st.code(row['tool_response'][:1000], language="text")

else:
    st.info("No agent interactions recorded yet.")

# Debug Information
if st.session_state.debug_mode:
    st.header("🐛 Debug Information")
    
    with st.expander("Database Tables", expanded=False):
        conn = get_database_connection()
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
        st.write("**Available Tables:**")
        for table in tables['name']:
            count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn)
            st.write(f"• {table}: {count.iloc[0]['count']} rows")
        conn.close()
    
    with st.expander("Account Raw Data", expanded=False):
        for name, account in accounts.items():
            st.write(f"**{name.title()} Account:**")
            st.json(account.model_dump())

# Footer
st.markdown("---")
st.caption("🏢 Trading System Dashboard | Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Auto-refresh logic
if auto_refresh:
    import time
    time.sleep(10)
    st.rerun()