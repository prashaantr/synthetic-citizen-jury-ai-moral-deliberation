# Code

This directory contains the reusable multi-agent simulation engine.

## Entry Points

- `agent_simulation/cli.py`: command-line runner
- `agent_simulation/engine.py`: executes configured simulation rounds
- `agent_simulation/schema.py`: dataclass schema for configs and results
- `agent_simulation/clients.py`: model provider adapters
- `run_simulation.py`: script wrapper around the CLI

## Run

From the repository root:

```bash
PYTHONPATH=code python3 -m agent_simulation --list-presets
PYTHONPATH=code python3 -m agent_simulation configs/hackathon_one_hour.json \
  --prompt "Design an AI workflow for triaging city pothole reports."
```

Dry runs do not call an external model provider. Use `--provider openai --model <model-name>` for OpenAI-backed runs after installing the optional dependency.
