import type { Metadata } from "next";
import { AcceptInvitationForm } from "@/features/team/components/accept-invitation-form";

// Empêche le jeton d'invitation de fuiter via l'en-tête Referer.
export const metadata: Metadata = {
  referrer: "no-referrer",
};

export default function AcceptInvitationPage() {
  return <AcceptInvitationForm />;
}
