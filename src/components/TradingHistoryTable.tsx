import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface Trader {
  id: number;
  name: string;
  color: string;
}

interface TradingHistoryTableProps {
  traders: Trader[];
}

const generateTradingHistory = () => {
  const symbols = ['BTC', 'ETH', 'AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN', 'NVDA', 'META', 'NFLX'];
  const sides = ['BUY', 'SELL'];
  const data = [];
  
  for (let i = 0; i < 25; i++) {
    const symbol = symbols[Math.floor(Math.random() * symbols.length)];
    const side = sides[Math.floor(Math.random() * sides.length)];
    const quantity = Math.random() * 100 + 1;
    const price = Math.random() * 1000 + 10;
    const traderId = Math.floor(Math.random() * 3) + 1;
    const daysAgo = Math.floor(Math.random() * 14);
    const date = new Date(Date.now() - daysAgo * 24 * 60 * 60 * 1000);
    
    data.push({
      id: i + 1,
      timestamp: date,
      symbol,
      side,
      quantity: quantity.toFixed(2),
      price: price.toFixed(2),
      total: (quantity * price).toFixed(2),
      traderId,
      status: Math.random() > 0.1 ? 'FILLED' : 'PARTIAL'
    });
  }
  
  return data.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
};

export const TradingHistoryTable = ({ traders }: TradingHistoryTableProps) => {
  const tradingHistory = generateTradingHistory();

  const getTraderName = (traderId: number) => {
    return traders.find(t => t.id === traderId)?.name || 'Unknown';
  };

  const getTraderColor = (traderId: number) => {
    const trader = traders.find(t => t.id === traderId);
    return trader?.color === 'trading-blue' ? 'bg-trading-blue' : 
           trader?.color === 'trading-yellow' ? 'bg-trading-yellow' : 'bg-trading-purple';
  };

  const formatDateTime = (date: Date) => {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="max-h-96 overflow-auto">
      <Table>
        <TableHeader>
          <TableRow className="border-border">
            <TableHead className="text-muted-foreground">Date/Time</TableHead>
            <TableHead className="text-muted-foreground">Symbol</TableHead>
            <TableHead className="text-muted-foreground">Side</TableHead>
            <TableHead className="text-muted-foreground">Trader</TableHead>
            <TableHead className="text-muted-foreground text-right">Quantity</TableHead>
            <TableHead className="text-muted-foreground text-right">Price</TableHead>
            <TableHead className="text-muted-foreground text-right">Total</TableHead>
            <TableHead className="text-muted-foreground">Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tradingHistory.map((trade) => (
            <TableRow key={trade.id} className="border-border hover:bg-muted/50">
              <TableCell className="text-foreground text-sm">
                {formatDateTime(trade.timestamp)}
              </TableCell>
              <TableCell className="font-medium text-foreground">{trade.symbol}</TableCell>
              <TableCell>
                <Badge 
                  variant="outline" 
                  className={`${trade.side === 'BUY' ? 'bg-trading-green text-white border-trading-green' : 'bg-trading-red text-white border-trading-red'}`}
                >
                  {trade.side}
                </Badge>
              </TableCell>
              <TableCell>
                <Badge variant="outline" className={`${getTraderColor(trade.traderId)} text-white border-none`}>
                  {getTraderName(trade.traderId)}
                </Badge>
              </TableCell>
              <TableCell className="text-right text-foreground">{trade.quantity}</TableCell>
              <TableCell className="text-right text-foreground">${trade.price}</TableCell>
              <TableCell className="text-right text-foreground">${trade.total}</TableCell>
              <TableCell>
                <Badge 
                  variant="outline" 
                  className={`${trade.status === 'FILLED' ? 'bg-muted text-foreground border-border' : 'bg-trading-yellow text-black border-trading-yellow'}`}
                >
                  {trade.status}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};