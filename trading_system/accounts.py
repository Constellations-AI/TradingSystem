from pydantic import BaseModel
import json
from dotenv import load_dotenv
from datetime import datetime
from data.polygon import PolygonClient
from database import Database
from db_config import DATABASE_PATH

load_dotenv(override=True)

INITIAL_BALANCE = 10_000.0
SPREAD = 0.002


def get_closing_price(symbol: str) -> float:
    """Get the most recent closing price for a symbol"""
    try:
        polygon = PolygonClient()
        # Get the last day's data
        data = polygon.get_aggregates(symbol, timespan="day", limit=1)
        
        if data.get("status") == "OK" and data.get("results"):
            results = data["results"]
            if results and len(results) > 0:
                return results[0].get("c", 0)  # 'c' is closing price
        
        return 0  # Unable to get closing price
    except Exception as e:
        print(f"Error getting closing price for {symbol}: {e}")
        return 0


def get_current_price(symbol: str) -> float:
    """Get current market price for a symbol using Polygon API"""
    try:
        # Always use last trade price - works regardless of market hours
        polygon = PolygonClient()
        trade_data = polygon.get_last_trade(symbol)
        
        # Use last trade price if available
        if trade_data.get("status") == "OK" and trade_data.get("results"):
            return trade_data["results"].get("p", 0)
        
        # Fallback to quote data if trade data unavailable
        quote_data = polygon.get_last_quote(symbol)
        if quote_data.get("status") == "OK" and quote_data.get("results"):
            bid = quote_data["results"].get("p", 0)
            ask = quote_data["results"].get("P", 0)
            if bid > 0 and ask > 0:
                return (bid + ask) / 2
        
        return 0  # Unable to get price
    except Exception as e:
        print(f"Error getting price for {symbol}: {e}")
        return 0


class Transaction(BaseModel):
    symbol: str
    quantity: int
    price: float
    timestamp: str
    rationale: str

    def total(self) -> float:
        return self.quantity * self.price
    
    def __repr__(self):
        return f"{abs(self.quantity)} shares of {self.symbol} at {self.price} each."


