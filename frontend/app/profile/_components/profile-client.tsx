"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { withdrawFundsAction } from "@/lib/actions/agent/agent-actions";
import { useAccount, useBalance, useWriteContract } from "wagmi";
import { erc20Abi, formatUnits, parseUnits } from "viem";
import { useState, useEffect } from "react";
import { Skeleton } from "@/components/ui/skeleton";

const USDCE_ADDRESS = process.env.NEXT_PUBLIC_USDCE_ADDRESS as `0x${string}`;
const AGENT_ADDRESS = process.env
  .NEXT_PUBLIC_POLYMARKET_PROXY_ADDRESS as `0x${string}`;

export default function ProfileClient() {
  const [amount, setAmount] = useState("");
  const { toast } = useToast();
  const { address } = useAccount();
  const { writeContract, status, error, data } = useWriteContract();

  useEffect(() => {
    if (status === "success") {
      const sentAmount = amount;
      toast({
        title: `Successfully sent ${sentAmount} ${
          usdceBalance?.symbol || "USDC.e"
        } to agent`,
        description: `Transaction hash: https://polygonscan.io/tx/${data}`,
      });
      setAmount("");
    } else if (status === "error") {
      let toastTitle = "Failed to send USDC.e to agent";

      switch (error?.name) {
        case "ContractFunctionExecutionError":
          toastTitle = "Failed to send USDC.e to agent";
          break;
        default:
          toastTitle = "Failed to send USDC.e to agent";
          break;
      }

      toast({
        title: toastTitle,
        description: error?.message.split(".")[0],
        variant: "destructive",
      });
      console.log("Error", error);
    } else if (status === "pending") {
      toast({
        title: "Pending",
        description: "Sending USDC.e to agent",
      });
    }
  }, [status]);

  // Get USDC.e balance
  const { data: usdceBalance, isLoading: usdceBalanceLoading } = useBalance({
    address,
    token: USDCE_ADDRESS,
  });

  // Get agent's USDC.e balance
  const { data: agentBalance, isLoading: agentBalanceLoading } = useBalance({
    address: AGENT_ADDRESS,
    token: USDCE_ADDRESS,
  });

  // sending USDC.e to agent
  const handleDeposit = () => {
    if (!amount || !address) return;

    try {
      toast({
        title: "Sending USDC.e to agent",
        description: "Accept transaction...",
      });
      writeContract({
        abi: erc20Abi,
        functionName: "transfer",
        args: [AGENT_ADDRESS, parseUnits(amount || "0", 6)],
        address: USDCE_ADDRESS,
      });
    } catch (error) {
      toast({
        title: "Transfer failed",
        description: "Failed to send USDC.e to agent",
        variant: "destructive",
      });
    }
  };

  const handleWithdraw = async () => {
    if (!amount) return;

    try {
      const result = await withdrawFundsAction(amount);

      if (result.isSuccess) {
        toast({
          title: "Success",
          description: "Funds withdrawn successfully",
        });
        setAmount("");
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to withdraw funds",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="container max-w-4xl mx-auto py-8 space-y-8">
      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-4">Balances</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Your USDC.e Balance</p>
            {usdceBalanceLoading || !usdceBalance ? (
              <Skeleton className="w-20 h-4" />
            ) : (
              <span className="text-lg font-medium">
                {formatUnits(usdceBalance.value, usdceBalance.decimals) || "0"}{" "}
                {usdceBalance.symbol || "USDC.e"}
              </span>
            )}
          </div>

          <div>
            <p className="text-sm text-muted-foreground">
              Agent's USDC.e Balance
            </p>
            {agentBalanceLoading || !agentBalance ? (
              <Skeleton className="w-20 h-4" />
            ) : (
              <span className="text-lg font-medium">
                {formatUnits(agentBalance.value, agentBalance.decimals) || "0"}{" "}
                {agentBalance.symbol || "USDC.e"}
              </span>
            )}
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-4">Manage Funds</h2>
        <div className="space-y-4">
          <div>
            <label htmlFor="amount" className="block text-sm font-medium mb-2">
              Amount
            </label>
            <div className="flex space-x-4">
              <Input
                id="amount"
                type="number"
                placeholder="Enter amount"
                value={amount}
                onChange={(e) => {
                  const inputValue = e.target.value;
                  // make sure it is a number or its a backspace
                  const numericValue = parseFloat(inputValue);
                  if (!isNaN(numericValue) || inputValue === "") {
                    setAmount(numericValue.toString());
                  }
                }}
              />
              <Button onClick={handleDeposit}>Deposit</Button>
              <Button onClick={handleWithdraw} variant="outline">
                Withdraw
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
