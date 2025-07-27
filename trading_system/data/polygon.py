"""
Polygon API Client
Handles technical analysis and market data with database caching
"""
import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from database import Database

# Load environment variables
load_dotenv(override=True)


class PolygonClient:
    """Client for Polygon market data with database caching"""
    
    # Cache TTL settings (in seconds)
    CACHE_TTL = {
        'aggregates': 300,        # 5 minutes for price data during market hours
        'last_trade': 10,         # 10 seconds for real-time data
        'last_quote': 10,         # 10 seconds for real-time quotes
        'snapshot': 60,           # 1 minute for market snapshots
        'macd': 3600,            # 1 hour for technical indicators
        'rsi': 3600,             # 1 hour for technical indicators
        'sma': 3600,             # 1 hour for technical indicators
        'financials': 86400,      # 24 hours for company financials
        'market_status': 300,     # 5 minutes for market status
    }
    
    def __init__(self, api_key: Optional[str] = None, db_path: str = "trading_system.db"):
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("Polygon API key is required")
        
        self.base_url = "https://api.polygon.io"
        self.session = requests.Session()
        self.db = Database(db_path)
        self._current_session_data_sources = []  # Track data sources for current operation
        
    def _make_request(self, endpoint: str, params: Dict, cache_ttl: Optional[int] = None) -> Tuple[Dict, Dict]:
        """
        Make API request with caching support
        Returns: (response_data, metadata)
        """
        function_name = endpoint.split('/')[-1]  # Extract function name from endpoint
        
        # Determine cache TTL
        if cache_ttl is None:
            cache_ttl = self.CACHE_TTL.get(function_name, 300)  # Default 5 min
        
        # Check cache first
        cache_result = self.db.check_api_cache('polygon', function_name, params, cache_ttl)
        
        if cache_result:
            response_data, cache_age, api_call_id = cache_result
            print(f"🔄 Cache HIT: {function_name} (age: {cache_age}s)")
            
            # Track the original API call for briefing linkage
            self._current_session_data_sources.append((api_call_id, cache_age))
            
            return response_data, {
                'was_cached': True,
                'cache_age': cache_age,
                'api_call_id': api_call_id
            }
        
        # Cache miss - make actual API call
        params_with_key = params.copy()
        params_with_key['apikey'] = self.api_key
        
        try:
            # Build full URL
            full_url = f"{self.base_url}{endpoint}"
            
            # Log the API call (mask API key)
            log_params = {k: v for k, v in params_with_key.items() if k != 'apikey'}
            log_params['apikey'] = '*' * len(self.api_key)
            print(f"🌐 Polygon API Call: {full_url}?{self._format_params(log_params)}")
            
            response = self.session.get(full_url, params=params_with_key, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'ERROR':
                raise Exception(f"Polygon API Error: {data.get('error', 'Unknown error')}")
            
            # Log response summary
            if 'results' in data:
                if isinstance(data['results'], list):
                    print(f"📊 API Response: {len(data['results'])} results")
                elif isinstance(data['results'], dict) and 'values' in data['results']:
                    print(f"📊 API Response: {len(data['results']['values'])} data points")
                else:
                    print(f"📊 API Response: results object returned")
            
            # Save successful API call
            api_call_id = self.db.save_api_call(
                provider='polygon',
                function_name=function_name,
                params=params,
                response_data=data,
                success=True,
                was_cached=False,
                cache_age=0
            )
            
            # Track for briefing linkage
            self._current_session_data_sources.append((api_call_id, 0))
            
            return data, {
                'was_cached': False,
                'cache_age': 0,
                'api_call_id': api_call_id
            }
            
        except requests.exceptions.RequestException as e:
            # Save failed API call
            error_msg = str(e)
            self.db.save_api_call(
                provider='polygon',
                function_name=function_name,
                params=params,
                response_data={},
                success=False,
                error_message=error_msg
            )
            raise Exception(f"Request failed: {e}")
    
    def _format_params(self, params: Dict) -> str:
        """Format parameters for logging"""
        return "&".join(f"{k}={v}" for k, v in params.items())
    
    def get_session_data_sources(self) -> List[Tuple[int, int]]:
        """Get and clear current session's data sources"""
        sources = self._current_session_data_sources.copy()
        self._current_session_data_sources.clear()
        return sources
    
    # === PRICE DATA ===
    
    def get_aggregates(self, ticker: str, timespan: str = "day", 
                      from_date: str = None, to_date: str = None, limit: int = 120) -> Dict:
        """
        Get aggregated price data (OHLCV)
        timespan: minute, hour, day, week, month, quarter, year
        """
        if not from_date:
            # Default to 3 months ago
            from_dt = datetime.now() - timedelta(days=90)
            from_date = from_dt.strftime("%Y-%m-%d")
        
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        
        endpoint = f"/v2/aggs/ticker/{ticker}/range/1/{timespan}/{from_date}/{to_date}"
        params = {"limit": limit, "ticker": ticker, "timespan": timespan, "from_date": from_date, "to_date": to_date}
        
        data, metadata = self._make_request(endpoint, params)
        return data
    
    def get_last_trade(self, ticker: str) -> Dict:
        """Get last trade for a ticker"""
        endpoint = f"/v2/last/trade/{ticker}"
        params = {}
        
        data, metadata = self._make_request(endpoint, params, cache_ttl=10)  # 10 second cache
        return data
    
    def get_last_quote(self, ticker: str) -> Dict:
        """Get last quote (bid/ask) for a ticker"""
        endpoint = f"/v2/last/nbbo/{ticker}"
        params = {}
        
        data, metadata = self._make_request(endpoint, params, cache_ttl=10)  # 10 second cache
        return data
    
    # === MARKET SNAPSHOTS ===
    
    def get_market_gainers(self, limit: int = 20) -> Dict:
        """Get top market gainers"""
        endpoint = "/v2/snapshot/locale/us/markets/stocks/gainers"
        params = {"limit": limit}
        
        # Use longer cache when market is closed
        market_status = self.get_market_status()
        is_market_open = market_status.get("market") == "open"
        cache_ttl = 60 if is_market_open else 3600  # 1 minute if open, 1 hour if closed
        
        data, metadata = self._make_request(endpoint, params, cache_ttl=cache_ttl)
        return data
    
    def get_market_losers(self, limit: int = 20) -> Dict:
        """Get top market losers"""
        endpoint = "/v2/snapshot/locale/us/markets/stocks/losers"
        params = {"limit": limit}
        
        # Use longer cache when market is closed
        market_status = self.get_market_status()
        is_market_open = market_status.get("market") == "open"
        cache_ttl = 60 if is_market_open else 3600  # 1 minute if open, 1 hour if closed
        
        data, metadata = self._make_request(endpoint, params, cache_ttl=cache_ttl)
        return data
    
    def get_most_active(self, limit: int = 20) -> Dict:
        """Get most active stocks by volume"""
        endpoint = "/v2/snapshot/locale/us/markets/stocks/tickers"
        params = {"sort": "volume", "order": "desc", "limit": limit}
        
        # Use longer cache when market is closed
        market_status = self.get_market_status()
        is_market_open = market_status.get("market") == "open"
        cache_ttl = 60 if is_market_open else 3600  # 1 minute if open, 1 hour if closed
        
        data, metadata = self._make_request(endpoint, params, cache_ttl=cache_ttl)
        return data
    
    # === TECHNICAL INDICATORS ===
    
    def get_macd(self, ticker: str, timespan: str = "day", limit: int = 50) -> Dict:
        """Get MACD indicator"""
        endpoint = f"/v1/indicators/macd/{ticker}"
        params = {
            "timespan": timespan,
            "limit": limit
        }
        
        data, metadata = self._make_request(endpoint, params, cache_ttl=3600)  # 1 hour cache
        return data
    
    def get_rsi(self, ticker: str, timespan: str = "day", limit: int = 50, 
               window: int = 14) -> Dict:
        """Get RSI indicator"""
        endpoint = f"/v1/indicators/rsi/{ticker}"
        params = {
            "timespan": timespan,
            "limit": limit,
            "window": window
        }
        
        data, metadata = self._make_request(endpoint, params, cache_ttl=3600)
        return data
    
    def get_sma(self, ticker: str, timespan: str = "day", limit: int = 50,
               window: int = 20) -> Dict:
        """Get Simple Moving Average"""
        endpoint = f"/v1/indicators/sma/{ticker}"
        params = {
            "timespan": timespan,
            "limit": limit,
            "window": window
        }
        
        data, metadata = self._make_request(endpoint, params, cache_ttl=3600)
        return data
    
    # === MARKET STATUS ===
    
    def get_market_status(self) -> Dict:
        """Get current market status"""
        endpoint = "/v1/marketstatus/now"
        params = {}
        
        data, metadata = self._make_request(endpoint, params, cache_ttl=300)  # 5 minute cache
        return data