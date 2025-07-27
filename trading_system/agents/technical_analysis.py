"""
Technical Analysis Agent
Uses Polygon data to provide technical analysis, charts, and trading signals
"""
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from openai import AsyncOpenAI
from dotenv import load_dotenv

from data.polygon import PolygonClient

# Load environment variables
load_dotenv(override=True)


class TechnicalAnalysisAgent:
    """
    Agent that provides technical analysis, chart patterns, and trading signals
    """
    
    def __init__(self):
        # Initialize API clients
        self.polygon = PolygonClient()
        self.openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    async def analyze_ticker(self, ticker: str, timeframe: str = "1D", days: int = 60) -> Dict:
        """Comprehensive technical analysis for a ticker"""
        try:
            # Get price data
            df = self.polygon.get_candlestick_data(ticker, timeframe, days)
            if df.empty:
                return {"error": f"No data available for {ticker}"}
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(df)
            
            # Identify patterns
            patterns = self._identify_patterns(df)
            
            # Generate trading signals
            signals = self._generate_signals(df, indicators)
            
            # Get current price info
            try:
                current_data = self.polygon.get_current_price(ticker)
                current_price = current_data.get('results', {}).get('p', df.iloc[-1]['close'])
            except:
                current_price = df.iloc[-1]['close']
            
            return {
                'ticker': ticker,
                'timestamp': datetime.now().isoformat(),
                'current_price': current_price,
                'price_change': {
                    'amount': df.iloc[-1]['close'] - df.iloc[-2]['close'],
                    'percent': ((df.iloc[-1]['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close']) * 100
                },
                'technical_indicators': indicators,
                'chart_patterns': patterns,
                'trading_signals': signals,
                'support_resistance': self._find_support_resistance(df),
                'volume_analysis': self._analyze_volume(df),
                'data_points': len(df)
            }
            
        except Exception as e:
            return {"error": f"Technical analysis failed for {ticker}: {e}"}
    
    def create_candlestick_chart(self, ticker: str, timeframe: str = "1D", days: int = 60) -> go.Figure:
        """Create interactive candlestick chart with technical indicators"""
        try:
            # Get data
            df = self.polygon.get_candlestick_data(ticker, timeframe, days)
            if df.empty:
                return None
            
            # Calculate indicators for plotting
            df = self._add_indicators_to_df(df)
            
            # Create subplots
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                subplot_titles=(f'{ticker} Price & Moving Averages', 'RSI', 'Volume'),
                row_width=[0.2, 0.1, 0.1]
            )
            
            # Candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name=ticker
                ),
                row=1, col=1
            )
            
            # Moving averages
            if 'sma_20' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['sma_20'],
                        line=dict(color='orange', width=1),
                        name='SMA 20'
                    ),
                    row=1, col=1
                )
            
            if 'sma_50' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['sma_50'],
                        line=dict(color='blue', width=1),
                        name='SMA 50'
                    ),
                    row=1, col=1
                )
            
            # RSI
            if 'rsi' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['rsi'],
                        line=dict(color='purple', width=1),
                        name='RSI'
                    ),
                    row=2, col=1
                )
                
                # RSI overbought/oversold lines
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            # Volume
            colors = ['red' if df.iloc[i]['close'] < df.iloc[i]['open'] else 'green' for i in range(len(df))]
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['volume'],
                    marker_color=colors,
                    name='Volume',
                    opacity=0.7
                ),
                row=3, col=1
            )
            
            # Update layout
            fig.update_layout(
                title=f'{ticker} Technical Analysis - {timeframe}',
                xaxis_rangeslider_visible=False,
                height=800,
                showlegend=True
            )
            
            # Update y-axis labels
            fig.update_yaxes(title_text="Price ($)", row=1, col=1)
            fig.update_yaxes(title_text="RSI", row=2, col=1)
            fig.update_yaxes(title_text="Volume", row=3, col=1)
            
            return fig
            
        except Exception as e:
            print(f"Chart creation failed: {e}")
            return None
    
    async def get_trading_recommendation(self, ticker: str, trader_personality: str) -> Dict:
        """Get AI-powered trading recommendation based on technical analysis"""
        try:
            # Get technical analysis
            analysis = await self.analyze_ticker(ticker)
            if 'error' in analysis:
                return analysis
            
            # Define personality preferences
            personality_styles = {
                'warren': 'Long-term value investing, focus on fundamentals over technicals, patient entry/exit',
                'cathie': 'Growth-focused, willing to buy on momentum, technology sector expertise',
                'flash': 'Day trading, scalping, momentum-based, quick entries and exits'
            }
            
            style = personality_styles.get(trader_personality.lower(), 'Balanced approach')
            
            # Create recommendation prompt
            prompt = f"""
            You are providing a trading recommendation for {ticker} to a trader with this style: {trader_personality.upper()}
            
            Trading Style: {style}
            
            Technical Analysis:
            - Current Price: ${analysis['current_price']:.2f}
            - Price Change: {analysis['price_change']['percent']:.2f}%
            - RSI: {analysis['technical_indicators'].get('rsi', 'N/A')}
            - SMA 20: {analysis['technical_indicators'].get('sma_20', 'N/A')}
            - SMA 50: {analysis['technical_indicators'].get('sma_50', 'N/A')}
            - Trading Signals: {analysis['trading_signals']}
            - Support/Resistance: {analysis['support_resistance']}
            - Volume Analysis: {analysis['volume_analysis']}
            
            Provide a concise recommendation (max 200 words) that includes:
            1. Overall assessment (BUY/SELL/HOLD)
            2. Entry/exit strategy appropriate for this trader's style
            3. Risk management considerations
            4. Key levels to watch
            
            Be specific and actionable for this personality type.
            """
            
            response = await self.openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are a technical analysis expert providing recommendations for {trader_personality} style trading."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            return {
                'ticker': ticker,
                'trader_personality': trader_personality,
                'recommendation': response.choices[0].message.content,
                'technical_analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Recommendation failed: {e}"}
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate technical indicators"""
        try:
            indicators = {}
            
            # Simple Moving Averages
            if len(df) >= 20:
                indicators['sma_20'] = df['close'].rolling(window=20).mean().iloc[-1]
            if len(df) >= 50:
                indicators['sma_50'] = df['close'].rolling(window=50).mean().iloc[-1]
            
            # RSI
            if len(df) >= 14:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators['rsi'] = rsi.iloc[-1]
            
            # MACD
            if len(df) >= 26:
                ema_12 = df['close'].ewm(span=12).mean()
                ema_26 = df['close'].ewm(span=26).mean()
                macd = ema_12 - ema_26
                signal = macd.ewm(span=9).mean()
                indicators['macd'] = macd.iloc[-1]
                indicators['macd_signal'] = signal.iloc[-1]
                indicators['macd_histogram'] = (macd - signal).iloc[-1]
            
            # Bollinger Bands
            if len(df) >= 20:
                sma_20 = df['close'].rolling(window=20).mean()
                std_20 = df['close'].rolling(window=20).std()
                indicators['bb_upper'] = (sma_20 + (std_20 * 2)).iloc[-1]
                indicators['bb_lower'] = (sma_20 - (std_20 * 2)).iloc[-1]
                indicators['bb_middle'] = sma_20.iloc[-1]
            
            return indicators
            
        except Exception as e:
            return {"error": f"Indicator calculation failed: {e}"}
    
    def _add_indicators_to_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to dataframe for charting"""
        # Moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    def _identify_patterns(self, df: pd.DataFrame) -> Dict:
        """Identify basic chart patterns"""
        patterns = []
        
        if len(df) < 10:
            return {"patterns": patterns}
        
        # Simple pattern detection
        recent_highs = df['high'].tail(10)
        recent_lows = df['low'].tail(10)
        
        # Check for breakouts
        if df['close'].iloc[-1] > recent_highs.max():
            patterns.append("Breakout above resistance")
        elif df['close'].iloc[-1] < recent_lows.min():
            patterns.append("Breakdown below support")
        
        # Check for trend
        if len(df) >= 20:
            sma_20 = df['close'].rolling(window=20).mean()
            if df['close'].iloc[-1] > sma_20.iloc[-1] and sma_20.iloc[-1] > sma_20.iloc[-5]:
                patterns.append("Uptrend")
            elif df['close'].iloc[-1] < sma_20.iloc[-1] and sma_20.iloc[-1] < sma_20.iloc[-5]:
                patterns.append("Downtrend")
        
        return {"patterns": patterns}
    
    def _generate_signals(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Generate trading signals based on technical analysis"""
        signals = {"strength": "neutral", "signals": []}
        
        signal_count = 0
        total_signals = 0
        
        # RSI signals
        if 'rsi' in indicators:
            total_signals += 1
            if indicators['rsi'] < 30:
                signals["signals"].append("RSI oversold - potential buy")
                signal_count += 1
            elif indicators['rsi'] > 70:
                signals["signals"].append("RSI overbought - potential sell")
                signal_count -= 1
        
        # Moving average signals
        if 'sma_20' in indicators and 'sma_50' in indicators:
            total_signals += 1
            current_price = df['close'].iloc[-1]
            if current_price > indicators['sma_20'] > indicators['sma_50']:
                signals["signals"].append("Price above both MAs - bullish")
                signal_count += 1
            elif current_price < indicators['sma_20'] < indicators['sma_50']:
                signals["signals"].append("Price below both MAs - bearish")
                signal_count -= 1
        
        # MACD signals
        if 'macd' in indicators and 'macd_signal' in indicators:
            total_signals += 1
            if indicators['macd'] > indicators['macd_signal']:
                signals["signals"].append("MACD bullish crossover")
                signal_count += 1
            else:
                signals["signals"].append("MACD bearish crossover")
                signal_count -= 1
        
        # Determine overall strength
        if total_signals > 0:
            signal_ratio = signal_count / total_signals
            if signal_ratio > 0.5:
                signals["strength"] = "bullish"
            elif signal_ratio < -0.5:
                signals["strength"] = "bearish"
        
        return signals
    
    def _find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Find key support and resistance levels"""
        try:
            recent_data = df.tail(20)
            
            resistance = recent_data['high'].max()
            support = recent_data['low'].min()
            
            return {
                "support": round(support, 2),
                "resistance": round(resistance, 2),
                "current_vs_support": round(((df['close'].iloc[-1] - support) / support) * 100, 2),
                "current_vs_resistance": round(((resistance - df['close'].iloc[-1]) / df['close'].iloc[-1]) * 100, 2)
            }
        except:
            return {"support": None, "resistance": None}
    
    def _analyze_volume(self, df: pd.DataFrame) -> Dict:
        """Analyze volume patterns"""
        try:
            recent_volume = df['volume'].tail(20)
            avg_volume = recent_volume.mean()
            current_volume = df['volume'].iloc[-1]
            
            volume_ratio = current_volume / avg_volume
            
            analysis = {
                "current_volume": int(current_volume),
                "average_volume": int(avg_volume),
                "volume_ratio": round(volume_ratio, 2),
                "volume_trend": "high" if volume_ratio > 1.5 else "normal" if volume_ratio > 0.5 else "low"
            }
            
            return analysis
        except:
            return {"volume_trend": "unknown"}