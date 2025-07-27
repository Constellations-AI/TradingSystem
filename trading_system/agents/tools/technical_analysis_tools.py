# agents/tools/technical_analysis_tools.py

import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_core.tools import tool

from data.polygon import PolygonClient
from database import Database

load_dotenv(override=True)

class TechnicalAnalysisTools:
    def __init__(self, polygon: PolygonClient, db: Database, session_id: str = None):
        self.polygon = polygon
        self.db = db
        self.session_id = session_id or f"session_{int(time.time())}"

    @classmethod
    async def create(cls, session_id: str = None):
        db = Database()
        polygon = PolygonClient(db_path=db.db_path)
        return cls(polygon, db, session_id)
    
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

    def _format_price(self, price: float) -> str:
        """Format price for display"""
        return f"${price:.2f}"

    def _calculate_change(self, current: float, previous: float) -> tuple:
        """Calculate price change and percentage"""
        change = current - previous
        pct_change = (change / previous) * 100 if previous != 0 else 0
        return change, pct_change

    def _format_change(self, change: float, pct_change: float) -> str:
        """Format price change for display"""
        sign = "+" if change >= 0 else ""
        return f"{sign}{change:.2f} ({sign}{pct_change:.1f}%)"

    # === PRICE ANALYSIS TOOLS ===

    async def get_current_price(self, ticker: str) -> str:
        start_time = time.time()
        tool_args = {"ticker": ticker}
        
        try:
            # Get current quote and last trade
            quote = self.polygon.get_last_quote(ticker)
            trade = self.polygon.get_last_trade(ticker)
            
            # Get recent aggregate for previous close
            recent_data = self.polygon.get_aggregates(ticker, timespan="day", limit=2)
            
            if quote.get("status") != "OK" or not recent_data.get("results"):
                response = f"{ticker}: Price data unavailable"
                execution_time = int((time.time() - start_time) * 1000)
                self._track_tool_usage("get_current_price", tool_args, response, execution_time, False)
                return response
            
            # Extract data
            last_price = trade.get("results", {}).get("p", 0)
            bid = quote.get("results", {}).get("p", 0)
            ask = quote.get("results", {}).get("P", 0)
            
            bars = recent_data["results"]
            prev_close = bars[-2]["c"] if len(bars) >= 2 else bars[-1]["c"]
            volume = bars[-1]["v"] if bars else 0
            
            # Calculate change
            change, pct_change = self._calculate_change(last_price, prev_close)
            
            # Format response
            response = f"{ticker}: {self._format_price(last_price)} {self._format_change(change, pct_change)} | " \
                      f"Bid: {self._format_price(bid)} | Ask: {self._format_price(ask)} | " \
                      f"Vol: {volume:,.0f}"
            
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_current_price", tool_args, response, execution_time, True)
            return response
            
        except Exception as e:
            error_msg = f"Error getting current price for {ticker}: {e}"
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_current_price", tool_args, error_msg, execution_time, False, str(e))
            return error_msg

    async def get_price_history(self, ticker: str, timeframe: str = "day", period: str = "3M") -> str:
        start_time = time.time()
        tool_args = {"ticker": ticker, "timeframe": timeframe, "period": period}
        
        try:
            # Map period to limit
            period_map = {"1W": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365}
            limit = period_map.get(period, 90)
            
            data = self.polygon.get_aggregates(ticker, timespan=timeframe, limit=limit)
            bars = data.get("results", [])
            
            if not bars:
                response = f"{ticker}: No price history available for {period}"
                execution_time = int((time.time() - start_time) * 1000)
                self._track_tool_usage("get_price_history", tool_args, response, execution_time, False)
                return response
            
            # Calculate key metrics
            first_bar = bars[0]
            last_bar = bars[-1]
            high_price = max(bar["h"] for bar in bars)
            low_price = min(bar["l"] for bar in bars)
            
            period_change, period_pct = self._calculate_change(last_bar["c"], first_bar["o"])
            avg_volume = sum(bar["v"] for bar in bars) / len(bars)
            
            response = f"{ticker} {period} History: {self._format_price(last_bar['c'])} " \
                      f"{self._format_change(period_change, period_pct)} | " \
                      f"Range: {self._format_price(low_price)}-{self._format_price(high_price)} | " \
                      f"Avg Vol: {avg_volume:,.0f} | {len(bars)} {timeframe} bars"
            
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_price_history", tool_args, response, execution_time, True)
            return response
            
        except Exception as e:
            error_msg = f"Error getting price history for {ticker}: {e}"
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_price_history", tool_args, error_msg, execution_time, False, str(e))
            return error_msg

    async def analyze_price_action(self, ticker: str) -> str:
        start_time = time.time()
        tool_args = {"ticker": ticker}
        
        try:
            # Get recent price data
            data = self.polygon.get_aggregates(ticker, timespan="day", limit=50)
            bars = data.get("results", [])
            
            if len(bars) < 20:
                response = f"{ticker}: Insufficient data for price action analysis"
                execution_time = int((time.time() - start_time) * 1000)
                self._track_tool_usage("analyze_price_action", tool_args, response, execution_time, False)
                return response
            
            # Calculate support/resistance (simple version)
            recent_highs = [bar["h"] for bar in bars[-20:]]
            recent_lows = [bar["l"] for bar in bars[-20:]]
            current_price = bars[-1]["c"]
            
            resistance = max(recent_highs)
            support = min(recent_lows)
            
            # Trend analysis (simple slope)
            week_ago_price = bars[-5]["c"] if len(bars) >= 5 else bars[0]["c"]
            trend_change, trend_pct = self._calculate_change(current_price, week_ago_price)
            
            if trend_pct > 2:
                trend = "Strong Uptrend"
            elif trend_pct > 0.5:
                trend = "Uptrend"
            elif trend_pct < -2:
                trend = "Strong Downtrend"
            elif trend_pct < -0.5:
                trend = "Downtrend"
            else:
                trend = "Sideways"
            
            # Distance from support/resistance
            support_distance = ((current_price - support) / support) * 100
            resistance_distance = ((resistance - current_price) / current_price) * 100
            
            response = f"{ticker} Price Action: {trend} | " \
                      f"Support: {self._format_price(support)} (-{support_distance:.1f}%) | " \
                      f"Resistance: {self._format_price(resistance)} (+{resistance_distance:.1f}%) | " \
                      f"Current: {self._format_price(current_price)}"
            
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("analyze_price_action", tool_args, response, execution_time, True)
            return response
            
        except Exception as e:
            error_msg = f"Error analyzing price action for {ticker}: {e}"
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("analyze_price_action", tool_args, error_msg, execution_time, False, str(e))
            return error_msg

    # === TECHNICAL INDICATOR TOOLS ===

    async def get_moving_averages(self, ticker: str) -> str:
        start_time = time.time()
        tool_args = {"ticker": ticker}
        
        try:
            # Get moving averages
            sma_20 = self.polygon.get_sma(ticker, window=20, limit=20)
            sma_50 = self.polygon.get_sma(ticker, window=50, limit=50)
            
            # Get current price
            current_data = self.polygon.get_aggregates(ticker, timespan="day", limit=1)
            
            if not all([sma_20.get("results"), sma_50.get("results"), current_data.get("results")]):
                response = f"{ticker}: Moving average data unavailable"
                execution_time = int((time.time() - start_time) * 1000)
                self._track_tool_usage("get_moving_averages", tool_args, response, execution_time, False)
                return response
            
            current_price = current_data["results"][0]["c"]
            sma20_values = sma_20["results"]["values"]
            sma50_values = sma_50["results"]["values"]
            
            if not sma20_values or not sma50_values:
                response = f"{ticker}: Moving average calculation incomplete"
                execution_time = int((time.time() - start_time) * 1000)
                self._track_tool_usage("get_moving_averages", tool_args, response, execution_time, False)
                return response
            
            sma20_current = sma20_values[-1]["value"]
            sma50_current = sma50_values[-1]["value"]
            
            # Determine position relative to MAs
            above_sma20 = "Above" if current_price > sma20_current else "Below"
            above_sma50 = "Above" if current_price > sma50_current else "Below"
            
            # Golden/Death cross
            sma20_prev = sma20_values[-2]["value"] if len(sma20_values) >= 2 else sma20_current
            sma50_prev = sma50_values[-2]["value"] if len(sma50_values) >= 2 else sma50_current
            
            cross_signal = ""
            if sma20_prev <= sma50_prev and sma20_current > sma50_current:
                cross_signal = " | Golden Cross"
            elif sma20_prev >= sma50_prev and sma20_current < sma50_current:
                cross_signal = " | Death Cross"
            
            response = f"{ticker} Moving Averages: " \
                      f"Price {above_sma20} SMA20({self._format_price(sma20_current)}) | " \
                      f"{above_sma50} SMA50({self._format_price(sma50_current)}){cross_signal}"
            
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_moving_averages", tool_args, response, execution_time, True)
            return response
            
        except Exception as e:
            error_msg = f"Error getting moving averages for {ticker}: {e}"
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_moving_averages", tool_args, error_msg, execution_time, False, str(e))
            return error_msg

    async def get_momentum_indicators(self, ticker: str) -> str:
        start_time = time.time()
        tool_args = {"ticker": ticker}
        
        try:
            # Get RSI and MACD
            rsi_data = self.polygon.get_rsi(ticker, window=14, limit=14)
            macd_data = self.polygon.get_macd(ticker, limit=26)
            
            if not all([rsi_data.get("results"), macd_data.get("results")]):
                response = f"{ticker}: Momentum indicator data unavailable"
                execution_time = int((time.time() - start_time) * 1000)
                self._track_tool_usage("get_momentum_indicators", tool_args, response, execution_time, False)
                return response
            
            rsi_values = rsi_data["results"].get("values", [])
            macd_values = macd_data["results"].get("values", [])
            
            if not rsi_values or not macd_values:
                response = f"{ticker}: Momentum calculations incomplete"
                execution_time = int((time.time() - start_time) * 1000)
                self._track_tool_usage("get_momentum_indicators", tool_args, response, execution_time, False)
                return response
            
            # Latest RSI
            current_rsi = rsi_values[-1]["value"]
            if current_rsi > 70:
                rsi_signal = "Overbought"
            elif current_rsi < 30:
                rsi_signal = "Oversold"
            else:
                rsi_signal = "Neutral"
            
            # Latest MACD
            current_macd = macd_values[-1]
            macd_line = current_macd["value"]
            signal_line = current_macd["signal"]
            histogram = current_macd["histogram"]
            
            if macd_line > signal_line and histogram > 0:
                macd_signal = "Bullish"
            elif macd_line < signal_line and histogram < 0:
                macd_signal = "Bearish"
            else:
                macd_signal = "Mixed"
            
            response = f"{ticker} Momentum: RSI {current_rsi:.1f} ({rsi_signal}) | " \
                      f"MACD {macd_line:.2f}/{signal_line:.2f} ({macd_signal}) | " \
                      f"Histogram {histogram:.2f}"
            
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_momentum_indicators", tool_args, response, execution_time, True)
            return response
            
        except Exception as e:
            error_msg = f"Error getting momentum indicators for {ticker}: {e}"
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_momentum_indicators", tool_args, error_msg, execution_time, False, str(e))
            return error_msg

    async def get_volume_analysis(self, ticker: str) -> str:
        start_time = time.time()
        tool_args = {"ticker": ticker}
        
        try:
            # Get recent volume data
            data = self.polygon.get_aggregates(ticker, timespan="day", limit=20)
            bars = data.get("results", [])
            
            if len(bars) < 10:
                response = f"{ticker}: Insufficient volume data"
                execution_time = int((time.time() - start_time) * 1000)
                self._track_tool_usage("get_volume_analysis", tool_args, response, execution_time, False)
                return response
            
            # Volume analysis
            current_volume = bars[-1]["v"]
            avg_volume = sum(bar["v"] for bar in bars[-10:]) / 10
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Calculate VWAP for recent days
            vwap_sum = sum(bar["c"] * bar["v"] for bar in bars[-5:])
            volume_sum = sum(bar["v"] for bar in bars[-5:])
            vwap = vwap_sum / volume_sum if volume_sum > 0 else bars[-1]["c"]
            
            current_price = bars[-1]["c"]
            vwap_position = "Above" if current_price > vwap else "Below"
            
            # Volume signal
            if volume_ratio > 2:
                volume_signal = "Very High"
            elif volume_ratio > 1.5:
                volume_signal = "High"
            elif volume_ratio < 0.5:
                volume_signal = "Low"
            else:
                volume_signal = "Normal"
            
            response = f"{ticker} Volume: {current_volume:,.0f} ({volume_signal}, {volume_ratio:.1f}x avg) | " \
                      f"VWAP: {self._format_price(vwap)} ({vwap_position}) | " \
                      f"10D Avg: {avg_volume:,.0f}"
            
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_volume_analysis", tool_args, response, execution_time, True)
            return response
            
        except Exception as e:
            error_msg = f"Error analyzing volume for {ticker}: {e}"
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_volume_analysis", tool_args, error_msg, execution_time, False, str(e))
            return error_msg

    # === MARKET CONTEXT TOOLS ===

    async def get_market_overview(self) -> str:
        start_time = time.time()
        tool_args = {}
        
        try:
            # Get market status and top movers
            market_status = self.polygon.get_market_status()
            gainers = self.polygon.get_market_gainers(limit=3)
            losers = self.polygon.get_market_losers(limit=3)
            
            # Market status
            market_state = market_status.get("market", "Unknown")
            
            # Format top movers - handle both "results" and "tickers" response formats
            top_gainers = []
            top_losers = []
            
            gainer_tickers = gainers.get("tickers", gainers.get("results", []))
            for stock in gainer_tickers[:3]:
                symbol = stock.get("ticker", stock.get("T", ""))
                change_pct = stock.get("todaysChangePerc", 0)
                top_gainers.append(f"{symbol}(+{change_pct:.1f}%)")
            
            loser_tickers = losers.get("tickers", losers.get("results", []))
            for stock in loser_tickers[:3]:
                symbol = stock.get("ticker", stock.get("T", ""))
                change_pct = stock.get("todaysChangePerc", 0)
                top_losers.append(f"{symbol}({change_pct:.1f}%)")
            
            response = f"Market Overview: {market_state} | " \
                      f"Top Gainers: {', '.join(top_gainers)} | " \
                      f"Top Losers: {', '.join(top_losers)}"
            
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_market_overview", tool_args, response, execution_time, True)
            return response
            
        except Exception as e:
            error_msg = f"Error getting market overview: {e}"
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_market_overview", tool_args, error_msg, execution_time, False, str(e))
            return error_msg

    async def get_market_movers_with_analysis(self, limit: int = 20) -> str:
        start_time = time.time()
        tool_args = {"limit": limit}
        
        try:
            # Get market status first
            market_status = self.polygon.get_market_status()
            market_state = market_status.get("market", "Unknown")
            
            # Get comprehensive market movers
            gainers = self.polygon.get_market_gainers(limit=limit)
            losers = self.polygon.get_market_losers(limit=limit)
            most_active = self.polygon.get_most_active(limit=min(limit, 10))  # Limit most active to avoid too much data
            
            # Handle both "results" and "tickers" response formats
            gainer_tickers = gainers.get("tickers", gainers.get("results", []))
            loser_tickers = losers.get("tickers", losers.get("results", []))
            active_tickers = most_active.get("tickers", most_active.get("results", []))
            
            if not gainer_tickers and not loser_tickers:
                response = f"Market ({market_state}): No market movers data available"
                execution_time = int((time.time() - start_time) * 1000)
                self._track_tool_usage("get_market_movers_with_analysis", tool_args, response, execution_time, False)
                return response
            
            # Analyze top gainers
            top_gainers = []
            gainer_results = gainer_tickers[:limit]
            for stock in gainer_results:
                symbol = stock.get("ticker", stock.get("T", ""))
                change_pct = stock.get("todaysChangePerc", 0)
                # Handle different volume field names and nested structures
                volume = stock.get("day", {}).get("v", stock.get("v", 0))
                price = stock.get("day", {}).get("c", stock.get("c", 0))
                
                # Quick analysis
                volume_desc = "High Vol" if volume > 1000000 else "Normal Vol"
                price_desc = "High Price" if price > 100 else "Mid Price" if price > 20 else "Low Price"
                
                top_gainers.append(f"{symbol}(+{change_pct:.1f}%, {price_desc}, {volume_desc})")
            
            # Analyze top losers
            top_losers = []
            loser_results = loser_tickers[:limit]
            for stock in loser_results:
                symbol = stock.get("ticker", stock.get("T", ""))
                change_pct = stock.get("todaysChangePerc", 0)
                volume = stock.get("day", {}).get("v", stock.get("v", 0))
                price = stock.get("day", {}).get("c", stock.get("c", 0))
                
                volume_desc = "High Vol" if volume > 1000000 else "Normal Vol"
                price_desc = "High Price" if price > 100 else "Mid Price" if price > 20 else "Low Price"
                
                top_losers.append(f"{symbol}({change_pct:.1f}%, {price_desc}, {volume_desc})")
            
            # Most active analysis
            most_active_list = []
            active_results = active_tickers[:5]  # Top 5 most active
            for stock in active_results:
                symbol = stock.get("ticker", stock.get("T", ""))
                volume = stock.get("day", {}).get("v", stock.get("v", 0))
                change_pct = stock.get("todaysChangePerc", 0)
                
                direction = "↑" if change_pct > 0 else "↓" if change_pct < 0 else "→"
                most_active_list.append(f"{symbol}({direction}{abs(change_pct):.1f}%, {volume:,.0f})")
            
            # Generate recommendations
            recommendations = []
            
            # Look for strong gainers with high volume
            for stock in gainer_results[:5]:  # Top 5 gainers
                change_pct = stock.get("todaysChangePerc", 0)
                volume = stock.get("day", {}).get("v", stock.get("v", 0))
                symbol = stock.get("ticker", stock.get("T", ""))
                if change_pct > 5 and volume > 500000:  # Strong gain + decent volume
                    recommendations.append(f"BUY {symbol} (+{change_pct:.1f}% momentum)")
            
            # Look for oversold opportunities in losers
            for stock in loser_results[:3]:  # Top 3 losers
                change_pct = stock.get("todaysChangePerc", 0)
                volume = stock.get("day", {}).get("v", stock.get("v", 0))
                symbol = stock.get("ticker", stock.get("T", ""))
                if change_pct < -3 and volume > 300000:  # Decent drop + volume
                    recommendations.append(f"WATCH {symbol} ({change_pct:.1f}% potential oversold)")
            
            if not recommendations:
                recommendations = ["No clear momentum plays - consider waiting for better setups"]
            
            # Format comprehensive response
            response = f"Market Movers ({market_state}):\n\n"
            response += f"🚀 TOP GAINERS: {', '.join(top_gainers[:10])}\n\n"
            response += f"📉 TOP LOSERS: {', '.join(top_losers[:10])}\n\n"
            response += f"🔥 MOST ACTIVE: {', '.join(most_active_list)}\n\n"
            response += f"💡 RECOMMENDATIONS: {' | '.join(recommendations[:3])}"
            
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_market_movers_with_analysis", tool_args, response, execution_time, True)
            return response
            
        except Exception as e:
            error_msg = f"Error getting market movers analysis: {e}"
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("get_market_movers_with_analysis", tool_args, error_msg, execution_time, False, str(e))
            return error_msg

    async def technical_summary(self, ticker: str) -> str:
        start_time = time.time()
        tool_args = {"ticker": ticker}
        
        try:
            # Get current price and basic data
            current_data = self.polygon.get_aggregates(ticker, timespan="day", limit=5)
            rsi_data = self.polygon.get_rsi(ticker, window=14, limit=14)
            sma_20 = self.polygon.get_sma(ticker, window=20, limit=20)
            
            if not all([current_data.get("results"), rsi_data.get("results"), sma_20.get("results")]):
                response = f"{ticker}: Insufficient data for technical summary"
                execution_time = int((time.time() - start_time) * 1000)
                self._track_tool_usage("technical_summary", tool_args, response, execution_time, False)
                return response
            
            # Current metrics
            bars = current_data["results"]
            current_price = bars[-1]["c"]
            week_change = ((current_price - bars[0]["o"]) / bars[0]["o"]) * 100
            
            rsi_values = rsi_data["results"].get("values", [])
            sma20_values = sma_20["results"].get("values", [])
            
            if not rsi_values or not sma20_values:
                response = f"{ticker}: Technical calculations incomplete"
                execution_time = int((time.time() - start_time) * 1000)
                self._track_tool_usage("technical_summary", tool_args, response, execution_time, False)
                return response
            
            current_rsi = rsi_values[-1]["value"]
            sma20_current = sma20_values[-1]["value"]
            
            # Overall signal
            signals = []
            
            # Price vs SMA20
            if current_price > sma20_current:
                signals.append("Above SMA20")
            else:
                signals.append("Below SMA20")
            
            # RSI signal
            if current_rsi > 70:
                signals.append("Overbought")
            elif current_rsi < 30:
                signals.append("Oversold")
            
            # Trend
            if week_change > 5:
                trend = "STRONG BULLISH"
            elif week_change > 2:
                trend = "BULLISH"
            elif week_change < -5:
                trend = "STRONG BEARISH"
            elif week_change < -2:
                trend = "BEARISH"
            else:
                trend = "NEUTRAL"
            
            response = f"{ticker} Summary: {trend} | {', '.join(signals)} | " \
                      f"5D: {week_change:+.1f}% | RSI: {current_rsi:.0f} | " \
                      f"Price vs SMA20: {((current_price/sma20_current-1)*100):+.1f}%"
            
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("technical_summary", tool_args, response, execution_time, True)
            return response
            
        except Exception as e:
            error_msg = f"Error creating technical summary for {ticker}: {e}"
            execution_time = int((time.time() - start_time) * 1000)
            self._track_tool_usage("technical_summary", tool_args, error_msg, execution_time, False, str(e))
            return error_msg

