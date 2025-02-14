"use client";

import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface TradeExecutionCardProps {
  orderData: {
    orderID: string;
    takingAmount: string;
    makingAmount: string;
    status: string;
    transactionsHashes: string[];
    success: boolean;
    errorMsg?: string;
  };
}

export default function TradeExecutionCard({
  orderData,
}: TradeExecutionCardProps) {
  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Trade Execution</CardTitle>
          <Badge
            variant={orderData.success ? "default" : "destructive"}
            className="capitalize"
          >
            {orderData.status}
          </Badge>
        </div>
        <CardDescription>
          Order details and transaction information
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm font-medium text-muted-foreground">
              Taking Amount
            </p>
            <p className="text-sm">{orderData.takingAmount}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground">
              Making Amount
            </p>
            <p className="text-sm">{orderData.makingAmount}</p>
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-muted-foreground mb-1">
            Order ID
          </p>
          <p className="text-xs break-all font-mono bg-muted p-2 rounded">
            {orderData.orderID}
          </p>
        </div>

        {orderData.transactionsHashes.length > 0 && (
          <div>
            <p className="text-sm font-medium text-muted-foreground mb-1">
              Transaction Hashes
            </p>
            <ScrollArea className="h-[100px] w-full rounded-md border">
              {orderData.transactionsHashes.map((hash, index) => (
                <a
                  key={index}
                  href={`https://polygonscan.com/tx/${hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs break-all font-mono p-2 hover:bg-muted"
                >
                  {hash}
                </a>
              ))}
            </ScrollArea>
          </div>
        )}

        {orderData.errorMsg && (
          <div className="mt-4">
            <p className="text-sm font-medium text-destructive">Error</p>
            <p className="text-sm text-destructive">{orderData.errorMsg}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
