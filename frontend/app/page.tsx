import DashboardClient from "../components/dashboard-client";
import { getGammaMarkets } from "@/lib/actions/get-gamma-markets";

export default async function Page() {
  const marketsData = await getGammaMarkets(50, undefined, {
    featured: true,
    closed: false,
    order: "volumeNum",
    ascending: false,
    liquidityNumMin: 100000,
  });

  return <DashboardClient initialMarkets={marketsData.markets} />;
}
