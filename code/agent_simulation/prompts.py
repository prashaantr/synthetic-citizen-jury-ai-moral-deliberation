from __future__ import annotations

from typing import Any

from agent_simulation.schema import (
    AgentMessage,
    HarnessConfig,
    Participant,
    RoundSpec,
    Scenario,
)


class PromptRenderError(ValueError):
    """Raised when a prompt template references an unknown variable."""


def render_template(template: str, values: dict[str, Any]) -> str:
    try:
        return template.format_map(values)
    except KeyError as exc:
        missing = exc.args[0]
        available = ", ".join(sorted(values))
        raise PromptRenderError(
            f"Prompt references unknown variable '{missing}'. "
            f"Available variables: {available}"
        ) from exc


def format_decision_options(options: list[str]) -> str:
    if not options:
        return "No fixed options supplied."
    return "\n".join(f"- {option}" for option in options)


def format_participants(participants: list[Participant]) -> str:
    return "\n".join(
        f"- {participant.name} ({participant.id}): {participant.role}"
        for participant in participants
    )


def format_interaction_protocol(harness: HarnessConfig) -> str:
    if not harness.interaction_protocol:
        return ""
    rules = "\n".join(f"- {item}" for item in harness.interaction_protocol)
    return f"Interaction protocol:\n{rules}"


def format_interruption_rules(round_spec: RoundSpec) -> str:
    if not round_spec.interruption_rules:
        return "No special interruption rules for this round."
    return "\n".join(f"- {rule}" for rule in round_spec.interruption_rules)


def render_persona_contract(
    *,
    harness: HarnessConfig,
    participant: Participant,
) -> str:
    if not harness.persona_template:
        return ""
    values = participant_template_values(participant)
    return render_template(harness.persona_template, values)


def participant_template_values(participant: Participant) -> dict[str, Any]:
    values: dict[str, Any] = {
        "agent_id": participant.id,
        "agent_name": participant.name,
        "agent_role": participant.role,
        "agent_prompt": participant.prompt,
        "agent_attributes": format_attributes(participant.attributes),
    }
    values.update({f"agent_{key}": value for key, value in participant.attributes.items()})
    return values


def format_attributes(attributes: dict[str, Any]) -> str:
    if not attributes:
        return "No additional attributes supplied."
    return "\n".join(f"- {key}: {value}" for key, value in sorted(attributes.items()))


def format_transcript(
    messages: list[AgentMessage],
    *,
    visibility: str = "named",
) -> str:
    if visibility == "hidden":
        return "Prior transcript hidden for this round."

    if not messages:
        return "No prior transcript."

    blocks = []
    anonymous_labels: dict[str, str] = {}
    for message in messages:
        if visibility == "anonymous":
            label = anonymous_labels.setdefault(
                message.participant_id,
                f"Participant {len(anonymous_labels) + 1}",
            )
            speaker = f"{label}:"
        else:
            speaker = f"{message.participant_name} ({message.participant_id}):"
        blocks.append(f"[{message.round_id}] {speaker}\n{message.content}")
    return "\n\n".join(blocks)


def build_context(
    *,
    scenario: Scenario,
    participants: list[Participant],
    transcript: list[AgentMessage],
    round_spec: RoundSpec,
    participant: Participant | None = None,
    extra_values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    values: dict[str, Any] = {
        "scenario_title": scenario.title,
        "scenario_question": scenario.question,
        "scenario_background": scenario.background,
        "decision_options": format_decision_options(scenario.decision_options),
        "participants": format_participants(participants),
        "transcript": format_transcript(
            transcript,
            visibility=round_spec.transcript_visibility,
        ),
        "round_id": round_spec.id,
        "round_title": round_spec.title,
        "round_timebox_minutes": round_spec.timebox_minutes or "unspecified",
        "round_max_turns": round_spec.max_turns or "unspecified",
        "turn_strategy": round_spec.turn_strategy,
        "interruption_rules": format_interruption_rules(round_spec),
        "transcript_visibility": round_spec.transcript_visibility,
    }
    values.update(scenario.variables)

    if participant is not None:
        values.update(participant_template_values(participant))

    if extra_values:
        values.update(extra_values)

    return values
