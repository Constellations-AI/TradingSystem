"""
Portfolio and Trade Models
Simple data structures for tracking trades and portfolio performance
"""
import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import os


@dataclass
class Trade:
    """Individual trade record"""
    id: Optional[int] = None
    trader: str = ""
    ticker: str = ""
    action: str = ""  # BUY, SELL
    quantity: float = 0.0
    price: float = 0.0
    timestamp: str = ""
    rationale: str = ""
    conviction: str = ""
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None


@dataclass
class Position:
    """Current position in a ticker"""
    ticker: str
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float


class Portfolio:
    """Portfolio management for tracking trades and positions"""
    
    def __init__(self, db_path: str = "trading_system.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for portfolio tracking"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trader TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    rationale TEXT,
                    conviction TEXT,
                    stop_loss REAL,
                    target_price REAL
                )
            ''')
            
            # Portfolio summary table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_summary (
                    trader TEXT PRIMARY KEY,
                    cash_balance REAL DEFAULT 100000.0,
                    total_value REAL DEFAULT 100000.0,
                    total_pnl REAL DEFAULT 0.0,
                    last_updated TEXT
                )
            ''')
            
            conn.commit()
    
    def add_trade(self, trade: Trade) -> int:
        """Add a new trade to the portfolio"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades (trader, ticker, action, quantity, price, timestamp, rationale, conviction, stop_loss, target_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade.trader, trade.ticker, trade.action, trade.quantity, trade.price,
                trade.timestamp, trade.rationale, trade.conviction, trade.stop_loss, trade.target_price
            ))
            
            trade_id = cursor.lastrowid
            conn.commit()
            return trade_id
    
    def get_trades(self, trader: str = None, ticker: str = None, limit: int = 100) -> List[Trade]:
        """Get trades with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM trades WHERE 1=1"
            params = []
            
            if trader:
                query += " AND trader = ?"
                params.append(trader)
            
            if ticker:
                query += " AND ticker = ?"
                params.append(ticker)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            trades = []
            for row in rows:
                trade = Trade(
                    id=row[0], trader=row[1], ticker=row[2], action=row[3],
                    quantity=row[4], price=row[5], timestamp=row[6],
                    rationale=row[7], conviction=row[8], stop_loss=row[9], target_price=row[10]
                )
                trades.append(trade)
            
            return trades
    
    def get_positions(self, trader: str) -> List[Position]:
        """Calculate current positions for a trader"""
        trades = self.get_trades(trader=trader, limit=1000)
        
        # Calculate net positions
        positions = {}
        for trade in trades:
            ticker = trade.ticker
            if ticker not in positions:
                positions[ticker] = {'quantity': 0, 'total_cost': 0}
            
            if trade.action == 'BUY':
                positions[ticker]['quantity'] += trade.quantity
                positions[ticker]['total_cost'] += trade.quantity * trade.price
            elif trade.action == 'SELL':
                positions[ticker]['quantity'] -= trade.quantity
                positions[ticker]['total_cost'] -= trade.quantity * trade.price
        
        # Filter out zero positions and calculate metrics
        position_list = []
        for ticker, data in positions.items():
            if abs(data['quantity']) > 0.001:  # Avoid floating point precision issues
                avg_cost = data['total_cost'] / data['quantity'] if data['quantity'] != 0 else 0
                
                # For demo purposes, use a simple price (in real app, would fetch current price)
                current_price = avg_cost * (1 + (hash(ticker) % 21 - 10) / 100)  # Simulate price movement
                market_value = data['quantity'] * current_price
                unrealized_pnl = market_value - data['total_cost']
                unrealized_pnl_percent = (unrealized_pnl / data['total_cost']) * 100 if data['total_cost'] != 0 else 0
                
                position = Position(
                    ticker=ticker,
                    quantity=data['quantity'],
                    avg_cost=avg_cost,
                    current_price=current_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percent=unrealized_pnl_percent
                )
                position_list.append(position)
        
        return position_list
    
    def get_portfolio_summary(self, trader: str) -> Dict:
        """Get portfolio summary for a trader"""
        positions = self.get_positions(trader)
        trades = self.get_trades(trader=trader, limit=1000)
        
        # Calculate portfolio metrics
        total_market_value = sum(pos.market_value for pos in positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
        
        # Calculate realized P&L from closed positions (simplified)
        total_realized_pnl = 0
        for trade in trades:
            if trade.action == 'SELL':
                # This is a simplified calculation - in reality, would need FIFO/LIFO logic
                total_realized_pnl += trade.quantity * trade.price * 0.01  # Assume 1% profit per sale for demo
        
        starting_cash = 100000  # Demo starting amount
        cash_used = sum(trade.quantity * trade.price for trade in trades if trade.action == 'BUY')
        cash_received = sum(trade.quantity * trade.price for trade in trades if trade.action == 'SELL')
        current_cash = starting_cash - cash_used + cash_received
        
        total_portfolio_value = current_cash + total_market_value
        total_pnl = total_portfolio_value - starting_cash
        total_pnl_percent = (total_pnl / starting_cash) * 100
        
        return {
            'trader': trader,
            'starting_capital': starting_cash,
            'current_cash': current_cash,
            'market_value': total_market_value,
            'total_value': total_portfolio_value,
            'unrealized_pnl': total_unrealized_pnl,
            'realized_pnl': total_realized_pnl,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
            'number_of_positions': len(positions),
            'number_of_trades': len(trades),
            'last_updated': datetime.now().isoformat()
        }
    
    def simulate_trade_execution(self, trader: str, ticker: str, decision_data: Dict) -> Trade:
        """Convert a trading decision into an executed trade"""
        action = decision_data.get('decision', 'HOLD')
        if action == 'HOLD':
            return None
        
        # Simulate trade execution
        quantity = 100  # Demo quantity
        price = 150.0  # Demo price (in real app, would fetch current market price)
        
        trade = Trade(
            trader=trader,
            ticker=ticker,
            action=action,
            quantity=quantity,
            price=price,
            timestamp=datetime.now().isoformat(),
            rationale=decision_data.get('rationale', ''),
            conviction=decision_data.get('conviction', ''),
            stop_loss=decision_data.get('stop_loss'),
            target_price=decision_data.get('target_price')
        )
        
        trade.id = self.add_trade(trade)
        return trade