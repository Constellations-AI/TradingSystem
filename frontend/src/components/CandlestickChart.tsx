import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface CandlestickChartProps {
  symbol?: string;
}

interface MarketData {
  timestamp: string;
  date: string;
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export const CandlestickChart = ({ symbol = 'SPY' }: CandlestickChartProps) => {
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`http://localhost:8000/api/market/${symbol}?timeframe=day&limit=30`);
        const data = await response.json();
        if (data.data) {
          setMarketData(data.data);
        }
      } catch (error) {
        console.error('Error fetching market data:', error);
        // Generate mock data as fallback
        const mockData = generateMockData(symbol);
        setMarketData(mockData);
      } finally {
        setLoading(false);
      }
    };

    fetchMarketData();
  }, [symbol]);

  const generateMockData = (symbol: string): MarketData[] => {
    const data: MarketData[] = [];
    const basePrice = { SPY: 450, AAPL: 180, TSLA: 250, NVDA: 140 }[symbol] || 150;
    
    for (let i = 29; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      const open = basePrice + (Math.random() - 0.5) * 10;
      const close = open + (Math.random() - 0.5) * 8;
      const high = Math.max(open, close) + Math.random() * 3;
      const low = Math.min(open, close) - Math.random() * 3;
      
      data.push({
        timestamp: date.toISOString(),
        date: date.toISOString().split('T')[0],
        time: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        open: Number(open.toFixed(2)),
        high: Number(high.toFixed(2)),
        low: Number(low.toFixed(2)),
        close: Number(close.toFixed(2)),
        volume: Math.floor(1000000 + Math.random() * 500000)
      });
    }
    
    return data;
  };

  if (loading) {
    return (
      <div className="h-96 w-full bg-card rounded-lg border border-border flex items-center justify-center">
        <div className="text-muted-foreground">Loading chart data...</div>
      </div>
    );
  }

  return (
    <div className="h-96 w-full bg-card rounded-lg border border-border">
      <div className="p-4 border-b border-border">
        <div className="text-sm font-medium text-muted-foreground">
          {symbol} • Price Chart (30 Days)
        </div>
      </div>
      <div className="h-[320px] w-full p-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={marketData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="time" 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
            />
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              domain={['dataMin - 5', 'dataMax + 5']}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'hsl(var(--popover))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
            />
            <Line 
              type="monotone" 
              dataKey="close" 
              stroke="hsl(var(--primary))" 
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};