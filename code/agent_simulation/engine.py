from __future__ import annotations

from typing import Any

from agent_simulation.clients import ModelClient
from agent_simulation.prompts import (
    build_context,
    format_interaction_protocol,
    render_persona_contract,
    render_template,
)
from agent_simulation.schema import (
    AgentMessage,
    Participant,
    RoundResult,
    RoundSpec,
    SimulationConfig,
    SimulationResult,
)


def run_simulation(
    *,
    config: SimulationConfig,
    client: ModelClient,
    model: str,
    temperature: float = 0.2,
    max_participants: int | None = None,
    run_metadata: dict[str, Any] | None = None,
) -> SimulationResult:
    participant_by_id = {participant.id: participant for participant in config.participants}
    transcript: list[AgentMessage] = []
    round_results: list[RoundResult] = []

    for round_spec in config.rounds:
        round_transcript = list(transcript)
        if round_spec.mode == "synthesis":
            messages = [
                _run_synthesis_round(
                    config=config,
                    round_spec=round_spec,
                    transcript=round_transcript,
                    client=client,
                    model=model,
                    temperature=temperature,
                )
            ]
        elif round_spec.mode == "group_chat":
            selected = _select_participants(round_spec, config.participants, participant_by_id)
            if max_participants is not None:
                selected = selected[:max_participants]
            messages = _run_group_chat_round(
                config=config,
                round_spec=round_spec,
                participants=selected,
                transcript=round_transcript,
                client=client,
                model=model,
                temperature=temperature,
            )
        else:
            selected = _select_participants(round_spec, config.participants, participant_by_id)
            if max_participants is not None:
                selected = selected[:max_participants]
            messages = [
                _run_participant_round(
                    config=config,
                    round_spec=round_spec,
                    participant=participant,
                    transcript=round_transcript,
                    client=client,
                    model=model,
                    temperature=temperature,
                )
                for participant in selected
            ]

        transcript.extend(messages)
        round_results.append(
            RoundResult(
                id=round_spec.id,
                title=round_spec.title,
                mode=round_spec.mode,
                transcript_visibility=round_spec.transcript_visibility,
                timebox_minutes=round_spec.timebox_minutes,
                max_turns=round_spec.max_turns,
                turn_strategy=round_spec.turn_strategy,
                messages=messages,
            )
        )

    return SimulationResult.create(
        config=config,
        model=model,
        provider=client.provider,
        rounds=round_results,
        metadata={
            "max_participants": max_participants,
            **(run_metadata or {}),
        },
    )


def _select_participants(
    round_spec: RoundSpec,
    participants: list[Participant],
    participant_by_id: dict[str, Participant],
) -> list[Participant]:
    if round_spec.participants == "all":
        return participants
    return [participant_by_id[participant_id] for participant_id in round_spec.participants]


def _run_participant_round(
    *,
    config: SimulationConfig,
    round_spec: RoundSpec,
    participant: Participant,
    transcript: list[AgentMessage],
    client: ModelClient,
    model: str,
    temperature: float,
    extra_context: dict[str, Any] | None = None,
    message_metadata: dict[str, Any] | None = None,
) -> AgentMessage:
    context = build_context(
        scenario=config.scenario,
        participants=config.participants,
        transcript=transcript,
        round_spec=round_spec,
        participant=participant,
        extra_values=extra_context,
    )
    system_prompt = render_template(
        "\n\n".join(
            part
            for part in [
                config.global_instructions,
                config.harness.shared_instructions,
                render_persona_contract(
                    harness=config.harness,
                    participant=participant,
                ),
                format_interaction_protocol(config.harness),
                participant.prompt,
                round_spec.system_prompt,
            ]
            if part.strip()
        ),
        context,
    )
    user_prompt = render_template(round_spec.prompt, context)
    content = client.complete(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        temperature=temperature,
        metadata={
            "agent_id": participant.id,
            "agent_name": participant.name,
            "round_id": round_spec.id,
            "round_title": round_spec.title,
            **(message_metadata or {}),
        },
    )
    return AgentMessage(
        participant_id=participant.id,
        participant_name=participant.name,
        participant_role=participant.role,
        round_id=round_spec.id,
        content=content,
        metadata={
            "round_title": round_spec.title,
            "mode": round_spec.mode,
            **(message_metadata or {}),
        },
    )


def _run_group_chat_round(
    *,
    config: SimulationConfig,
    round_spec: RoundSpec,
    participants: list[Participant],
    transcript: list[AgentMessage],
    client: ModelClient,
    model: str,
    temperature: float,
) -> list[AgentMessage]:
    if not participants:
        return []

    max_turns = round_spec.max_turns or len(participants)
    messages: list[AgentMessage] = []
    for turn_index in range(max_turns):
        speaker = _select_group_chat_speaker(
            participants=participants,
            turn_index=turn_index,
            strategy=round_spec.turn_strategy,
        )
        event_type = (
            "interruption"
            if round_spec.turn_strategy == "interruptions" and turn_index > 0
            else "contribution"
        )
        message = _run_participant_round(
            config=config,
            round_spec=round_spec,
            participant=speaker,
            transcript=[*transcript, *messages],
            client=client,
            model=model,
            temperature=temperature,
            extra_context={
                "turn_number": turn_index + 1,
                "turns_remaining": max_turns - turn_index - 1,
                "current_speaker": speaker.name,
                "event_type": event_type,
            },
            message_metadata={
                "turn_number": turn_index + 1,
                "turns_remaining": max_turns - turn_index - 1,
                "event_type": event_type,
            },
        )
        messages.append(message)
    return messages


def _select_group_chat_speaker(
    *,
    participants: list[Participant],
    turn_index: int,
    strategy: str,
) -> Participant:
    if strategy == "interruptions":
        # Offset the speaker order so interruption rounds are not a simple replay
        # of the previous round-robin pattern.
        return participants[(turn_index * 2 + 1) % len(participants)]
    return participants[turn_index % len(participants)]


def _run_synthesis_round(
    *,
    config: SimulationConfig,
    round_spec: RoundSpec,
    transcript: list[AgentMessage],
    client: ModelClient,
    model: str,
    temperature: float,
) -> AgentMessage:
    context = build_context(
        scenario=config.scenario,
        participants=config.participants,
        transcript=transcript,
        round_spec=round_spec,
        extra_values={
            "turn_number": "synthesis",
            "turns_remaining": 0,
            "current_speaker": round_spec.speaker_name,
            "event_type": "synthesis",
        },
    )
    system_prompt = render_template(
        "\n\n".join(
            part
            for part in [
                config.global_instructions,
                config.harness.shared_instructions,
                format_interaction_protocol(config.harness),
                config.harness.output_contract,
                round_spec.system_prompt,
            ]
            if part.strip()
        ),
        context,
    )
    user_prompt = render_template(round_spec.prompt, context)
    content = client.complete(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        temperature=temperature,
        metadata={
            "agent_id": round_spec.speaker_id,
            "agent_name": round_spec.speaker_name,
            "round_id": round_spec.id,
            "round_title": round_spec.title,
        },
    )
    return AgentMessage(
        participant_id=round_spec.speaker_id,
        participant_name=round_spec.speaker_name,
        participant_role=round_spec.speaker_role,
        round_id=round_spec.id,
        content=content,
        metadata={
            "round_title": round_spec.title,
            "mode": round_spec.mode,
        },
    )
