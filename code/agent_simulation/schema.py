from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, cast


RoundMode = Literal["individual", "group_chat", "synthesis"]
TranscriptVisibility = Literal["named", "anonymous", "hidden"]
TurnStrategy = Literal["round_robin", "interruptions"]


class ConfigError(ValueError):
    """Raised when a simulation config is structurally invalid."""


@dataclass(frozen=True)
class HarnessConfig:
    shared_instructions: str = ""
    persona_template: str = ""
    interaction_protocol: list[str] = field(default_factory=list)
    output_contract: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "HarnessConfig":
        if data is None:
            return cls()
        _ensure_object(data, "harness")
        return cls(
            shared_instructions=_optional_text(
                data, "shared_instructions", "", "harness"
            ),
            persona_template=_optional_text(data, "persona_template", "", "harness"),
            interaction_protocol=_optional_text_list(
                data, "interaction_protocol", "harness"
            ),
            output_contract=_optional_text(data, "output_contract", "", "harness"),
        )


@dataclass(frozen=True)
class Scenario:
    title: str
    question: str
    background: str = ""
    decision_options: list[str] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scenario":
        path = "scenario"
        _ensure_object(data, path)
        return cls(
            title=_required_text(data, "title", path),
            question=_required_text(data, "question", path),
            background=_optional_text(data, "background", "", path),
            decision_options=_optional_text_list(data, "decision_options", path),
            variables=_optional_mapping(data, "variables", path),
        )


@dataclass(frozen=True)
class Participant:
    id: str
    name: str
    role: str
    prompt: str
    attributes: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Participant":
        path = "participants[]"
        _ensure_object(data, path)
        participant_id = _required_identifier(data, "id", path)
        return cls(
            id=participant_id,
            name=_optional_text(data, "name", participant_id, path),
            role=_optional_text(data, "role", "", path),
            prompt=_required_text(data, "prompt", path),
            attributes=_optional_mapping(data, "attributes", path),
        )


@dataclass(frozen=True)
class RoundSpec:
    id: str
    title: str
    prompt: str
    mode: RoundMode = "individual"
    participants: str | list[str] = "all"
    system_prompt: str = ""
    speaker_id: str = "synthesizer"
    speaker_name: str = "Synthesizer"
    speaker_role: str = "Synthesis"
    transcript_visibility: TranscriptVisibility = "named"
    timebox_minutes: int | None = None
    max_turns: int | None = None
    turn_strategy: TurnStrategy = "round_robin"
    interruption_rules: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RoundSpec":
        _ensure_object(data, "rounds[]")
        path = f"rounds[{data.get('id', '?')}]"
        mode = str(data.get("mode", "individual"))
        if mode not in {"individual", "group_chat", "synthesis"}:
            raise ConfigError(
                f"{path}.mode must be one of: individual, group_chat, synthesis"
            )

        transcript_visibility = str(data.get("transcript_visibility", "named"))
        if transcript_visibility not in {"named", "anonymous", "hidden"}:
            raise ConfigError(
                f"{path}.transcript_visibility must be one of: named, anonymous, hidden"
            )

        turn_strategy = str(data.get("turn_strategy", "round_robin"))
        if turn_strategy not in {"round_robin", "interruptions"}:
            raise ConfigError(
                f"{path}.turn_strategy must be one of: round_robin, interruptions"
            )

        participants = _round_participants(data.get("participants", "all"), path)

        return cls(
            id=_required_identifier(data, "id", "rounds[]"),
            title=_optional_text(data, "title", str(data.get("id", "")), path),
            prompt=_required_text(data, "prompt", path),
            mode=cast(RoundMode, mode),
            participants=participants,
            system_prompt=_optional_text(data, "system_prompt", "", path),
            speaker_id=_optional_identifier(data, "speaker_id", "synthesizer", path),
            speaker_name=_optional_text(data, "speaker_name", "Synthesizer", path),
            speaker_role=_optional_text(data, "speaker_role", "Synthesis", path),
            transcript_visibility=cast(TranscriptVisibility, transcript_visibility),
            timebox_minutes=_optional_positive_int(data, "timebox_minutes", path),
            max_turns=_optional_positive_int(data, "max_turns", path),
            turn_strategy=cast(TurnStrategy, turn_strategy),
            interruption_rules=_optional_text_list(data, "interruption_rules", path),
        )


@dataclass(frozen=True)
class SimulationConfig:
    name: str
    description: str
    scenario: Scenario
    participants: list[Participant]
    rounds: list[RoundSpec]
    harness: HarnessConfig = field(default_factory=HarnessConfig)
    global_instructions: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimulationConfig":
        if not isinstance(data, dict):
            raise ConfigError("Simulation config must be a JSON object.")

        participant_items = data.get("participants", [])
        if not isinstance(participant_items, list):
            raise ConfigError("participants must be a list.")
        participants = [Participant.from_dict(item) for item in participant_items]
        if not participants:
            raise ConfigError("Simulation config requires at least one participant.")
        _require_unique_ids("participants", [participant.id for participant in participants])

        round_items = data.get("rounds", [])
        if not isinstance(round_items, list):
            raise ConfigError("rounds must be a list.")
        rounds = [RoundSpec.from_dict(item) for item in round_items]
        if not rounds:
            raise ConfigError("Simulation config requires at least one round.")
        _require_unique_ids("rounds", [round_spec.id for round_spec in rounds])

        participant_ids = {participant.id for participant in participants}
        for round_spec in rounds:
            if isinstance(round_spec.participants, list):
                unknown = sorted(set(round_spec.participants) - participant_ids)
                if unknown:
                    raise ConfigError(
                        f"Round '{round_spec.id}' references unknown participant(s): {unknown}"
                    )

        return cls(
            name=_required_identifier(data, "name", "config"),
            description=_optional_text(data, "description", "", "config"),
            scenario=Scenario.from_dict(_required_mapping(data, "scenario", "config")),
            participants=participants,
            rounds=rounds,
            harness=HarnessConfig.from_dict(data.get("harness")),
            global_instructions=_optional_text(data, "global_instructions", "", "config"),
            metadata=_optional_mapping(data, "metadata", "config"),
        )