# --- Tool binding ---

async def technical_analysis_tools(session_id: str = None):
    toolkit = await TechnicalAnalysisTools.create(session_id)

    @tool
    async def get_current_price(ticker: str) -> str:
        """Get real-time price, bid/ask, and volume for a stock."""
        return await toolkit.get_current_price(ticker)

    @tool
    async def get_price_history(ticker: str, timeframe: str = "day", period: str = "3M") -> str:
        """Get historical price data. timeframe: minute/day/week. period: 1W/1M/3M/6M/1Y."""
        return await toolkit.get_price_history(ticker, timeframe, period)

    @tool
    async def analyze_price_action(ticker: str) -> str:
        """Analyze support/resistance levels and price trends."""
        return await toolkit.analyze_price_action(ticker)

    @tool
    async def get_moving_averages(ticker: str) -> str:
        """Get moving averages (SMA 20/50) and crossover signals."""
        return await toolkit.get_moving_averages(ticker)

    @tool
    async def get_momentum_indicators(ticker: str) -> str:
        """Get RSI and MACD momentum indicators with signals."""
        return await toolkit.get_momentum_indicators(ticker)

    @tool
    async def get_volume_analysis(ticker: str) -> str:
        """Analyze volume patterns, VWAP, and unusual activity."""
        return await toolkit.get_volume_analysis(ticker)

    @tool
    async def get_market_overview() -> str:
        """Get overall market status and top gainers/losers."""
        return await toolkit.get_market_overview()

    @tool
    async def get_market_movers_with_analysis(limit: int = 20) -> str:
        """Get comprehensive market movers analysis with buy/sell recommendations. Shows top gainers, losers, most active stocks with volume and price analysis."""
        return await toolkit.get_market_movers_with_analysis(limit)

    @tool
    async def technical_summary(ticker: str) -> str:
        """Get comprehensive one-line technical analysis summary."""
        return await toolkit.technical_summary(ticker)

    return [
        get_current_price,
        get_price_history,
        analyze_price_action,
        get_moving_averages,
        get_momentum_indicators,
        get_volume_analysis,
        get_market_overview,
        get_market_movers_with_analysis,
        technical_summary
    ]