from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ToolTrace:
    tool_name: str
    input: dict
    output: dict


@dataclass
class RunTrace:
    agent_name: str
    workflow: str
    traces: list[ToolTrace] = field(default_factory=list)

    def add(self, tool_name: str, input_payload: dict, output_payload: dict) -> None:
        self.traces.append(
            ToolTrace(tool_name=tool_name, input=input_payload, output=output_payload)
        )

    def as_json(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "workflow": self.workflow,
            "tools": [
                {"tool_name": t.tool_name, "input": t.input, "output": t.output}
                for t in self.traces
            ],
        }
