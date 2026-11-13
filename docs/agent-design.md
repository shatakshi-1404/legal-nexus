# Agent design
One module of nodes (`backend/app/agents/nodes.py`), each wrapped in `@tracked` which writes a redacted AgentRun row
(input/output summary, tools, duration, errors). LangGraph `RetryPolicy(max_attempts=2)` retries failed nodes; each
attempt appears in the monitor. Prompts live in `prompts/templates.py`; structured outputs in `schemas/agents.py`.
