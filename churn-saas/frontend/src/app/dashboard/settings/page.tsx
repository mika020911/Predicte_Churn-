import { IntegrationsPanel } from "@/features/settings/components/integrations-panel";
import { RiskSettingsForm } from "@/features/settings/components/risk-settings-form";

export default function SettingsPage() {
  return (
    <>
      <RiskSettingsForm />
      <IntegrationsPanel />
    </>
  );
}
