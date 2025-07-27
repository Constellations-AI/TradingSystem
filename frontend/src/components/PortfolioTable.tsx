import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useState, useEffect, useMemo, useCallback, memo } from "react";
import { apiClient, TraderPortfolio } from "@/services/api";

interface Trader {
  id: number;
  name: string;
  color: string;
}

interface PortfolioTableProps {
  traders: Trader[];
  traderId?: number; // Optional: if provided, filter by this trader
}

// Memoized table row component to prevent unnecessary re-renders
const PortfolioRow = memo(({ 
  row, 
  showTrader, 
  getTraderName, 
  getTraderColor 
}: { 
  row: any; 
  showTrader: boolean; 
  getTraderName: (id: number) => string; 
  getTraderColor: (id: number) => string; 
}) => {
  const isProfitable = parseFloat(row.pnl) >= 0;
  const pnlColor = isProfitable ? 'text-trading-green' : 'text-trading-red';
  const pnlSign = isProfitable ? '+' : '';
  
  return (
    <TableRow key={row.id} className="border-border hover:bg-muted/50">
      <TableCell className="font-medium text-foreground">{row.symbol}</TableCell>
      {showTrader && (
        <TableCell>
          <Badge variant="outline" className={`${getTraderColor(row.traderId)} text-white border-none`}>
            {getTraderName(row.traderId)}
          </Badge>
        </TableCell>
      )}
      <TableCell className="text-right text-foreground">{row.quantity}</TableCell>
      <TableCell className="text-right text-foreground">${row.avgPrice}</TableCell>
      <TableCell className="text-right text-foreground">${row.currentPrice}</TableCell>
      <TableCell className="text-right text-foreground">${row.marketValue}</TableCell>
      <TableCell className="text-right">
        <span className={pnlColor}>
          {pnlSign}${row.pnl} ({pnlSign}{row.pnlPercent}%)
        </span>
      </TableCell>
    </TableRow>
  );
});

PortfolioRow.displayName = 'PortfolioRow';

