import DashboardClient from "../components/dashboard-client";
import { getMarkets } from "@/lib/actions/getMarkets";

export default async function Page() {
  const marketsData = await getMarkets();

  return <DashboardClient initialMarkets={marketsData.data} />;
}
