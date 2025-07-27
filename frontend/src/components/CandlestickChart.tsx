import TradingViewWidget from 'react-tradingview-widget';
import { useState, useEffect } from 'react';

interface CandlestickChartProps {
  symbol?: string;
}

// Map our symbols to TradingView format
const getTradingViewSymbol = (symbol: string): string => {
  const symbolMap: { [key: string]: string } = {
    'SPY': 'AMEX:SPY',
    'AAPL': 'NASDAQ:AAPL', 
    'TSLA': 'NASDAQ:TSLA',
    'NVDA': 'NASDAQ:NVDA',
    'MSFT': 'NASDAQ:MSFT',
    'BTC': 'BINANCE:BTCUSDT',
    'ETH': 'BINANCE:ETHUSDT'
  };
  
  return symbolMap[symbol] || `NASDAQ:${symbol}`;
};

export const CandlestickChart = ({ symbol = 'SPY' }: CandlestickChartProps) => {
  const tradingViewSymbol = getTradingViewSymbol(symbol);
  const [key, setKey] = useState(0);

  // Update key when symbol changes to force re-render
  useEffect(() => {
    setKey(prev => prev + 1);
  }, [symbol]);

  return (
    <div className="h-96 w-full bg-card rounded-lg border border-border">
      <div className="p-2 border-b border-border">
        <div className="text-sm font-medium text-muted-foreground">
          {symbol} • Professional Trading Chart
        </div>
      </div>
      <div className="h-[340px] w-full">
        <TradingViewWidget
          key={`${tradingViewSymbol}-${key}`}
          symbol={tradingViewSymbol}
          theme="dark"
          locale="en"
          autosize
          hide_side_toolbar={false}
          allow_symbol_change={true}
          interval="D"
          toolbar_bg="rgba(0, 0, 0, 0.1)"
          enable_publishing={false}
          hide_top_toolbar={false}
          save_image={false}
          studies={[
            "Volume@tv-basicstudies",
            "MACD@tv-basicstudies"
          ]}
          container_id={`tradingview_${symbol}_${key}`}
          style={{
            height: '100%',
            width: '100%'
          }}
          details={true}
          calendar={false}
          hotlist={false}
          news={[]}
        />
      </div>
    </div>
  );
};