import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState, useEffect, useCallback, memo } from "react";
import { apiClient } from "@/services/api";

interface Trader {
  id: number;
  name: string;
  color: string;
}

interface TradingHistoryTableProps {
  traders: Trader[];
  traderId?: number; // Optional: if provided, filter by this trader
}

// Memoized table row component to prevent unnecessary re-renders
const TradingHistoryRow = memo(({ 
  trade, 
  showTrader, 
  getTraderName, 
  getTraderColor,
  formatDateTime 
}: { 
  trade: any; 
  showTrader: boolean; 
  getTraderName: (id: number) => string; 
  getTraderColor: (id: number) => string;
  formatDateTime: (date: Date) => string;
}) => {
  const sideColor = trade.side === 'BUY' 
    ? 'bg-trading-green text-white border-trading-green' 
    : 'bg-trading-red text-white border-trading-red';
  
  const statusColor = trade.status === 'FILLED' 
    ? 'bg-muted text-foreground border-border' 
    : 'bg-trading-yellow text-black border-trading-yellow';

  return (
    <TableRow className="border-border hover:bg-muted/50">
      <TableCell className="text-foreground text-sm">
        {formatDateTime(trade.timestamp)}
      </TableCell>
      <TableCell className="font-medium text-foreground">{trade.symbol}</TableCell>
      <TableCell>
        <Badge variant="outline" className={sideColor}>
          {trade.side}
        </Badge>
      </TableCell>
      {showTrader && (
        <TableCell>
          <Badge variant="outline" className={`${getTraderColor(trade.traderId)} text-white border-none`}>
            {getTraderName(trade.traderId)}
          </Badge>
        </TableCell>
      )}
      <TableCell className="text-right text-foreground">{trade.quantity}</TableCell>
      <TableCell className="text-right text-foreground">${trade.price}</TableCell>
      <TableCell className="text-right text-foreground">${trade.total}</TableCell>
      <TableCell>
        <Badge variant="outline" className={statusColor}>
          {trade.status}
        </Badge>
      </TableCell>
    </TableRow>
  );
});

TradingHistoryRow.displayName = 'TradingHistoryRow';