export const PortfolioTable = ({ traders, traderId }: PortfolioTableProps) => {
  const [portfolioData, setPortfolioData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdateHash, setLastUpdateHash] = useState<string>('');

  // Memoized trader lookup functions to prevent unnecessary re-renders
  const getTraderName = useCallback((traderId: number) => {
    return traders.find(t => t.id === traderId)?.name || 'Unknown';
  }, [traders]);

  const getTraderColor = useCallback((traderId: number) => {
    const trader = traders.find(t => t.id === traderId);
    return trader?.color === 'trading-blue' ? 'bg-trading-blue' : 
           trader?.color === 'trading-yellow' ? 'bg-trading-yellow' : 'bg-trading-purple';
  }, [traders]);

  // Function to calculate formatted holding data
  const formatHolding = useCallback((holding: any, index: number, traderID: number, tradesData: any) => {
    // Calculate average price from trading history
    const symbolTrades = tradesData.trades.filter((trade: any) => 
      trade.symbol === holding.symbol && trade.side === 'BUY'
    );
    
    let avgPrice = 0;
    let totalQuantity = 0;
    let totalCost = 0;
    
    symbolTrades.forEach((trade: any) => {
      totalQuantity += trade.quantity;
      totalCost += trade.quantity * trade.price;
    });
    
    if (totalQuantity > 0) {
      avgPrice = totalCost / totalQuantity;
    }
    
    // Calculate P&L
    const currentValue = holding.current_price * holding.quantity;
    const costBasis = avgPrice * holding.quantity;
    const pnl = currentValue - costBasis;
    const pnlPercent = costBasis > 0 ? (pnl / costBasis) * 100 : 0;
    
    return {
      id: traderId ? index + 1 : `${traderID}-${index}`,
      symbol: holding.symbol,
      quantity: holding.quantity.toString(),
      avgPrice: avgPrice > 0 ? avgPrice.toFixed(2) : "N/A",
      currentPrice: holding.current_price.toFixed(2),
      marketValue: holding.market_value.toFixed(2),
      pnl: avgPrice > 0 ? pnl.toFixed(2) : "N/A",
      pnlPercent: avgPrice > 0 ? pnlPercent.toFixed(2) : "N/A",
      traderId: traderID
    };
  }, [traderId]);

  // Function to check if data has actually changed
  const hasDataChanged = useCallback((newData: any[]) => {
    const newHash = JSON.stringify(newData.map(item => ({
      symbol: item.symbol,
      quantity: item.quantity,
      currentPrice: item.currentPrice,
      marketValue: item.marketValue,
      pnl: item.pnl
    })));
    
    if (newHash !== lastUpdateHash) {
      setLastUpdateHash(newHash);
      return true;
    }
    return false;
  }, [lastUpdateHash]);

  const fetchPortfolioData = useCallback(async () => {
    try {
      // Only show loading spinner on initial load
      if (portfolioData.length === 0) {
        setLoading(true);
      }
      
      let newPortfolioData: any[] = [];
      
      if (traderId) {
        // Get data for specific trader
        const trader = traders.find(t => t.id === traderId);
        if (trader) {
          const [portfolioResponse, tradesData] = await Promise.all([
            apiClient.getTraderPortfolio(trader.name.toLowerCase()),
            apiClient.getTraderTrades(trader.name.toLowerCase())
          ]);
          
          newPortfolioData = portfolioResponse.holdings.map((holding: any, index: number) => 
            formatHolding(holding, index, traderId, tradesData)
          );
        }
      } else {
        // Get data for all traders
        const allHoldings: any[] = [];
        for (let i = 0; i < traders.length; i++) {
          const trader = traders[i];
          try {
            const [portfolioResponse, tradesData] = await Promise.all([
              apiClient.getTraderPortfolio(trader.name.toLowerCase()),
              apiClient.getTraderTrades(trader.name.toLowerCase())
            ]);
            
            const formattedHoldings = portfolioResponse.holdings.map((holding: any, index: number) => 
              formatHolding(holding, index, trader.id, tradesData)
            );
            allHoldings.push(...formattedHoldings);
          } catch (error) {
            console.error(`Error fetching data for ${trader.name}:`, error);
          }
        }
        newPortfolioData = allHoldings;
      }
      
      // Only update state if data has actually changed
      if (hasDataChanged(newPortfolioData)) {
        setPortfolioData(newPortfolioData);
      }
      
    } catch (error) {
      console.error('Error fetching portfolio data:', error);
      if (portfolioData.length === 0) {
        setPortfolioData([]);
      }
    } finally {
      setLoading(false);
    }
  }, [traders, traderId, portfolioData.length, formatHolding, hasDataChanged]);

  useEffect(() => {
    fetchPortfolioData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchPortfolioData, 30000);
    return () => clearInterval(interval);
  }, [fetchPortfolioData]);

  // Create skeleton rows that match the table structure
  const SkeletonRow = () => (
    <TableRow className="border-border">
      <TableCell className="font-medium">
        <div className="h-4 bg-muted/30 rounded w-16 animate-pulse"></div>
      </TableCell>
      {!traderId && (
        <TableCell>
          <div className="h-6 bg-muted/30 rounded w-20 animate-pulse"></div>
        </TableCell>
      )}
      <TableCell className="text-right">
        <div className="h-4 bg-muted/30 rounded w-12 ml-auto animate-pulse"></div>
      </TableCell>
      <TableCell className="text-right">
        <div className="h-4 bg-muted/30 rounded w-16 ml-auto animate-pulse"></div>
      </TableCell>
      <TableCell className="text-right">
        <div className="h-4 bg-muted/30 rounded w-16 ml-auto animate-pulse"></div>
      </TableCell>
      <TableCell className="text-right">
        <div className="h-4 bg-muted/30 rounded w-20 ml-auto animate-pulse"></div>
      </TableCell>
      <TableCell className="text-right">
        <div className="h-4 bg-muted/30 rounded w-24 ml-auto animate-pulse"></div>
      </TableCell>
    </TableRow>
  );

  if (loading) {
    return (
      <div className="h-[280px] overflow-auto">
        <Table>
          <TableHeader className="sticky top-0 bg-background z-10">
            <TableRow className="border-border">
              <TableHead className="text-muted-foreground">Symbol</TableHead>
              {!traderId && <TableHead className="text-muted-foreground">Trader</TableHead>}
              <TableHead className="text-muted-foreground text-right">Quantity</TableHead>
              <TableHead className="text-muted-foreground text-right">Avg Price</TableHead>
              <TableHead className="text-muted-foreground text-right">Current Price</TableHead>
              <TableHead className="text-muted-foreground text-right">Market Value</TableHead>
              <TableHead className="text-muted-foreground text-right">P&L</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, index) => (
              <SkeletonRow key={index} />
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  if (portfolioData.length === 0) {
    return (
      <div className="h-[280px] overflow-auto">
        <Table>
          <TableHeader className="sticky top-0 bg-background z-10">
            <TableRow className="border-border">
              <TableHead className="text-muted-foreground">Symbol</TableHead>
              {!traderId && <TableHead className="text-muted-foreground">Trader</TableHead>}
              <TableHead className="text-muted-foreground text-right">Quantity</TableHead>
              <TableHead className="text-muted-foreground text-right">Avg Price</TableHead>
              <TableHead className="text-muted-foreground text-right">Current Price</TableHead>
              <TableHead className="text-muted-foreground text-right">Market Value</TableHead>
              <TableHead className="text-muted-foreground text-right">P&L</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell colSpan={traderId ? 6 : 7} className="text-center text-muted-foreground py-8">
                No holdings found
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    );
  }

  return (
    <div className="h-[280px] overflow-auto">
      <Table>
        <TableHeader className="sticky top-0 bg-background z-10">
          <TableRow className="border-border">
            <TableHead className="text-muted-foreground">Symbol</TableHead>
            {!traderId && <TableHead className="text-muted-foreground">Trader</TableHead>}
            <TableHead className="text-muted-foreground text-right">Quantity</TableHead>
            <TableHead className="text-muted-foreground text-right">Avg Price</TableHead>
            <TableHead className="text-muted-foreground text-right">Current Price</TableHead>
            <TableHead className="text-muted-foreground text-right">Market Value</TableHead>
            <TableHead className="text-muted-foreground text-right">P&L</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {portfolioData.map((row) => (
            <PortfolioRow
              key={row.id}
              row={row}
              showTrader={!traderId}
              getTraderName={getTraderName}
              getTraderColor={getTraderColor}
            />
          ))}
        </TableBody>
      </Table>
    </div>
  );
};