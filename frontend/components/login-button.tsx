/* <ai_context>
   LoginButton component triggers user login via Privy.
</ai_context> */
"use client";

import React from "react";

export default function LoginButton() {
  const handleLogin = () => {
    // Simulate Privy login flow
    alert("Login functionality not implemented. (Simulated login)");
  };

  return (
    <button
      className="px-3 py-1 bg-primary text-primary-foreground rounded"
      onClick={handleLogin}
    >
      Connect Wallet
    </button>
  );
}