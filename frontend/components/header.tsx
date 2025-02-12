/* <ai_context>
   Header component for the application. Displays site logo, title, and Privy login button.
</ai_context> */
"use client";

import React from "react";
import Link from "next/link";
import { usePrivy } from "@privy-io/react-auth";
import { LogIn, LogOut } from "lucide-react";

export default function Header() {
  const { login, authenticated, logout } = usePrivy();

  return (
    <header className="flex items-center justify-between p-4 border-b">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
          <span className="text-primary-foreground font-bold">P</span>
        </div>
        <Link href="/" className="text-xl font-bold">
          Polytrader
        </Link>
      </div>

      <button
        onClick={authenticated ? logout : login}
        className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:opacity-90 transition-opacity"
      >
        {authenticated ? (
          <>
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </>
        ) : (
          <>
            <LogIn className="w-4 h-4" />
            <span>Sign In</span>
          </>
        )}
      </button>
    </header>
  );
}
