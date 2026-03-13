import { Message } from "@/lib/types";
import { formatDate } from "@/lib/utils";

interface Props {
  messages: Message[];
  showAgentMeta?: boolean;
  assistantLabel?: string;
  viewer?: "workspace" | "admin";
}

function senderType(message: Message): "user" | "ai" | "human" | "system" {
  if (message.role === "system") {
    return "system";
  }
  if (message.role === "user") {
    return "user";
  }

  const metaSender = typeof message.meta_json?.sender_type === "string" ? message.meta_json.sender_type : null;
  if (metaSender === "human") {
    return "human";
  }
  if (metaSender === "system") {
    return "system";
  }
  if ((message.agent_name ?? "").toLowerCase().includes("human")) {
    return "human";
  }
  return "ai";
}

export function MessageList({
  messages,
  showAgentMeta = true,
  assistantLabel = "Assistant",
  viewer = "workspace",
}: Props) {
  return (
    <div className="space-y-3">
      {messages.map((message) => {
        const source = senderType(message);
        const isOutgoing =
          (viewer === "workspace" && source === "user") ||
          (viewer === "admin" && source === "human");
        const sender =
          source === "system"
            ? "System"
            : source === "human"
              ? viewer === "admin"
                ? "You"
                : "Human Support"
              : source === "user"
                ? viewer === "workspace"
                  ? "You"
                  : "Practice Team"
                : assistantLabel;
        const bubbleClass = isOutgoing
          ? "rounded-[28px] rounded-br-[10px] bg-[linear-gradient(180deg,#12304c,#11233b)] px-4 py-3.5 text-sm text-white shadow-[0_22px_50px_rgba(17,34,59,0.16)]"
          : source === "human"
            ? "rounded-[28px] rounded-bl-[10px] border border-emerald-200/90 bg-[linear-gradient(180deg,rgba(236,253,245,0.98),rgba(255,255,255,0.96))] px-4 py-3.5 text-sm text-emerald-950 shadow-[0_18px_45px_rgba(5,150,105,0.08)]"
            : source === "system"
              ? "rounded-[28px] rounded-bl-[10px] border border-amber-200/90 bg-[linear-gradient(180deg,rgba(255,251,235,0.98),rgba(255,255,255,0.96))] px-4 py-3.5 text-sm text-amber-950 shadow-[0_18px_45px_rgba(217,119,6,0.08)]"
              : source === "user"
                ? "rounded-[28px] rounded-bl-[10px] border border-sky-200/90 bg-[linear-gradient(180deg,rgba(239,246,255,0.98),rgba(255,255,255,0.96))] px-4 py-3.5 text-sm text-sky-950 shadow-[0_18px_45px_rgba(14,116,144,0.08)]"
                : "rounded-[28px] rounded-bl-[10px] border border-slate-200/90 bg-white/96 px-4 py-3.5 text-sm text-ink shadow-[0_18px_45px_rgba(15,23,42,0.08)]";
        const metaClass = isOutgoing ? "text-[10px] text-slate-200" : "text-[10px] text-muted";
        return (
          <div key={message.id} className={isOutgoing ? "ml-auto max-w-[86%] animate-fade-rise" : "mr-auto max-w-[86%] animate-fade-rise"}>
            <div className={bubbleClass}>
              <div className="mb-2 flex items-center justify-between gap-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.12em] opacity-80">{sender}</p>
                <p className={metaClass}>{formatDate(message.created_at)}</p>
              </div>
              <p className="whitespace-pre-wrap leading-7">{message.content}</p>
              {showAgentMeta && message.agent_name && source !== "human" && source !== "system" ? (
                <p className={`mt-2 ${metaClass}`}>{message.agent_name}</p>
              ) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}
