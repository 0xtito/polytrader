/* <ai_context>
   Main page of the Next.js 13 app. This shows a basic dashboard
   displaying markets, positions, and a simple user override button.
</ai_context> */

"use client";

import React, { useState, useEffect } from "react";

export default function Home() {
  const [markets, setMarkets] = useState<any[]>([]);
  const [log, setLog] = useState<string[]>([]);

  // useEffect(() => {
  //   // Example: fetch or subscribe to updates from the backend
  //   fetch("http://localhost:3001/markets") // you'd implement an endpoint or use a WebSocket
  //     .then((res) => res.json())
  //     .then((data) => {
  //       setMarkets(data);
  //     })
  //     .catch((err) => console.error(err));

  //   // For demonstration, just add a mock event to the log
  //   setLog((prev) => [...prev, "Loaded initial market data..."]);
  // }, []);

  const handleOverride = (marketId: string) => {
    // Placeholder: call override endpoint, then log
    setLog((prev) => [
      ...prev,
      `User override triggered for market: ${marketId}`,
    ]);
  };

  return (
    <main style={{ padding: 20 }}>
      <h1>Polymarket AI Dashboard</h1>
      <section style={{ marginBottom: 30 }}>
        <h2>Markets</h2>
        {markets.length === 0 && <p>No markets loaded.</p>}
        {markets.map((m) => (
          <div
            key={m.id}
            style={{ border: "1px solid #ccc", marginBottom: 10, padding: 10 }}
          >
            <p>Market ID: {m.id}</p>
            <p>Market Name: {m.name}</p>
            <p>Current Price: {m.price}</p>
            <button onClick={() => handleOverride(m.id)}>
              Override / Exit Position
            </button>
          </div>
        ))}
      </section>

      <section>
        <h2>Event Log</h2>
        <div
          style={{
            maxHeight: 200,
            overflowY: "auto",
            border: "1px solid #333",
            padding: 10,
          }}
        >
          {log.map((entry, idx) => (
            <div key={idx}>{entry}</div>
          ))}
        </div>
      </section>
    </main>
  );
}
