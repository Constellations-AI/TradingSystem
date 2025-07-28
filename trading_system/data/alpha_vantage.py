"""
Alpha Vantage API Client
Handles market intelligence and sentiment data with database caching
"""
import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from database import Database
from db_config import DATABASE_PATH

# Load environment variables
load_dotenv(override=True)


class AlphaVantageClient:
    """Client for Alpha Vantage market intelligence with database caching"""
    
    # Cache TTL settings (in seconds)
    CACHE_TTL = {
        'NEWS_SENTIMENT': 1800,    # 30 minutes
        'SYMBOL_SEARCH': 86400,    # 24 hours
        'TIME_SERIES_DAILY': 3600, # 1 hour
    }
    
    def __init__(self, api_key: Optional[str] = None, db_path: str = None):
        self.api_key = api_key or os.getenv("ALPHAVANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is required")
        
        self.base_url = "https://www.alphavantage.co/query"
        self.session = requests.Session()
        self.db = Database(db_path or DATABASE_PATH)
        self._current_session_data_sources = []  # Track data sources for current operation
        
    def _make_request(self, params: Dict, cache_ttl: Optional[int] = None) -> Tuple[Dict, Dict]:
        """
        Make API request with caching support
        Returns: (response_data, metadata)
        """
        function_name = params.get('function', 'unknown')
        
        # Determine cache TTL
        if cache_ttl is None:
            cache_ttl = self.CACHE_TTL.get(function_name, 1800)  # Default 30 min
        
        # Check cache first
        cache_result = self.db.check_api_cache('alpha_vantage', function_name, params, cache_ttl)
        
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
            # Log the full URL being called
            full_url = f"{self.base_url}?" + "&".join(f"{k}={v}" for k, v in params_with_key.items() if k != 'apikey')
            full_url += f"&apikey={'*' * len(self.api_key)}"  # Mask API key in logs
            print(f"🌐 Alpha Vantage API Call: {full_url}")
            
            response = self.session.get(self.base_url, params=params_with_key, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                raise Exception(f"Alpha Vantage API Error: {data['Error Message']}")
            
            # Log response summary
            if 'feed' in data:
                print(f"📊 API Response: {len(data['feed'])} articles returned")
            
            # Save successful API call
            api_call_id = self.db.save_api_call(
                provider='alpha_vantage',
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
                provider='alpha_vantage',
                function_name=function_name,
                params=params,
                response_data={},
                success=False,
                error_message=error_msg
            )
            raise Exception(f"Request failed: {e}")
    
    def get_session_data_sources(self) -> List[Tuple[int, int]]:
        """Get and clear current session's data sources"""
        sources = self._current_session_data_sources.copy()
        self._current_session_data_sources.clear()
        return sources
    
    def get_market_news(self, topics: str = None, limit: int = 20) -> Dict:
        """Get latest market news with sentiment analysis"""
        params = {
            'function': 'NEWS_SENTIMENT',
            'sort': 'LATEST',
            'limit': str(limit)
        }
        
        if topics:
            params['topics'] = topics
            
        data, metadata = self._make_request(params)
        return data
    
    def get_market_sentiment(self, time_from: str = None, time_to: str = None) -> Dict:
        """Get market sentiment for a time period"""
        params = {
            'function': 'NEWS_SENTIMENT',
            'sort': 'RELEVANCE',
            'limit': '50'
        }
        
        # Default to last 24 hours if no time range provided
        if not time_from:
            yesterday = datetime.now() - timedelta(days=1)
            time_from = yesterday.strftime("%Y%m%dT0000")
            time_to = datetime.now().strftime("%Y%m%dT2359")
        
        params['time_from'] = time_from
        params['time_to'] = time_to
        
        data, metadata = self._make_request(params)
        return data
    
    def get_topic_sentiment(self, topic: str, limit: int = 15) -> Dict:
        """Get sentiment analysis for specific topic"""
        params = {
            'function': 'NEWS_SENTIMENT',
            'topics': topic,
            'sort': 'RELEVANCE',
            'limit': str(limit)
        }
        
        data, metadata = self._make_request(params)
        return data
    
    def search_symbol(self, keywords: str) -> Dict:
        """Search for ticker symbols using company name or keywords"""
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': keywords
        }
        
        # Symbol search can be cached longer
        data, metadata = self._make_request(params, cache_ttl=86400)  # 24 hours
        return data
    
    def get_ticker_sentiment(self, tickers: str, limit: int = 15) -> Dict:
        """Get sentiment analysis for specific tickers"""
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': tickers,
            'sort': 'RELEVANCE',
            'limit': str(limit)
        }
        
        data, metadata = self._make_request(params)
        return data
    
    def get_daily_briefing_data(self) -> Dict:
        """Get comprehensive daily market intelligence"""
        # Get general market news
        market_data = self.get_market_news(limit=30)
        
        # Get sentiment for key topics
        topics = ['financial_markets', 'economy_macro', 'technology', 'earnings']
        topic_data = {}
        
        for topic in topics:
            try:
                topic_data[topic] = self.get_topic_sentiment(topic, limit=10)
            except Exception as e:
                print(f"Warning: Failed to get {topic} sentiment: {e}")
                topic_data[topic] = None
        
        return {
            'market_news': market_data,
            'topic_sentiments': topic_data,
            'timestamp': datetime.now().isoformat()
        }