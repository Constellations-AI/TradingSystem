import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface Trader {
  id: number;
  name: string;
  color: string;
}

interface PortfolioTableProps {
  traders: Trader[];
}

const generatePortfolioData = () => {
  const symbols = ['BTC', 'ETH', 'AAPL', 'GOOGL', 'TSLA', 'MSFT', 'AMZN'];
  const data = [];
  
  for (let i = 0; i < 15; i++) {
    const symbol = symbols[Math.floor(Math.random() * symbols.length)];
    const quantity = Math.random() * 100 + 10;
    const avgPrice = Math.random() * 1000 + 50;
    const currentPrice = avgPrice * (1 + (Math.random() - 0.5) * 0.2);
    const marketValue = quantity * currentPrice;
    const pnl = quantity * (currentPrice - avgPrice);
    const traderId = Math.floor(Math.random() * 3) + 1;
    
    data.push({
      id: i + 1,
      symbol,
      quantity: quantity.toFixed(2),
      avgPrice: avgPrice.toFixed(2),
      currentPrice: currentPrice.toFixed(2),
      marketValue: marketValue.toFixed(2),
      pnl: pnl.toFixed(2),
      pnlPercent: ((currentPrice - avgPrice) / avgPrice * 100).toFixed(2),
      traderId
    });
  }
  
  return data;
};

export const PortfolioTable = ({ traders }: PortfolioTableProps) => {
  const portfolioData = generatePortfolioData();

  const getTraderName = (traderId: number) => {
    return traders.find(t => t.id === traderId)?.name || 'Unknown';
  };

  const getTraderColor = (traderId: number) => {
    const trader = traders.find(t => t.id === traderId);
    return trader?.color === 'trading-blue' ? 'bg-trading-blue' : 
           trader?.color === 'trading-yellow' ? 'bg-trading-yellow' : 'bg-trading-purple';
  };

  return (
    <div className="max-h-96 overflow-auto">
      <Table>
        <TableHeader>
          <TableRow className="border-border">
            <TableHead className="text-muted-foreground">Symbol</TableHead>
            <TableHead className="text-muted-foreground">Trader</TableHead>
            <TableHead className="text-muted-foreground text-right">Quantity</TableHead>
            <TableHead className="text-muted-foreground text-right">Avg Price</TableHead>
            <TableHead className="text-muted-foreground text-right">Current Price</TableHead>
            <TableHead className="text-muted-foreground text-right">Market Value</TableHead>
            <TableHead className="text-muted-foreground text-right">P&L</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {portfolioData.map((row) => (
            <TableRow key={row.id} className="border-border hover:bg-muted/50">
              <TableCell className="font-medium text-foreground">{row.symbol}</TableCell>
              <TableCell>
                <Badge variant="outline" className={`${getTraderColor(row.traderId)} text-white border-none`}>
                  {getTraderName(row.traderId)}
                </Badge>
              </TableCell>
              <TableCell className="text-right text-foreground">{row.quantity}</TableCell>
              <TableCell className="text-right text-foreground">${row.avgPrice}</TableCell>
              <TableCell className="text-right text-foreground">${row.currentPrice}</TableCell>
              <TableCell className="text-right text-foreground">${row.marketValue}</TableCell>
              <TableCell className="text-right">
                <span className={parseFloat(row.pnl) >= 0 ? 'text-trading-green' : 'text-trading-red'}>
                  {parseFloat(row.pnl) >= 0 ? '+' : ''}${row.pnl} ({parseFloat(row.pnlPercent) >= 0 ? '+' : ''}{row.pnlPercent}%)
                </span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};