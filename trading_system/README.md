# 🤖 AI Trading System

A clean, focused AI trading system with market intelligence, technical analysis, and personality-driven trading decisions.

## 🏗️ Architecture

### Core Components
- **Market Intelligence Agent** - Alpha Vantage news & sentiment analysis
- **Technical Analysis Agent** - Polygon price data & chart analysis  
- **Trading Agents** - Warren Buffett, Cathie Wood, Flash personalities
- **Streamlit Interface** - Interactive dashboard with Plotly charts

### Clean Structure
```
trading_system/
├── agents/                 # AI agent implementations
│   ├── market_intelligence.py
│   ├── technical_analysis.py
│   └── traders.py
├── data/                   # API client classes
│   ├── alpha_vantage.py
│   └── polygon.py
├── models/                 # Data structures
│   └── portfolio.py
├── app.py                  # Streamlit interface
├── main.py                 # Entry point
└── requirements.txt
```

## 🚀 Quick Start

### 1. Environment Setup
```bash
cd trading_system
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy `.env.example` to `.env` and add your API keys:
```
OPENAI_API_KEY=your_openai_key
ALPHAVANTAGE_API_KEY=your_alphavantage_key
POLYGON_API_KEY=your_polygon_key
BRAVE_API_KEY=your_brave_key  # Optional
ANTHROPIC_API_KEY=your_anthropic_key  # Optional
```

### 3. Run the System
```bash
python main.py
```
or directly:
```bash
streamlit run app.py
```

## 🎯 Features

### Market Intelligence
- **Daily Market Overview** - Sentiment, key stories, trending tickers
- **Personalized Briefings** - Tailored to each trader personality
- **News Analysis** - High-impact article identification
- **Brave Search Integration** - Deep-dive article analysis

### Technical Analysis
- **Interactive Charts** - Candlestick charts with indicators
- **Technical Indicators** - RSI, SMA, MACD, Bollinger Bands
- **Pattern Recognition** - Basic chart pattern detection
- **Support/Resistance** - Key price levels identification
- **Volume Analysis** - Volume trends and confirmation

### AI Traders
- **Warren Buffett** - Value investing, long-term focus, fundamental analysis
- **Cathie Wood** - Innovation investing, disruptive growth, technology focus
- **Flash** - Day trading, momentum, technical analysis, quick decisions

### Portfolio Management
- **Position Tracking** - Current holdings and P&L
- **Trade History** - Detailed trade logs with rationale
- **Performance Metrics** - Portfolio value and returns
- **Risk Management** - Position sizing and stop losses

## 🔧 Technical Details

### Data Sources
- **Alpha Vantage** - News sentiment, market intelligence
- **Polygon** - Stock prices, OHLCV data, market data
- **OpenAI GPT-4** - AI analysis and decision making
- **Brave Search** - Article search and context (optional)

### Agent Architecture
Each agent is **standalone** and **focused**:
- Market Intelligence Agent handles external data and sentiment
- Technical Analysis Agent handles price data and indicators
- Trading Agents make personality-driven decisions using both sources

### Key Improvements over Previous System
- ✅ **Clean separation of concerns** - each agent has one responsibility
- ✅ **No agent-as-tool antipattern** - full agents with proper context
- ✅ **Focused scope** - market intelligence + technical analysis + decisions
- ✅ **Modern UI** - Streamlit with interactive Plotly charts
- ✅ **Simple data flow** - API clients → Agents → UI
- ✅ **Portfolio demonstration** - clean trade tracking and P&L

## 🎨 UI Components

### 📊 Market Intelligence Tab
- Market sentiment overview
- Key stories with sentiment scores
- Trending tickers
- Expandable story details with links

### 📈 Technical Analysis Tab
- Real-time price metrics (price, RSI, signals, volume)
- Interactive candlestick charts with indicators
- Configurable timeframes and periods
- Support/resistance levels
- Trading signal summary

### 🤖 Trading Decisions Tab
- Personality-driven analysis for each trader
- Decision rationale with key factors
- Position sizing and risk management
- Execute trade buttons (demo)
- Flash-specific entry/exit levels

### 💼 Portfolio Tab
- Portfolio summary for each trader
- Current positions with P&L
- Recent trade history
- Performance metrics

## 🔮 Future Enhancements

### Near Term
- Real-time price updates
- More technical indicators
- Backtesting functionality
- Email/SMS alerts

### Medium Term
- Options analysis
- Sector rotation strategies
- Risk analytics dashboard
- Performance attribution

### Long Term
- Live trading integration
- Multi-asset support (crypto, forex)
- Advanced ML models
- Social sentiment integration

## 📈 Portfolio Demonstration

This system demonstrates:
- **Clean architecture** - modular, testable, maintainable
- **AI integration** - practical use of LLMs for financial analysis
- **Data visualization** - professional charts and dashboards
- **API integration** - real market data from multiple sources
- **Personality modeling** - distinct trading strategies and decision making

Perfect for showcasing **software engineering skills** combined with **AI/ML expertise** and **financial domain knowledge**.