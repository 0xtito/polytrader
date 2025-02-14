export interface AgentPosition {
  marketId: string;
  marketQuestion: string;
  outcome: string;
  amount: number;
  entryPrice: number;
  timestamp: number;
}

export interface AgentBalance {
  usdcBalance: string;
  usdceBalance: string;
}

export interface SwapResult {
  success: boolean;
  hash?: string;
  error?: string;
}

export interface WithdrawResult {
  success: boolean;
  amount: string;
  hash?: string;
  error?: string;
}

export interface DepositResult {
  success: boolean;
  amount: string;
  hash?: string;
  error?: string;
}
