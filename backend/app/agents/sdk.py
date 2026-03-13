from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass

SDK_AVAILABLE = importlib.util.find_spec("agents") is not None


def _sdk_module():
    if not SDK_AVAILABLE:
        return None
    try:
        return importlib.import_module("agents")
    except Exception:  # pragma: no cover
        return None


def _prepare_tool(tool, sdk_module):
    if sdk_module is None or not callable(tool):
        return tool
    try:
        return sdk_module.function_tool(tool)
    except Exception:  # pragma: no cover
        return tool


class Agent:
    def __init__(self, name: str, instructions: str, tools: list | None = None, model: str | None = None):
        self.name = name
        self.instructions = instructions
        self.tools = tools or []
        self.model = model

        sdk_module = _sdk_module()
        self._delegate = None
        if sdk_module is not None:
            try:
                self._delegate = sdk_module.Agent(
                    name=name,
                    instructions=instructions,
                    tools=[_prepare_tool(tool, sdk_module) for tool in self.tools],
                    model=model,
                )
            except Exception:  # pragma: no cover
                self._delegate = None


@dataclass
class _RunResult:
    final_output: str


class Runner:
    @staticmethod
    async def run(agent: Agent, input: str, **kwargs):
        sdk_module = _sdk_module()
        if sdk_module is not None and getattr(agent, "_delegate", None) is not None:
            try:
                return await sdk_module.Runner.run(agent._delegate, input=input, **kwargs)
            except Exception:  # pragma: no cover
                pass
        return _RunResult(final_output=f"[{agent.name}] {input}")


def function_tool(func):
    return func