export const TradingHistoryTable = ({ traders, traderId }: TradingHistoryTableProps) => {
  const [tradingHistory, setTradingHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdateHash, setLastUpdateHash] = useState<string>('');
  const [showReasons, setShowReasons] = useState(false);
  const [expandedReasons, setExpandedReasons] = useState<Set<string>>(new Set());

  // Memoized helper functions to prevent unnecessary re-renders
  const getTraderName = useCallback((traderId: number) => {
    return traders.find(t => t.id === traderId)?.name || 'Unknown';
  }, [traders]);

  const getTraderColor = useCallback((traderId: number) => {
    const trader = traders.find(t => t.id === traderId);
    return trader?.color === 'trading-blue' ? 'bg-trading-blue' : 
           trader?.color === 'trading-yellow' ? 'bg-trading-yellow' : 'bg-trading-purple';
  }, [traders]);

  const formatDateTime = useCallback((date: Date) => {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }, []);

  // Helper functions for reasoning expansion
  const toggleReasoningExpansion = useCallback((tradeId: string) => {
    setExpandedReasons(prev => {
      const newSet = new Set(prev);
      if (newSet.has(tradeId)) {
        newSet.delete(tradeId);
      } else {
        newSet.add(tradeId);
      }
      return newSet;
    });
  }, []);

  const getTruncatedReasoning = useCallback((reasoning: string, maxLength: number = 150) => {
    if (!reasoning || reasoning.length <= maxLength) return reasoning;
    return reasoning.substring(0, maxLength) + '...';
  }, []);

  // Function to format trade data
  const formatTrade = useCallback((trade: any, index: number, traderID: number) => ({
    id: traderId ? index + 1 : `${traderID}-${index}`,
    timestamp: new Date(trade.timestamp),
    symbol: trade.symbol,
    side: trade.side,
    quantity: trade.quantity.toString(),
    price: trade.price.toFixed(2),
    total: trade.total.toFixed(2),
    traderId: traderID,
    status: trade.status,
    reasoning: trade.reasoning || 'No reasoning provided'
  }), [traderId]);

  // Function to check if data has actually changed
  const hasDataChanged = useCallback((newData: any[]) => {
    const newHash = JSON.stringify(newData.map(item => ({
      id: item.id,
      timestamp: item.timestamp.getTime(),
      symbol: item.symbol,
      side: item.side,
      quantity: item.quantity,
      price: item.price,
      total: item.total,
      status: item.status
    })));
    
    if (newHash !== lastUpdateHash) {
      setLastUpdateHash(newHash);
      return true;
    }
    return false;
  }, [lastUpdateHash]);

  const fetchTradingHistory = useCallback(async () => {
    try {
      // Only show loading spinner on initial load
      if (tradingHistory.length === 0) {
        setLoading(true);
      }
      
      let newTradingData: any[] = [];
      
      if (traderId) {
        // Get data for specific trader
        const trader = traders.find(t => t.id === traderId);
        if (trader) {
          const data = await apiClient.getTraderTrades(trader.name.toLowerCase());
          newTradingData = data.trades.map((trade: any, index: number) => 
            formatTrade(trade, index, traderId)
          );
        }
      } else {
        // Get data for all traders
        const allTrades: any[] = [];
        for (let i = 0; i < traders.length; i++) {
          const trader = traders[i];
          try {
            const data = await apiClient.getTraderTrades(trader.name.toLowerCase());
            const formattedTrades = data.trades.map((trade: any, index: number) => 
              formatTrade(trade, index, trader.id)
            );
            allTrades.push(...formattedTrades);
          } catch (error) {
            console.error(`Error fetching trades for ${trader.name}:`, error);
          }
        }
        // Sort by timestamp (newest first)
        allTrades.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
        newTradingData = allTrades;
      }
      
      // Only update state if data has actually changed
      if (hasDataChanged(newTradingData)) {
        setTradingHistory(newTradingData);
      }
      
    } catch (error) {
      console.error('Error fetching trading history:', error);
      if (tradingHistory.length === 0) {
        setTradingHistory([]);
      }
    } finally {
      setLoading(false);
    }
  }, [traders, traderId, tradingHistory.length, formatTrade, hasDataChanged]);

  useEffect(() => {
    fetchTradingHistory();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchTradingHistory, 30000);
    return () => clearInterval(interval);
  }, [fetchTradingHistory]);

  // Create skeleton rows that match the table structure
  const SkeletonRow = () => (
    <TableRow className="border-border">
      <TableCell>
        <div className="h-4 bg-muted/30 rounded w-20 animate-pulse"></div>
      </TableCell>
      <TableCell>
        <div className="h-4 bg-muted/30 rounded w-16 animate-pulse"></div>
      </TableCell>
      <TableCell>
        <div className="h-6 bg-muted/30 rounded w-12 animate-pulse"></div>
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
        <div className="h-4 bg-muted/30 rounded w-20 ml-auto animate-pulse"></div>
      </TableCell>
      <TableCell>
        <div className="h-6 bg-muted/30 rounded w-16 animate-pulse"></div>
      </TableCell>
    </TableRow>
  );

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-[420px] overflow-auto">
          <Table>
            <TableHeader className="sticky top-0 bg-background z-10">
              <TableRow className="border-border">
                <TableHead className="text-muted-foreground">Date/Time</TableHead>
                <TableHead className="text-muted-foreground">Symbol</TableHead>
                <TableHead className="text-muted-foreground">Side</TableHead>
                {!traderId && <TableHead className="text-muted-foreground">Trader</TableHead>}
                <TableHead className="text-muted-foreground text-right">Quantity</TableHead>
                <TableHead className="text-muted-foreground text-right">Price</TableHead>
                <TableHead className="text-muted-foreground text-right">Total</TableHead>
                <TableHead className="text-muted-foreground">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Array.from({ length: 10 }).map((_, index) => (
                <SkeletonRow key={index} />
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    );
  }

  if (tradingHistory.length === 0) {
    return (
      <div className="space-y-4">
        <div className="h-[420px] overflow-auto">
          <Table>
            <TableHeader className="sticky top-0 bg-background z-10">
              <TableRow className="border-border">
                <TableHead className="text-muted-foreground">Date/Time</TableHead>
                <TableHead className="text-muted-foreground">Symbol</TableHead>
                <TableHead className="text-muted-foreground">Side</TableHead>
                {!traderId && <TableHead className="text-muted-foreground">Trader</TableHead>}
                <TableHead className="text-muted-foreground text-right">Quantity</TableHead>
                <TableHead className="text-muted-foreground text-right">Price</TableHead>
                <TableHead className="text-muted-foreground text-right">Total</TableHead>
                <TableHead className="text-muted-foreground">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell colSpan={traderId ? 7 : 8} className="text-center text-muted-foreground py-8">
                  No trades found
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Trading History Table */}
      <div className="h-[420px] overflow-auto">
        <Table>
          <TableHeader className="sticky top-0 bg-background z-10">
            <TableRow className="border-border">
              <TableHead className="text-muted-foreground">Date/Time</TableHead>
              <TableHead className="text-muted-foreground">Symbol</TableHead>
              <TableHead className="text-muted-foreground">Side</TableHead>
              {!traderId && <TableHead className="text-muted-foreground">Trader</TableHead>}
              <TableHead className="text-muted-foreground text-right">Quantity</TableHead>
              <TableHead className="text-muted-foreground text-right">Price</TableHead>
              <TableHead className="text-muted-foreground text-right">Total</TableHead>
              <TableHead className="text-muted-foreground">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tradingHistory.map((trade) => (
              <TradingHistoryRow
                key={trade.id}
                trade={trade}
                showTrader={!traderId}
                getTraderName={getTraderName}
                getTraderColor={getTraderColor}
                formatDateTime={formatDateTime}
              />
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Trading Reasons Section */}
      {tradingHistory.length > 0 && (
        <div className="border rounded-lg">
          <Button
            variant="ghost"
            onClick={() => setShowReasons(!showReasons)}
            className="w-full flex items-center justify-between p-4 hover:bg-muted/50"
          >
            <span className="font-medium">Trading Reasons</span>
            {showReasons ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
          
          {showReasons && (
            <div className="border-t max-h-[300px] overflow-auto">
              <Table>
                <TableHeader className="sticky top-0 bg-background z-10">
                  <TableRow className="border-border">
                    <TableHead className="text-muted-foreground w-32">Symbol</TableHead>
                    <TableHead className="text-muted-foreground w-20">Side</TableHead>
                    <TableHead className="text-muted-foreground w-24">Date</TableHead>
                    <TableHead className="text-muted-foreground">Reasoning</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tradingHistory.map((trade) => {
                    const tradeId = `reason-${trade.id}`;
                    const isExpanded = expandedReasons.has(tradeId);
                    const reasoning = trade.reasoning || 'No reasoning available';
                    const needsExpansion = reasoning.length > 150;
                    
                    return (
                      <TableRow key={tradeId} className="border-border">
                        <TableCell className="font-medium text-foreground">{trade.symbol}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className={
                            trade.side === 'BUY' 
                              ? 'bg-trading-green text-white border-trading-green' 
                              : 'bg-trading-red text-white border-trading-red'
                          }>
                            {trade.side}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-foreground text-sm">
                          {formatDateTime(trade.timestamp)}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm leading-relaxed">
                          <div className="space-y-2">
                            <div>
                              {isExpanded ? reasoning : getTruncatedReasoning(reasoning)}
                            </div>
                            {needsExpansion && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => toggleReasoningExpansion(tradeId)}
                                className="h-6 px-2 text-xs text-trading-blue hover:text-trading-blue hover:bg-trading-blue/10"
                              >
                                {isExpanded ? (
                                  <>
                                    <ChevronUp className="h-3 w-3 mr-1" />
                                    Show less
                                  </>
                                ) : (
                                  <>
                                    <ChevronDown className="h-3 w-3 mr-1" />
                                    Read more
                                  </>
                                )}
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};