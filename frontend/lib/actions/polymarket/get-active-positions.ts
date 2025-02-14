"use server";

import { polyClient } from "@/lib/polymarket";

export async function getActivePositions(address: string) {
  const positions = await polyClient.getTrades({
    maker_address: address,
  });
  return positions;
}
