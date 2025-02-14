"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { WagmiProvider } from "@privy-io/wagmi";

import { wagmiConfig } from "@/lib/wagmiConfig";
import { State } from "wagmi";

export default function WagmiProviderWrapper({
  children,
  initialState,
}: {
  children: React.ReactNode;
  initialState: State | undefined;
}) {
  const queryClient = new QueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <WagmiProvider config={wagmiConfig} initialState={initialState}>
        {children}
      </WagmiProvider>
    </QueryClientProvider>
  );
}
