/* <ai_context>
   Header component for the application. Displays site title, theme toggle, and login button.
</ai_context> */
"use client";

import React from "react";
import Link from "next/link";
import ThemeToggle from "./theme-toggle";
import LoginButton from "./login-button";

export default function Header() {
  return (
    <header className="flex items-center justify-between p-4 border-b">
      <div>
        <Link href="/">
          <h1 className="text-xl font-bold">Prediction Markets</h1>
        </Link>
      </div>
      <div className="flex items-center space-x-4">
        <ThemeToggle />
        <LoginButton />
      </div>
    </header>
  );
}