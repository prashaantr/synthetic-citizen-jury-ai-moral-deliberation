from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from agent_simulation.schema import ConfigError, SimulationConfig


def apply_runtime_inputs(
    config: SimulationConfig,
    *,
    prompt: str | None = None,
    prompt_file: str | Path | None = None,
    variables: dict[str, str] | None = None,
) -> SimulationConfig:
    challenge_prompt = _resolve_prompt(prompt=prompt, prompt_file=prompt_file)
    scenario_variables = dict(config.scenario.variables)

    if challenge_prompt:
        scenario_variables["challenge_prompt"] = challenge_prompt
        scenario_variables["challenge_brief"] = challenge_prompt

    if variables:
        scenario_variables.update(variables)

    scenario = replace(config.scenario, variables=scenario_variables)
    return replace(config, scenario=scenario)


def parse_variable_assignments(assignments: list[str] | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for assignment in assignments or []:
        if "=" not in assignment:
            raise ConfigError(
                f"Invalid --var '{assignment}'. Expected KEY=VALUE."
            )
        key, value = assignment.split("=", 1)
        key = key.strip()
        if not key:
            raise ConfigError(f"Invalid --var '{assignment}'. KEY cannot be empty.")
        parsed[key] = value
    return parsed


def _resolve_prompt(
    *,
    prompt: str | None,
    prompt_file: str | Path | None,
) -> str | None:
    if prompt and prompt_file:
        raise ConfigError("Use either --prompt or --prompt-file, not both.")
    if prompt_file:
        path = Path(prompt_file)
        try:
            prompt = path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ConfigError(f"Prompt file not found: {path}") from exc
    if prompt is None:
        return None
    prompt = prompt.strip()
    if not prompt:
        raise ConfigError("Prompt cannot be empty.")
    return prompt
