# agents/tools/market_intelligence.py

import os
import time
from datetime import datetime
from typing import List
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

from data.alpha_vantage import AlphaVantageClient
from database import Database
from db_config import DATABASE_PATH

load_dotenv(override=True)

class MarketIntelligenceTools:
    def __init__(self, alpha: AlphaVantageClient, db: Database, session_id: str = None):
        self.alpha = alpha
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.db = db
        self.session_id = session_id or f"session_{int(time.time())}"

    @classmethod
    async def create(cls, session_id: str = None):
        db = Database(DATABASE_PATH)
        alpha = AlphaVantageClient(db_path=db.db_path)
        return cls(alpha, db, session_id)
    
    def _track_tool_usage(self, tool_name: str, tool_args: dict, response: str, 
                         execution_time_ms: int = None, success: bool = True, error: str = None):
        """Helper method to track tool usage"""
        try:
            self.db.save_tool_usage(
                session_id=self.session_id,
                tool_name=tool_name,
                tool_args=tool_args,
                tool_response=response,
                execution_time_ms=execution_time_ms,
                success=success,
                error_message=error
            )
        except Exception as e:
            print(f"Warning: Failed to save tool usage: {e}")

    async def get_market_overview(self) -> str:
        start_time = time.time()
        tool_args = {}
        
        try:
            # Store API calls for debugging
            import sys
            from io import StringIO
            
            # Capture print output
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            data = self.alpha.get_daily_briefing_data()
            
            # Restore stdout and get captured output
            sys.stdout = old_stdout
            api_calls = captured_output.getvalue()
            
            # Include API calls in debug info if available
            debug_info = f"\n\n🔍 DEBUG - API Calls:\n{api_calls}" if api_calls.strip() else ""
            market_news = data.get("market_news", {})
            articles = market_news.get("feed", [])
            if not articles:
                response = "No market news articles available."
                self._track_tool_usage("get_market_overview", tool_args, response, 
                                     int((time.time() - start_time) * 1000), True)
                return response
            
            # Get overall sentiment and top stories
            top_stories = []
            sentiments = []
            
            for article in articles[:5]:
                title = article.get("title", "No title")
                sentiment_score = article.get("overall_sentiment_score", 0)
                sentiment_label = article.get("overall_sentiment_label", "Neutral")
                source = article.get("source", "Unknown")
                
                top_stories.append(f"• {title} ({source}) - {sentiment_label}")
                sentiments.append(sentiment_score)
            
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
            
            overview = f"Market Overview:\n"
            overview += f"Average sentiment: {avg_sentiment:.3f} ({self._sentiment_label(avg_sentiment)})\n"
            overview += f"Based on {len(articles)} recent articles\n\n"
            overview += "Top Stories:\n" + "\n".join(top_stories)
            overview += debug_info
            
            # Track successful tool usage
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_market_overview", tool_args, overview, execution_time, True)
            
            return overview
        except Exception as e:
            error_msg = f"Error getting market overview: {e}"
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_market_overview", tool_args, error_msg, execution_time, False, str(e))
            return error_msg
    
    def _sentiment_label(self, score):
        if score > 0.1:
            return "Positive"
        elif score < -0.1:
            return "Negative"
        else:
            return "Neutral"

    async def research_specific_stock(self, ticker: str) -> str:
        start_time = time.time()
        tool_args = {"ticker": ticker}
        
        try:
            # Capture API calls for debugging
            import sys
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            # First, try to resolve the ticker symbol if it might be a company name
            resolved_ticker = ticker.upper()
            debug_info = ""
            
            if not ticker.isupper() or len(ticker) > 5:  # Likely a company name
                symbol_search = self.alpha.search_symbol(ticker)
                matches = symbol_search.get("bestMatches", [])
                if matches:
                    resolved_ticker = matches[0].get("1. symbol", ticker.upper())
                    debug_info = f"🔍 Resolved '{ticker}' to ticker: {resolved_ticker}\n"
                else:
                    debug_info = f"⚠️ Could not resolve '{ticker}' to a ticker symbol\n"
            
            ticker_sentiment = self.alpha.get_ticker_sentiment(resolved_ticker, limit=15)
            
            sys.stdout = old_stdout
            api_calls = captured_output.getvalue()
            debug_info += f"\n🔍 DEBUG - API Calls:\n{api_calls}" if api_calls.strip() else ""
            
            articles = ticker_sentiment.get("feed", [])
            
            if not articles:
                return f"No recent articles found for {ticker}"
            
            # Calculate ticker-specific sentiment
            ticker_sentiments = []
            relevant_articles = []
            
            for article in articles:
                title = article.get("title", "No title")
                source = article.get("source", "Unknown")
                time_published = article.get("time_published", "Unknown time")
                
                # Look for ticker-specific sentiment
                ticker_sentiment_data = article.get("ticker_sentiment", [])
                debug_info += f"📈 Article: {title[:50]}...\n"
                debug_info += f"   Available tickers: {[ts.get('ticker') for ts in ticker_sentiment_data]}\n"
                debug_info += f"   Looking for: {resolved_ticker}\n"
                debug_info += f"   Ticker sentiment data: {ticker_sentiment_data}\n"
                
                for ts in ticker_sentiment_data:
                    if ts.get("ticker") == resolved_ticker:  # Use resolved ticker
                        debug_info += f"   FOUND MATCH! Ticker data: {ts}\n"
                        sentiment_score = float(ts.get("ticker_sentiment_score", 0))
                        sentiment_label = ts.get("ticker_sentiment_label", "Neutral")
                        relevance = float(ts.get("relevance_score", 0))
                        debug_info += f"   Parsed: score={sentiment_score}, label={sentiment_label}, relevance={relevance}\n"
                        
                        if relevance > 0.01:  # Lowered threshold to include more articles
                            ticker_sentiments.append(sentiment_score)
                            relevant_articles.append({
                                "title": title,
                                "source": source,
                                "sentiment": sentiment_label,
                                "score": sentiment_score,
                                "time": time_published
                            })
            
            if not ticker_sentiments:
                return f"Found {len(articles)} articles mentioning {ticker}, but none with significant relevance"
            
            avg_sentiment = sum(ticker_sentiments) / len(ticker_sentiments)
            
            analysis = f"Analysis for {resolved_ticker} ({ticker}):\n"
            analysis += f"Average sentiment: {avg_sentiment:.3f} ({self._sentiment_label(avg_sentiment)})\n"
            analysis += f"Based on {len(relevant_articles)} relevant articles\n\n"
            
            analysis += "Recent relevant articles:\n"
            for article in relevant_articles[:3]:
                analysis += f"• {article['title']} ({article['source']}) - {article['sentiment']}\n"
            
            analysis += debug_info
            
            # Track successful tool usage
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("research_specific_stock", tool_args, analysis, execution_time, True)
            
            return analysis
            
        except Exception as e:
            import traceback
            error_msg = f"Error researching {ticker}: {e}\n\nFull traceback:\n{traceback.format_exc()}"
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("research_specific_stock", tool_args, error_msg, execution_time, False, str(e))
            return error_msg

    async def get_topic_sentiment(self, topic: str) -> str:
        try:
            data = self.alpha.get_topic_sentiment(topic, limit=10)
            articles = data.get("feed", [])
            
            if not articles:
                return f"No articles found for topic: {topic}"
            
            # Calculate topic sentiment and gather relevant articles
            sentiments = []
            topic_articles = []
            
            for article in articles:
                title = article.get("title", "No title")
                source = article.get("source", "Unknown")
                sentiment_score = article.get("overall_sentiment_score", 0)
                sentiment_label = article.get("overall_sentiment_label", "Neutral")
                
                # Check if article is relevant to the topic
                topics_list = article.get("topics", [])
                topic_relevance = any(topic.lower() in t.get("topic", "").lower() for t in topics_list)
                
                if topic_relevance or topic.lower() in title.lower():
                    sentiments.append(sentiment_score)
                    topic_articles.append({
                        "title": title,
                        "source": source,
                        "sentiment": sentiment_label,
                        "score": sentiment_score
                    })
            
            if not sentiments:
                return f"Found {len(articles)} articles but none specifically relevant to {topic}"
            
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            analysis = f"Topic Analysis: {topic}\n"
            analysis += f"Average sentiment: {avg_sentiment:.3f} ({self._sentiment_label(avg_sentiment)})\n"
            analysis += f"Based on {len(topic_articles)} relevant articles\n\n"
            
            analysis += "Recent articles:\n"
            for article in topic_articles[:3]:
                analysis += f"• {article['title']} ({article['source']}) - {article['sentiment']}\n"
            
            return analysis
            
        except Exception as e:
            return f"Error analyzing topic {topic}: {e}"

    async def search_additional_context(self, query: str) -> str:
        if not self.brave_api_key:
            return "Brave API key not configured."
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.brave_api_key
            }
            params = {
                "q": query,
                "count": 5,
                "search_lang": "en",
                "country": "US",
                "safesearch": "moderate"
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            results = response.json().get("web", {}).get("results", [])

            formatted = f"Top results for '{query}':\n"
            for result in results[:3]:
                formatted += f"- {result.get('title')} ({result.get('url')})\n"
            return formatted or "No results found."

        except Exception as e:
            return f"Brave search failed: {e}"

# --- Tool binding ---

async def market_intelligence_tools(session_id: str = None):
    toolkit = await MarketIntelligenceTools.create(session_id)

    @tool
    async def get_market_overview() -> str:
        """Get market sentiment, trending tickers, and key stories."""
        return await toolkit.get_market_overview()

    @tool
    async def research_specific_stock(ticker: str) -> str:
        """Analyze a specific stock including recent sentiment and articles."""
        return await toolkit.research_specific_stock(ticker)

    @tool
    async def get_topic_sentiment(topic: str) -> str:
        """Analyze sentiment trends for a given topic or sector."""
        return await toolkit.get_topic_sentiment(topic)

    @tool
    async def search_additional_context(query: str) -> str:
        """Web search for financial or market topics."""
        return await toolkit.search_additional_context(query)

    return [
        get_market_overview,
        research_specific_stock,
        get_topic_sentiment,
        search_additional_context
    ]
