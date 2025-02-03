/* <ai_context>
   This file sets up the general layout for the Next.js 13 app directory.
   It's a simple example that can wrap all pages in a common layout.
</ai_context> */

import React from "react";

export const metadata = {
  title: "Polymarket AI Dashboard",
  description: "Monitor and control the Polymarket AI Agent",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0 }}>{children}</body>
    </html>
  );
}