class Account(BaseModel):
    name: str
    balance: float
    strategy: str
    holdings: dict[str, int]
    transactions: list[Transaction]
    portfolio_value_time_series: list[tuple[str, float]]

    @classmethod
    def get(cls, name: str):
        # Use persistent database path
        db = Database(DATABASE_PATH)
        
        # Table creation is now handled by Database.init_database()
        # No need to create tables here since Database class handles both SQLite and PostgreSQL
        
        # Try to load existing account data
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                # Use appropriate parameter style for database type
                if hasattr(db, 'use_postgresql') and db.use_postgresql:
                    cursor.execute(
                        "SELECT balance, strategy, holdings, transactions, portfolio_history FROM trader_accounts WHERE trader_name = %s",
                        (name.lower(),)
                    )
                else:
                    cursor.execute(
                        "SELECT balance, strategy, holdings, transactions, portfolio_history FROM trader_accounts WHERE trader_name = ?",
                        (name.lower(),)
                    )
                result = cursor.fetchone()
                
                if result:
                    balance, strategy, holdings_json, transactions_json, portfolio_json = result
                    
                    # Parse JSON fields
                    holdings = json.loads(holdings_json) if holdings_json else {}
                    transactions_data = json.loads(transactions_json) if transactions_json else []
                    portfolio_history = json.loads(portfolio_json) if portfolio_json else []
                    
                    # Convert transaction dicts back to Transaction objects
                    transactions = [Transaction(**t) for t in transactions_data]
                    
                    return cls(
                        name=name.lower(),
                        balance=balance,
                        strategy=strategy,
                        holdings=holdings,
                        transactions=transactions,
                        portfolio_value_time_series=portfolio_history
                    )
        except Exception as e:
            print(f"Note: Creating new account for {name} (previous data not found: {e})")
        
        # Create default account data
        account = cls(
            name=name.lower(),
            balance=INITIAL_BALANCE,
            strategy="",
            holdings={},
            transactions=[],
            portfolio_value_time_series=[]
        )
        
        # Add initial portfolio value entry for performance tracking
        account.update_portfolio_value_series()
        
        return account
    
    def save(self):
        # Save account data to persistent database
        db = Database(DATABASE_PATH)
        
        # Convert transactions to JSON-serializable format
        transactions_data = [t.model_dump() for t in self.transactions]
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                # Use appropriate upsert syntax for database type
                if hasattr(db, 'use_postgresql') and db.use_postgresql:
                    cursor.execute('''
                        INSERT INTO trader_accounts 
                        (trader_name, balance, strategy, holdings, transactions, portfolio_history, last_updated)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (trader_name) DO UPDATE SET
                            balance = EXCLUDED.balance,
                            strategy = EXCLUDED.strategy,
                            holdings = EXCLUDED.holdings,
                            transactions = EXCLUDED.transactions,
                            portfolio_history = EXCLUDED.portfolio_history,
                            last_updated = EXCLUDED.last_updated
                    ''', (
                        self.name.lower(),
                        self.balance,
                        self.strategy,
                        json.dumps(self.holdings),
                        json.dumps(transactions_data),
                        json.dumps(self.portfolio_value_time_series),
                        datetime.now().isoformat()
                    ))
                else:
                    cursor.execute('''
                        INSERT OR REPLACE INTO trader_accounts 
                        (trader_name, balance, strategy, holdings, transactions, portfolio_history, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        self.name.lower(),
                        self.balance,
                        self.strategy,
                        json.dumps(self.holdings),
                        json.dumps(transactions_data),
                        json.dumps(self.portfolio_value_time_series),
                        datetime.now().isoformat()
                    ))
                conn.commit()
        except Exception as e:
            print(f"Error saving account for {self.name}: {e}")

    def reset(self, strategy: str):
        self.balance = INITIAL_BALANCE
        self.strategy = strategy
        self.holdings = {}
        self.transactions = []
        self.portfolio_value_time_series = []
        self.save()

    def deposit(self, amount: float):
        """ Deposit funds into the account. """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        print(f"Deposited ${amount}. New balance: ${self.balance}")
        self.save()

    def withdraw(self, amount: float):
        """ Withdraw funds from the account, ensuring it doesn't go negative. """
        if amount > self.balance:
            raise ValueError("Insufficient funds for withdrawal.")
        self.balance -= amount
        print(f"Withdrew ${amount}. New balance: ${self.balance}")
        self.save()

    def buy_shares(self, symbol: str, quantity: int, rationale: str) -> str:
        """ Buy shares of a stock if sufficient funds are available. """
        
        # Get current market price
        price = get_current_price(symbol)
        if price == 0:
            raise ValueError(f"Unable to get current price for {symbol}. Market may be closed or symbol invalid.")
        
        # Apply spread for realistic trading costs
        buy_price = price * (1 + SPREAD)
        total_cost = buy_price * quantity
        
        if total_cost > self.balance:
            raise ValueError("Insufficient funds to buy shares.")
        
        # Update holdings
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Record transaction
        transaction = Transaction(
            symbol=symbol, 
            quantity=quantity, 
            price=buy_price, 
            timestamp=timestamp, 
            rationale=rationale
        )
        self.transactions.append(transaction)
        
        # Update balance
        self.balance -= total_cost
        self.save()
        
        return f"Bought {quantity} shares of {symbol} at ${buy_price:.2f} each. Total cost: ${total_cost:.2f}\n" + self.report()

    def sell_shares(self, symbol: str, quantity: int, rationale: str) -> str:
        """ Sell shares of a stock if the user has enough shares. """
        
        if self.holdings.get(symbol, 0) < quantity:
            raise ValueError(f"Cannot sell {quantity} shares of {symbol}. Only {self.holdings.get(symbol, 0)} shares held.")
        
        # Get current market price
        price = get_current_price(symbol)
        if price == 0:
            raise ValueError(f"Unable to get current price for {symbol}. Market may be closed or symbol invalid.")
        
        # Apply spread for realistic trading costs
        sell_price = price * (1 - SPREAD)
        total_proceeds = sell_price * quantity
        
        # Update holdings
        self.holdings[symbol] -= quantity
        
        # If shares are completely sold, remove from holdings
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Record transaction (negative quantity for sell)
        transaction = Transaction(
            symbol=symbol, 
            quantity=-quantity, 
            price=sell_price, 
            timestamp=timestamp, 
            rationale=rationale
        )
        self.transactions.append(transaction)

        # Update balance
        self.balance += total_proceeds
        self.save()
        
        return f"Sold {quantity} shares of {symbol} at ${sell_price:.2f} each. Total proceeds: ${total_proceeds:.2f}\n" + self.report()

    def calculate_portfolio_value(self):
        """ Calculate the total value of the user's portfolio. """
        total_value = self.balance
        for symbol, quantity in self.holdings.items():
            current_price = get_current_price(symbol)
            total_value += current_price * quantity
        return total_value

    def calculate_profit_loss(self, portfolio_value: float):
        """ Calculate profit or loss from the initial investment. """
        return portfolio_value - INITIAL_BALANCE

    def get_holdings(self):
        """ Report the current holdings of the user. """
        return self.holdings

    def get_profit_loss(self):
        """ Report the user's profit or loss at any point in time. """
        portfolio_value = self.calculate_portfolio_value()
        return self.calculate_profit_loss(portfolio_value)

    def list_transactions(self):
        """ List all transactions made by the user. """
        return [transaction.model_dump() for transaction in self.transactions]
    
    def update_portfolio_value_series(self):
        """Update portfolio value time series without full report"""
        portfolio_value = self.calculate_portfolio_value()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Avoid duplicate timestamps (only update if time changed)
        if not self.portfolio_value_time_series or self.portfolio_value_time_series[-1][0] != timestamp:
            self.portfolio_value_time_series.append((timestamp, portfolio_value))
            self.save()
    
    def report(self) -> str:
        """ Return a JSON string representing the account. """
        portfolio_value = self.calculate_portfolio_value()
        self.portfolio_value_time_series.append((datetime.now().strftime("%Y-%m-%d %H:%M:%S"), portfolio_value))
        self.save()
        
        pnl = self.calculate_profit_loss(portfolio_value)
        data = self.model_dump()
        data["total_portfolio_value"] = portfolio_value
        data["total_profit_loss"] = pnl
        data["total_profit_loss_percent"] = (pnl / INITIAL_BALANCE) * 100
        
        return json.dumps(data, indent=2)
    
    def get_strategy(self) -> str:
        """ Return the strategy of the account """
        return self.strategy
    
    def change_strategy(self, strategy: str) -> str:
        """ Change the investment strategy for this account """
        self.strategy = strategy
        self.save()
        return f"Strategy changed to: {strategy}"


# Factory functions for creating trader accounts
def get_trader_account(trader_name: str) -> Account:
    """Get or create an account for a specific trader"""
    return Account.get(trader_name.lower())


def get_all_trader_accounts() -> dict[str, Account]:
    """Get accounts for all trader personalities"""
    return {
        'warren': get_trader_account('warren'),
        'camillo': get_trader_account('camillo'),
        'flash': get_trader_account('flash')
    }


# Example usage:
if __name__ == "__main__":
    # Test the account system
    print("Testing Account System...")
    
    # Create accounts for each trader (individual databases)
    warren = get_trader_account("warren")
    camillo = get_trader_account("camillo")
    pavel = get_trader_account("pavel")
    
    print(f"Warren's account: ${warren.balance}")
    print(f"Cathie's account: ${camillo.balance}")
    print(f"Pavel's account: ${pavel.balance}")
    print("All accounts saved to shared trading_system.db")
    
    print("Account system ready!")