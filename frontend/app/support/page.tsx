import { redirect } from "next/navigation";

export default function LegacySupportRoute() {
  redirect("/admin/support");
}

