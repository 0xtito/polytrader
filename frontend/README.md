# Polytrader Frontend

This directory contains the Next.js application for interacting with the Polytrader AI Backend. It includes:

- React / Next.js 15
- Privy / WAGMI for web3 integration
- TailwindCSS (configured via tailwind.config.ts)
- Shadcn UI library
- TypeScript for type safety

## Installation

Navigate to the frontend directory:

```bash
cd frontend
```

```bash
pnpm install
```

## Configure Environment:

Copy `.env.example` to `.env` if needed, then fill in environment variables. For any variables you want exposed to the client, prefix them with `NEXT_PUBLIC_`.

Example:

```
NEXT_PUBLIC_SOME_API_URL=https://api.example.com
```

## Usage

Development Server
Start the local dev server:

```bash
pnpm dev
```

This will use Next.js’s built-in dev server (with turbopack if your Node version supports it). The app should be available at http://localhost:3000.

Production Build

```bash
pnpm build
pnpm start
```

This first creates an optimized production build, and then starts the server on the default port 3000. You can customize via environment variables or command-line flags.

3. Project Structure

```
frontend/
├── app/
│ ├── page.tsx
│ ├── layout.tsx
│ └── ...
├── components/
│ ├── header.tsx
│ ├── ...
│ └── ui/
├── hooks/
├── lib/
├── public/
├── types/
├── package.json
├── pnpm-lock.yaml
└── README.md (this file)
```

4. Additional Notes

- Shadcn UI: Our UI library is integrated. See components/ui/ for base components.
- TailwindCSS: Configuration is in tailwind.config.ts and postcss.config.mjs.
- Server Actions: We use Next.js server actions in lib/actions/....
