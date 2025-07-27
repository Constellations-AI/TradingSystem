import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { CandlestickChart } from "./CandlestickChart";
import { TraderPerformanceChart } from "./TraderPerformanceChart";
import { PortfolioTable } from "./PortfolioTable";
import { TradingHistoryTable } from "./TradingHistoryTable";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export const TradingDashboard = () => {
  const [selectedSymbol, setSelectedSymbol] = useState("SPY");
  const navigate = useNavigate();
  
  const traders = [
    { id: 1, name: "warren", displayName: "Warren", color: "trading-blue" },
    { id: 4, name: "camillo", displayName: "Camillo", color: "trading-yellow" },
    { id: 3, name: "pavel", displayName: "Pavel", color: "trading-purple" }
  ];

  const availableSymbols = [
    { value: "SPY", label: "SPY - S&P 500 ETF" },
    { value: "AAPL", label: "AAPL - Apple Inc." },
    { value: "TSLA", label: "TSLA - Tesla Inc." },
    { value: "NVDA", label: "NVDA - NVIDIA Corp." },
    { value: "MSFT", label: "MSFT - Microsoft Corp." },
    { value: "BTC", label: "BTC - Bitcoin" },
    { value: "ETH", label: "ETH - Ethereum" }
  ];

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/')}
              className="flex items-center gap-2 hover:bg-trading-green/10 hover:text-trading-green hover:border-trading-green/40"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Home
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-foreground">Trading Dashboard</h1>
              <p className="text-muted-foreground">Real-time trading performance and portfolio tracking</p>
            </div>
          </div>
        </div>

        {/* Project Background */}
        <Card className="bg-card/80 backdrop-blur-sm border-trading-blue/20">
          <CardContent className="p-6">
            <div className="space-y-4 text-muted-foreground leading-relaxed">
              <p>
                This project evolved from a multi-agent intelligence collection and analysis system I originally built for a client. Rather than using LangGraph agents to perform deep research for intelligence assessments, I repurposed them to analyze market news and stock movements. As it turns out, the two domains overlap more than you'd expect.
              </p>
              <p>
                The idea of assigning "trader personalities" was inspired by my current obsession with Jack Schwager's Market Wizards series. I'm fascinated by the intersection of logic and intuition - the way elite traders make seemingly unforeseeable predictions by fluidly moving between art and science.
              </p>
              <p>
                Instead of simply prompting the models to "maximize profit," I designed them to learn from the decision-making patterns of human masters. I'm currently prototyping with GPT-4o, and plan to begin fine-tuning open-source models once I've gathered enough training data.
              </p>
              <p className="text-sm text-muted-foreground/80 border-t border-muted/20 pt-4 mt-6">
                <strong>Disclaimer:</strong> This is a personal research experiment adapting multi-agent frameworks from my client work into financial sector applications. It has no affiliation with the trading personalities depicted and provides no investment recommendations. The algorithms are continuously evolving as part of ongoing research—even I wouldn't follow these trades! This is purely a demonstration of autonomous agent orchestration in financial domains.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Last Updated Info */}
        <div className="flex justify-end">
          <div className="text-right">
            <div className="text-sm text-muted-foreground">Last Updated</div>
            <div className="text-lg font-semibold">{new Date().toLocaleTimeString()}</div>
          </div>
        </div>

        {/* Candlestick Chart */}
        <Card className="bg-card border-border shadow-lg">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-xl text-card-foreground">Market Overview</CardTitle>
              <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Select symbol" />
                </SelectTrigger>
                <SelectContent>
                  {availableSymbols.map((symbol) => (
                    <SelectItem key={symbol.value} value={symbol.value}>
                      {symbol.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            <CandlestickChart symbol={selectedSymbol} />
          </CardContent>
        </Card>

        {/* Trader Performance Charts with Individual Portfolio and Trading History */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {traders.map((trader) => (
            <div key={trader.id} className="space-y-6">
              {/* Trader Performance Chart */}
              <Card className="bg-card border-border shadow-lg">
                <CardHeader>
                  <CardTitle className="text-lg text-card-foreground">{trader.displayName} Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <TraderPerformanceChart 
                    traderId={trader.id} 
                    color={trader.color} 
                    traderName={trader.displayName} 
                  />
                </CardContent>
              </Card>

              {/* Individual Portfolio Table */}
              <Card className="bg-card border-border shadow-lg">
                <CardHeader>
                  <CardTitle className="text-lg text-card-foreground">{trader.displayName}'s Portfolio</CardTitle>
                </CardHeader>
                <CardContent>
                  <PortfolioTable traders={traders} traderId={trader.id} />
                </CardContent>
              </Card>

              {/* Individual Trading History Table */}
              <Card className="bg-card border-border shadow-lg">
                <CardHeader>
                  <CardTitle className="text-lg text-card-foreground">{trader.displayName}'s Trading History</CardTitle>
                </CardHeader>
                <CardContent>
                  <TradingHistoryTable traders={traders} traderId={trader.id} />
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};