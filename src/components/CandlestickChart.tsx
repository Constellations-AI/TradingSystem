import { ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from 'recharts';

// Generate mock candlestick data
const generateCandlestickData = () => {
  const data = [];
  let price = 45000;
  
  for (let i = 0; i < 30; i++) {
    const open = price;
    const high = open + Math.random() * 2000;
    const low = open - Math.random() * 1500;
    const close = low + Math.random() * (high - low);
    const volume = Math.random() * 1000 + 500;
    
    data.push({
      time: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      open,
      high,
      low,
      close,
      volume,
      // For display purposes, we'll show green/red bars
      bodyHeight: Math.abs(close - open),
      bodyY: Math.min(open, close),
      wickTop: high,
      wickBottom: low,
      fill: close >= open ? 'hsl(var(--trading-green))' : 'hsl(var(--trading-red))'
    });
    
    price = close;
  }
  
  return data;
};

const candlestickData = generateCandlestickData();

export const CandlestickChart = () => {
  return (
    <div className="h-96">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={candlestickData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--chart-grid))" />
          <XAxis 
            dataKey="time" 
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'hsl(var(--chart-text))', fontSize: 12 }}
          />
          <YAxis 
            domain={['dataMin - 1000', 'dataMax + 1000']}
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'hsl(var(--chart-text))', fontSize: 12 }}
            tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px',
              color: 'hsl(var(--card-foreground))'
            }}
            formatter={(value, name) => [
              name === 'volume' ? `${Math.round(value as number)}` : `$${(value as number).toFixed(2)}`,
              typeof name === 'string' ? name.charAt(0).toUpperCase() + name.slice(1) : String(name)
            ]}
          />
          
          {/* Candlestick wicks */}
          <Line
            type="linear"
            dataKey="wickTop"
            stroke="hsl(var(--muted-foreground))"
            strokeWidth={1}
            dot={false}
            connectNulls={false}
          />
          <Line
            type="linear"
            dataKey="wickBottom"
            stroke="hsl(var(--muted-foreground))"
            strokeWidth={1}
            dot={false}
            connectNulls={false}
          />
          
          {/* Candlestick bodies */}
          <Bar 
            dataKey="bodyHeight" 
            fill="hsl(var(--trading-green))"
            stroke="hsl(var(--border))"
          />
          
          {/* Volume bars at bottom */}
          <Bar 
            dataKey="volume" 
            fill="hsl(var(--muted))"
            opacity={0.3}
            yAxisId="volume"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};