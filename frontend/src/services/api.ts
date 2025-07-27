/**
 * API client for Trading System backend
 */

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://tradingsystem-lccs.onrender.com' 
  : 'http://localhost:8000';

export interface Trader {
  id: number;
  name: string;
  display_name: string;
  color: string;
}

export interface TraderPortfolio {
  trader_name: string;
  portfolio_value: number;
  cash_balance: number;
  holdings: Array<{
    symbol: string;
    quantity: number;
    current_price: number;
    market_value: number;
  }>;
  total_trades: number;
}

export interface TraderPerformance {
  trader_name: string;
  current_value: number;
  starting_value: number;
  total_pnl: number;
  total_return: number;
  performance_history: Array<{
    timestamp: string;
    portfolio_value: number;
    date: string;
  }>;
}

export interface Trade {
  timestamp: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  total: number;
  reasoning: string;
  status: string;
}

export interface TraderTrades {
  trader_name: string;
  trades: Trade[];
  total_count: number;
}

export interface MarketData {
  symbol: string;
  timeframe: string;
  data: Array<{
    timestamp: string;
    date: string;
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
  count: number;
  is_mock?: boolean;
}

export interface TradingSummary {
  total_portfolio_value: number;
  total_traders: number;
  trader_summaries: Array<{
    name: string;
    portfolio_value: number;
    holdings_count: number;
    trades_count: number;
  }>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }

  // Trader endpoints
  async getTraders(): Promise<{ traders: Trader[] }> {
    return this.request('/api/traders');
  }

  async getTraderPortfolio(traderName: string): Promise<TraderPortfolio> {
    return this.request(`/api/traders/${traderName}/portfolio`);
  }

  async getTraderPerformance(traderName: string): Promise<TraderPerformance> {
    return this.request(`/api/traders/${traderName}/performance`);
  }

  async getTraderTrades(traderName: string, limit: number = 50): Promise<TraderTrades> {
    return this.request(`/api/traders/${traderName}/trades?limit=${limit}`);
  }

  // Market data endpoints
  async getMarketData(symbol: string, timeframe: string = 'day', limit: number = 30): Promise<MarketData> {
    return this.request(`/api/market/${symbol}?timeframe=${timeframe}&limit=${limit}`);
  }

  // Summary endpoint
  async getTradingSummary(): Promise<TradingSummary> {
    return this.request('/api/summary');
  }

  // Health check
  async healthCheck(): Promise<{ message: string; timestamp: string }> {
    return this.request('/');
  }
}

export const apiClient = new ApiClient();
export default apiClient;