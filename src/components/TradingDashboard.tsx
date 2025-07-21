import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CandlestickChart } from "./CandlestickChart";
import { TraderPerformanceChart } from "./TraderPerformanceChart";
import { PortfolioTable } from "./PortfolioTable";
import { TradingHistoryTable } from "./TradingHistoryTable";

export const TradingDashboard = () => {
  const traders = [
    { id: 1, name: "Alex Chen", color: "trading-blue" },
    { id: 2, name: "Sarah Kim", color: "trading-yellow" },
    { id: 3, name: "Marcus Johnson", color: "trading-purple" }
  ];

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Trading Dashboard</h1>
            <p className="text-muted-foreground">Real-time trading performance and portfolio tracking</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground">Last Updated</div>
            <div className="text-lg font-semibold">{new Date().toLocaleTimeString()}</div>
          </div>
        </div>

        {/* Candlestick Chart */}
        <Card className="bg-card border-border shadow-lg">
          <CardHeader>
            <CardTitle className="text-xl text-card-foreground">Market Overview - BTC/USD</CardTitle>
          </CardHeader>
          <CardContent>
            <CandlestickChart />
          </CardContent>
        </Card>

        {/* Trader Performance Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {traders.map((trader) => (
            <Card key={trader.id} className="bg-card border-border shadow-lg">
              <CardHeader>
                <CardTitle className="text-lg text-card-foreground">{trader.name} Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <TraderPerformanceChart traderId={trader.id} color={trader.color} />
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Portfolio and Trading History */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <Card className="bg-card border-border shadow-lg">
            <CardHeader>
              <CardTitle className="text-xl text-card-foreground">Current Portfolio</CardTitle>
            </CardHeader>
            <CardContent>
              <PortfolioTable traders={traders} />
            </CardContent>
          </Card>

          <Card className="bg-card border-border shadow-lg">
            <CardHeader>
              <CardTitle className="text-xl text-card-foreground">Trading History (Last 2 Weeks)</CardTitle>
            </CardHeader>
            <CardContent>
              <TradingHistoryTable traders={traders} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};