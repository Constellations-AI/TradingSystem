import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, Area, AreaChart } from 'recharts';
import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/services/api';

interface TraderPerformanceChartProps {
  traderId: number;
  color: string;
  traderName: string;
}

// This will be replaced with real API data

export const TraderPerformanceChart = ({ traderId, color, traderName }: TraderPerformanceChartProps) => {
  const [performanceData, setPerformanceData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [traderStats, setTraderStats] = useState({
    totalPnl: 0,
    totalReturn: 0,
    currentValue: 0
  });
  const [lastUpdateHash, setLastUpdateHash] = useState<string>('');

  // Function to check if performance data has actually changed
  const hasDataChanged = useCallback((newData: any[], newStats: any) => {
    const newHash = JSON.stringify({
      dataPoints: newData.map(point => ({
        date: point.date,
        portfolio: point.portfolio,
        pnl: point.pnl
      })),
      stats: {
        totalPnl: newStats.totalPnl,
        totalReturn: newStats.totalReturn,
        currentValue: newStats.currentValue
      }
    });
    
    if (newHash !== lastUpdateHash) {
      setLastUpdateHash(newHash);
      return true;
    }
    return false;
  }, [lastUpdateHash]);

  const fetchPerformanceData = useCallback(async () => {
    try {
      // Only show loading on initial fetch
      if (performanceData.length === 0) {
        setLoading(true);
      }
      const data = await apiClient.getTraderPerformance(traderName.toLowerCase());
        
      // Transform the performance history for the chart
      const chartData = data.performance_history.map((point) => ({
        date: new Date(point.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        portfolio: point.portfolio_value,
        pnl: point.portfolio_value - data.starting_value,
        return: ((point.portfolio_value - data.starting_value) / data.starting_value) * 100
      }));
      
      const newStats = {
        totalPnl: data.total_pnl,
        totalReturn: data.total_return,
        currentValue: data.current_value
      };
      
      // Only update state if data has actually changed
      if (hasDataChanged(chartData, newStats)) {
        setPerformanceData(chartData);
        setTraderStats(newStats);
      }
    } catch (error) {
      console.error(`Error fetching performance for ${traderName}:`, error);
      if (performanceData.length === 0) {
        setPerformanceData([]);
      }
    } finally {
      setLoading(false);
    }
  }, [traderName, performanceData.length, hasDataChanged]);

  useEffect(() => {
    fetchPerformanceData();
    
    // Refresh every hour (3600 seconds = 60 minutes)
    const interval = setInterval(fetchPerformanceData, 3600000);
    return () => clearInterval(interval);
  }, [fetchPerformanceData]);

  const isProfit = traderStats.totalPnl >= 0;
  const chartColor = isProfit ? 'hsl(var(--trading-green))' : 'hsl(var(--trading-red))';

  if (loading) {
    return (
      <div className="space-y-4">
        {/* Performance Stats - Skeleton */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <div className="text-sm text-muted-foreground">Total P&L</div>
            <div className="text-lg font-bold text-muted-foreground">Loading...</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-muted-foreground">Return</div>
            <div className="text-lg font-bold text-muted-foreground">Loading...</div>
          </div>
        </div>

        {/* Performance Chart - Fixed Size Container */}
        <div className="h-48 flex items-center justify-center bg-muted/10 rounded">
          <div className="text-muted-foreground text-sm">Loading performance...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Performance Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center">
          <div className="text-sm text-muted-foreground">Total P&L</div>
          <div className={`text-lg font-bold ${isProfit ? 'text-trading-green' : 'text-trading-red'}`}>
            {isProfit ? '+' : ''}${traderStats.totalPnl.toFixed(2)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-muted-foreground">Return</div>
          <div className={`text-lg font-bold ${isProfit ? 'text-trading-green' : 'text-trading-red'}`}>
            {isProfit ? '+' : ''}{traderStats.totalReturn.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* Performance Chart */}
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%" minHeight={192} minWidth={0}>
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