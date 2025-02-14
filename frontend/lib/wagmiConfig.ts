// Make sure to import `createConfig` from `@privy-io/wagmi`, not `wagmi`
import { createConfig } from "@privy-io/wagmi";
import { polygon } from "wagmi/chains";
import { cookieStorage, createStorage, http } from "wagmi";

declare module "wagmi" {
  interface Register {
    config: typeof wagmiConfig;
  }
}

export const wagmiConfig = createConfig({
  chains: [polygon],
  ssr: true,
  storage: createStorage({
    storage: cookieStorage,
  }),
  transports: {
    [polygon.id]: http(),
  },
});