@dataclass(frozen=True)
class AgentMessage:
    participant_id: str
    participant_name: str
    participant_role: str
    round_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoundResult:
    id: str
    title: str
    mode: RoundMode
    transcript_visibility: TranscriptVisibility
    timebox_minutes: int | None
    max_turns: int | None
    turn_strategy: TurnStrategy
    messages: list[AgentMessage]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "mode": self.mode,
            "transcript_visibility": self.transcript_visibility,
            "timebox_minutes": self.timebox_minutes,
            "max_turns": self.max_turns,
            "turn_strategy": self.turn_strategy,
            "messages": [message.to_dict() for message in self.messages],
        }


@dataclass(frozen=True)
class SimulationResult:
    config_name: str
    description: str
    scenario_title: str
    scenario_question: str
    started_at: str
    model: str
    provider: str
    rounds: list[RoundResult]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        config: SimulationConfig,
        model: str,
        provider: str,
        rounds: list[RoundResult],
        metadata: dict[str, Any] | None = None,
    ) -> "SimulationResult":
        return cls(
            config_name=config.name,
            description=config.description,
            scenario_title=config.scenario.title,
            scenario_question=config.scenario.question,
            started_at=datetime.now(timezone.utc).isoformat(),
            model=model,
            provider=provider,
            rounds=rounds,
            metadata={
                "config_metadata": config.metadata,
                "participant_count": len(config.participants),
                "round_count": len(config.rounds),
                **(metadata or {}),
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "config_name": self.config_name,
            "description": self.description,
            "scenario_title": self.scenario_title,
            "scenario_question": self.scenario_question,
            "started_at": self.started_at,
            "model": self.model,
            "provider": self.provider,
            "metadata": self.metadata,
            "rounds": [round_result.to_dict() for round_result in self.rounds],
        }


def _required_text(data: dict[str, Any], key: str, path: str) -> str:
    if key not in data:
        raise ConfigError(f"{path}.{key} is required.")
    value = str(data[key])
    if not value.strip():
        raise ConfigError(f"{path}.{key} cannot be empty.")
    return value


def _ensure_object(value: Any, path: str) -> None:
    if not isinstance(value, dict):
        raise ConfigError(f"{path} must be an object.")


def _optional_text(
    data: dict[str, Any],
    key: str,
    default: str,
    path: str,
) -> str:
    if key not in data or data[key] is None:
        return default
    return str(data[key])


def _required_identifier(data: dict[str, Any], key: str, path: str) -> str:
    value = _required_text(data, key, path).strip()
    _validate_identifier(value, f"{path}.{key}")
    return value


def _optional_identifier(
    data: dict[str, Any],
    key: str,
    default: str,
    path: str,
) -> str:
    value = _optional_text(data, key, default, path).strip()
    _validate_identifier(value, f"{path}.{key}")
    return value


def _validate_identifier(value: str, path: str) -> None:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    if not value or any(character not in allowed for character in value):
        raise ConfigError(
            f"{path} must contain only letters, numbers, underscores, or hyphens."
        )


def _optional_text_list(data: dict[str, Any], key: str, path: str) -> list[str]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ConfigError(f"{path}.{key} must be a list.")
    return [str(item) for item in value]


def _required_mapping(data: dict[str, Any], key: str, path: str) -> dict[str, Any]:
    if key not in data:
        raise ConfigError(f"{path}.{key} is required.")
    value = data[key]
    if not isinstance(value, dict):
        raise ConfigError(f"{path}.{key} must be an object.")
    return dict(value)


def _optional_mapping(data: dict[str, Any], key: str, path: str) -> dict[str, Any]:
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{path}.{key} must be an object.")
    return dict(value)


def _round_participants(value: Any, path: str) -> str | list[str]:
    if value == "all":
        return "all"
    if isinstance(value, str):
        raise ConfigError(f"{path}.participants must be 'all' or a list of ids.")
    if not isinstance(value, list):
        raise ConfigError(f"{path}.participants must be 'all' or a list of ids.")

    participant_ids: list[str] = []
    for item in value:
        participant_id = str(item).strip()
        _validate_identifier(participant_id, f"{path}.participants[]")
        participant_ids.append(participant_id)
    return participant_ids


def _optional_positive_int(
    data: dict[str, Any],
    key: str,
    path: str,
) -> int | None:
    if key not in data or data[key] is None:
        return None
    try:
        value = int(data[key])
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{path}.{key} must be a positive integer.") from exc
    if value <= 0:
        raise ConfigError(f"{path}.{key} must be a positive integer.")
    return value


def _require_unique_ids(label: str, ids: list[str]) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for item_id in ids:
        if item_id in seen:
            duplicates.append(item_id)
        seen.add(item_id)
    if duplicates:
        raise ConfigError(f"{label} contains duplicate id(s): {sorted(duplicates)}")
