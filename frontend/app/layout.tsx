import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import { Toaster } from "@/components/ui/toaster";
import PrivyProvider from "@/components/providers/PrivyProvider";
import Header from "@/components/header";
import WagmiProviderWrapper from "@/components/providers/QueryClientWrapper";

import { headers } from "next/headers";
import { cookieToInitialState } from "wagmi";

import { wagmiConfig } from "@/lib/wagmiConfig";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Polymarket AI Dashboard",
  description: "Monitor and control the Polymarket AI Agent",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const initialState = cookieToInitialState(
    wagmiConfig,
    (await headers()).get("cookie")
  );

  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <PrivyProvider>
          <WagmiProviderWrapper initialState={initialState}>
            <Header />
            <main>{children}</main>
          </WagmiProviderWrapper>
        </PrivyProvider>
        <Toaster />
      </body>
    </html>
  );
}
