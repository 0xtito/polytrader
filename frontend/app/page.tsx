import { getMarkets } from "@/lib/actions/getMarkets";
import DashboardClient from "../components/dashboard-client";
// import { getMarkets } from "@/lib/actions/getMarkets";
import { getGammaMarkets } from "@/lib/actions/get-gamma-markets";

export default async function Page() {
  const marketsData = await getGammaMarkets();

  return <DashboardClient initialMarkets={marketsData.markets} />;
}
