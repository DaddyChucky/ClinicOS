import { Card } from "@/components/ui/card";

const personas = [
  {
    name: "Office Manager",
    pains: "staff overload, schedule churn, claims follow-up backlog"
  },
  {
    name: "Front Desk Lead",
    pains: "manual reminders, intake backlog, no-show spikes"
  },
  {
    name: "Practice Owner / Admin",
    pains: "cross-location visibility, margin pressure, growth predictability"
  }
];

export function PersonaPanel() {
  return (
    <Card className="space-y-2">
      <h3 className="text-lg font-semibold text-ink">Persona Snapshot</h3>
      {personas.map((persona) => (
        <div key={persona.name} className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm">
          <p className="font-semibold text-ink">{persona.name}</p>
          <p className="text-slate">Pain points: {persona.pains}</p>
        </div>
      ))}
    </Card>
  );
}
