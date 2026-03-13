"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { OpenAIHealth } from "@/lib/types";

export function AiModeBadge() {
  const [health, setHealth] = useState<OpenAIHealth | null>(null);

  useEffect(() => {
    let active = true;
    api
      .getOpenAIHealth()
      .then((result) => {
        if (active) setHealth(result);
      })
      .catch(() => {
        if (active) setHealth(null);
      });
    return () => {
      active = false;
    };
  }, []);

  const live = health?.runtime_mode === "live_ai";
  return (
    <Badge variant={live ? "success" : "danger"} className="text-[11px]">
      {live ? "Live" : "Offline"}
    </Badge>
  );
}
