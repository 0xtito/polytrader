/* <ai_context>
   Header component for the application. Displays site logo, title, and Privy login button.
</ai_context> */
"use client";

import React from "react";
import Link from "next/link";
import { usePrivy } from "@privy-io/react-auth";
import { LogIn, LogOut, User, Wallet } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { useAccount } from "wagmi";
import { Skeleton } from "./ui/skeleton";

import Image from "next/image";

export default function Header() {
  const { login, authenticated, logout } = usePrivy();
  const { address, isConnecting } = useAccount();
  const router = useRouter();

  return (
    <header className="flex items-center justify-between p-4 border-b">
      <div className="flex items-center space-x-3">
        <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center">
          <Link href="/" className="text-xl font-bold">
            <Image
              src="/logo-cropped.png"
              alt="Polytrader"
              width={48}
              height={48}
            />
          </Link>
        </div>
      </div>

      {isConnecting ? (
        <Skeleton className="w-10 h-10 rounded-full" />
      ) : authenticated ? (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="flex items-center space-x-2">
              <Wallet className="w-4 h-4" />
              <span>{address?.slice(0, 6)}...</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem onClick={() => router.push("/profile")}>
              Profile
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout} className="text-destructive">
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ) : (
        <Button onClick={login} className="flex items-center space-x-2">
          <LogIn className="w-4 h-4" />
          <span>Sign In</span>
        </Button>
      )}
    </header>
  );
}
