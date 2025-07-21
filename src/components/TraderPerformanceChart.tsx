import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, Area, AreaChart } from 'recharts';

interface TraderPerformanceChartProps {
  traderId: number;
  color: string;
}

const generatePerformanceData = (traderId: number) => {
  const data = [];
  let pnl = 0;
  let portfolio = 100000; // Starting with $100k
  
  for (let i = 0; i < 14; i++) {
    const dailyReturn = (Math.random() - 0.48) * 0.05; // Slightly positive bias
    const dailyPnL = portfolio * dailyReturn;
    pnl += dailyPnL;
    portfolio += dailyPnL;
    
    data.push({
      day: `Day ${i + 1}`,
      date: new Date(Date.now() - (13 - i) * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      pnl: pnl,
      portfolio: portfolio,
      dailyPnL: dailyPnL,
      return: (portfolio - 100000) / 100000 * 100
    });
  }
  
  return data;
};

export const TraderPerformanceChart = ({ traderId, color }: TraderPerformanceChartProps) => {
  const performanceData = generatePerformanceData(traderId);
  const latestData = performanceData[performanceData.length - 1];
  const isProfit = latestData.pnl >= 0;
  const chartColor = isProfit ? 'hsl(var(--trading-green))' : 'hsl(var(--trading-red))';

  return (
    <div className="space-y-4">
      {/* Performance Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center">
          <div className="text-sm text-muted-foreground">Total P&L</div>
          <div className={`text-lg font-bold ${isProfit ? 'text-trading-green' : 'text-trading-red'}`}>
            {isProfit ? '+' : ''}${latestData.pnl.toFixed(2)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-muted-foreground">Return</div>
          <div className={`text-lg font-bold ${isProfit ? 'text-trading-green' : 'text-trading-red'}`}>
            {isProfit ? '+' : ''}{latestData.return.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* Performance Chart */}
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={performanceData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
            <defs>
              <linearGradient id={`gradient-${traderId}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={chartColor} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={chartColor} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--chart-grid))" />
            <XAxis 
              dataKey="date" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(var(--chart-text))', fontSize: 10 }}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(var(--chart-text))', fontSize: 10 }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                color: 'hsl(var(--card-foreground))',
                fontSize: '12px'
              }}
              formatter={(value, name) => [
                name === 'portfolio' ? `$${(value as number).toFixed(2)}` : `$${(value as number).toFixed(2)}`,
                name === 'portfolio' ? 'Portfolio Value' : 'P&L'
              ]}
            />
            <Area
              type="monotone"
              dataKey="portfolio"
              stroke={chartColor}
              strokeWidth={2}
              fill={`url(#gradient-${traderId})`}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};