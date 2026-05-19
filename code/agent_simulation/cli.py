from __future__ import annotations

import argparse
from pathlib import Path

from agent_simulation.clients import create_client
from agent_simulation.engine import run_simulation
from agent_simulation.io import list_config_files, load_config, save_result
from agent_simulation.runtime import apply_runtime_inputs, parse_variable_assignments
from agent_simulation.schema import ConfigError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a config-driven multi-agent simulation."
    )
    parser.add_argument(
        "config",
        nargs="?",
        help="Path to a simulation config JSON file.",
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="List JSON configs in the preset directory and exit.",
    )
    parser.add_argument(
        "--config-dir",
        default="configs",
        help="Directory used by --list-presets.",
    )
    parser.add_argument(
        "--provider",
        choices=["dry-run", "openai"],
        default="dry-run",
        help="Model provider to use. dry-run does not call external APIs.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name. Required for non-dry-run providers.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature passed to the model provider.",
    )
    parser.add_argument(
        "--max-participants",
        type=int,
        default=None,
        help="Limit participants per individual round for smoke tests.",
    )
    parser.add_argument(
        "--output-dir",
        default="runs",
        help="Directory where JSON and Markdown run outputs will be written.",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Challenge prompt to inject into scenario variables.",
    )
    parser.add_argument(
        "--prompt-file",
        default=None,
        help="Read the challenge prompt from a UTF-8 text file.",
    )
    parser.add_argument(
        "--var",
        action="append",
        default=None,
        metavar="KEY=VALUE",
        help="Override or add a scenario variable. May be used multiple times.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_presets:
        for config_path in list_config_files(args.config_dir):
            print(config_path)
        return 0

    if not args.config:
        parser.error("config is required unless --list-presets is used")

    if args.provider != "dry-run" and not args.model:
        parser.error("--model is required when --provider is not dry-run")

    if args.max_participants is not None and args.max_participants <= 0:
        parser.error("--max-participants must be greater than zero")

    if args.temperature < 0 or args.temperature > 2:
        parser.error("--temperature must be between 0 and 2")

    model = args.model or "dry-run-model"
    try:
        config = apply_runtime_inputs(
            load_config(Path(args.config)),
            prompt=args.prompt,
            prompt_file=args.prompt_file,
            variables=parse_variable_assignments(args.var),
        )
        client = create_client(args.provider)
        result = run_simulation(
            config=config,
            client=client,
            model=model,
            temperature=args.temperature,
            max_participants=args.max_participants,
            run_metadata={
                "config_path": str(Path(args.config)),
                "output_dir": str(Path(args.output_dir)),
            },
        )
        json_path, markdown_path = save_result(result, args.output_dir)
    except (ConfigError, RuntimeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
