"use server";

import { getAgentBalanceAction } from "@/lib/actions/agent/agent-actions";
import ProfileClient from "./_components/profile-client";

export default async function ProfilePage() {
  return (
    <div>
      <ProfileClient />
    </div>
  );
}
