# Agent Simulation Lab

A small Python framework for running prompt-configured multi-agent simulations.

The original research project, **Synthetic Citizen Jury AI for Moral Deliberation**, remains available through citizen-jury presets. The implementation has been generalized so the same runner can simulate other groups as well: hackathon teams, Delphi panels, adversarial reviewers, consensus groups, or any custom agent workflow defined in JSON.

This repository was originally created with [Co-Sci](https://co-sci.org).

## Use Cases

- Compare synthetic citizen-jury deliberation with and without a foreperson.
- Test group dynamics such as consensus seeking, anonymous Delphi revision, and adversarial collaboration.
- Run a one-hour peer-agent hackathon from a user-supplied challenge prompt.
- Create new simulations by changing participants, roles, rounds, and prompts without editing engine code.

## Quick Start

From a fresh clone:

```bash
git clone https://github.com/prashaantr/synthetic-citizen-jury-ai-moral-deliberation.git
cd synthetic-citizen-jury-ai-moral-deliberation
```

Run without installing anything:

```bash
PYTHONPATH=code python3 -m agent_simulation --list-presets
```

List available presets:

```bash
PYTHONPATH=code python3 -m agent_simulation --list-presets
```

Run a dry-run hackathon simulation:

```bash
PYTHONPATH=code python3 -m agent_simulation configs/hackathon_one_hour.json \
  --prompt "Design an AI workflow for triaging city pothole reports." \
  --max-participants 2
```

Run a foreperson-led jury dry run:

```bash
PYTHONPATH=code python3 -m agent_simulation configs/citizen_jury_with_foreperson.json --max-participants 2
```

Dry runs do not call an external model. They validate the config, render prompts, execute the round structure, and write sample outputs to `runs/`.

## Installation

The dry-run path uses only the Python standard library.

Recommended local setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Then run:

```bash
agent-sim --list-presets
agent-sim configs/hackathon_one_hour.json --max-participants 2
```

For OpenAI-backed runs:

```bash
pip install -e '.[openai]'
export OPENAI_API_KEY='your-key'
agent-sim configs/hackathon_one_hour.json --provider openai --model <model-name>
```

Use `--max-participants` while testing to control cost and latency.

If you do not want to install the package, prefix commands with `PYTHONPATH=code`:

```bash
PYTHONPATH=code python3 -m agent_simulation configs/hackathon_one_hour.json \
  --prompt "Your hackathon challenge"
```

## Presets

| Preset | Purpose |
| --- | --- |
| `configs/citizen_jury_with_foreperson.json` | Foreperson-led deliberation with midpoint summary and final verdict. |
| `configs/citizen_jury_without_foreperson_consensus.json` | Leaderless consensus process with a neutral recorder. |
| `configs/citizen_jury_without_foreperson_delphi.json` | Anonymous Delphi-style process with private ballots and anonymized revision. |
| `configs/citizen_jury_without_foreperson_adversarial.json` | No-foreperson adversarial collaboration with critique, steelman, and repair rounds. |
| `configs/hackathon_one_hour.json` | Time-boxed peer group that accepts a challenge prompt, deliberates, handles interruptions, and produces one final answer. |

## Hackathon Preset

The hackathon preset models a 60-minute peer deliberation. It does not assign fixed product, design, engineering, or management roles. Agents are equal-status participants whose behavior is shaped by a configurable persona harness.

| Round | Timebox | Goal |
| --- | ---: | --- |
| Independent read | 8 min | Each peer frames the challenge without social pressure. |
| Live divergence | 16 min | Agents interact in a shared group-chat transcript. |
| Interruption window | 12 min | Agents interrupt, redirect, merge, or build when the group is drifting. |
| Convergence | 16 min | Agents choose what the group should ship. |
| Final artifact | 8 min | A neutral recorder writes the deliverable and preserves dissent. |

Pass a challenge prompt at runtime:

```bash
PYTHONPATH=code python3 -m agent_simulation configs/hackathon_one_hour.json \
  --prompt "Design an AI assistant that helps a city prioritize pothole repairs."
```

Or read it from a file:

```bash
PYTHONPATH=code python3 -m agent_simulation configs/hackathon_one_hour.json \
  --prompt-file challenge.txt
```

Override scenario variables without editing JSON:

```bash
PYTHONPATH=code python3 -m agent_simulation configs/hackathon_one_hour.json \
  --prompt-file challenge.txt \
  --var target_user="Hackathon judges" \
  --var success_criteria="Novel, feasible, demoable in one hour"
```

The persona harness lives in `configs/hackathon_one_hour.json`:

```json
{
  "harness": {
    "shared_instructions": "All agents are equal-status hackathon participants.",
    "persona_template": "Persona harness for {agent_name}: ...",
    "interaction_protocol": ["Keep most turns under 140 words.", "..."],
    "output_contract": "The final output must include..."
  }
}
```

Agent characteristics live under `participants[].attributes`:

```json
{
  "id": "alex",
  "name": "Alex",
  "role": "Peer contributor",
  "attributes": {
    "temperament": "decisive, pragmatic",
    "strengths": "scope control, crisp recommendations",
    "interruption_style": "interrupts when the group is drifting",
    "failure_mode": "may converge too early"
  }
}
```

These attributes are injected into the agent's private system prompt through the harness. They are not job titles.

## Where Agent Character Prompts Go

For the hackathon simulation, agent character creation happens in `configs/hackathon_one_hour.json`.

Use these fields:

| Field | What to Put There |
| --- | --- |
| `participants[].name` | Display name for the agent in the transcript. |
| `participants[].role` | Keep this broad, usually `Peer contributor`, unless you intentionally want a job-like role. |
| `participants[].prompt` | The core private character prompt for that agent. Put the agent's behavioral mandate here. |
| `participants[].attributes` | Structured personality and collaboration traits used by the harness. |
| `harness.persona_template` | The shared template that turns attributes into each agent's private system prompt. |
| `harness.shared_instructions` | Rules every agent receives. |
| `harness.interaction_protocol` | Group behavior rules for all agents. |

Minimal character example:

```json
{
  "id": "morgan",
  "name": "Morgan",
  "role": "Peer contributor",
  "prompt": "You are an equal peer in the hackathon. You are contrarian when the group is drifting toward a fashionable but weak answer.",
  "attributes": {
    "temperament": "contrarian, concise, evidence-seeking",
    "strengths": "finding weak assumptions and simpler alternatives",
    "collaboration_style": "challenges politely, then offers a replacement",
    "interruption_style": "interrupts when the group accepts an unsupported premise",
    "failure_mode": "may reject useful ideas too quickly"
  }
}
```

The harness then injects those fields through this template:

```json
"persona_template": "Persona harness for {agent_name}:\\n- Temperament: {agent_temperament}\\n- Strengths: {agent_strengths}\\n- Collaboration style: {agent_collaboration_style}\\n- Interruption style: {agent_interruption_style}\\n- Known failure mode: {agent_failure_mode}\\n\\nUse these traits to decide when to propose, challenge, interrupt, merge ideas, or yield."
```

If you add a new attribute like `"domain_bias": "prefers open-source tools"`, reference it in the template as `{agent_domain_bias}`.

## Common Commands

Dry-run the hackathon preset with an inline prompt:

```bash
PYTHONPATH=code python3 -m agent_simulation configs/hackathon_one_hour.json \
  --prompt "Come up with an AI agent simulation for testing startup ideas." \
  --output-dir runs/hackathon-test
```

Dry-run from a prompt file:

```bash
PYTHONPATH=code python3 -m agent_simulation configs/hackathon_one_hour.json \
  --prompt-file challenge.txt \
  --output-dir runs/hackathon-test
```

Override runtime variables:

```bash
PYTHONPATH=code python3 -m agent_simulation configs/hackathon_one_hour.json \
  --prompt-file challenge.txt \
  --var target_user="Hackathon judges" \
  --var success_criteria="Novel, feasible, demoable in one hour"
```

Run after editable install:

```bash
agent-sim configs/hackathon_one_hour.json \
  --prompt-file challenge.txt
```

Run with OpenAI:

```bash
export OPENAI_API_KEY='your-key'
agent-sim configs/hackathon_one_hour.json \
  --provider openai \
  --model <model-name> \
  --prompt-file challenge.txt
```

## Citizen Jury Presets

The citizen-jury presets keep the original moral-deliberation research direction intact while making the group dynamic explicit.

Use them to compare:

- Foreperson-led verdict synthesis versus no-foreperson aggregation.
- Named deliberation versus anonymous Delphi rounds.
- Consensus-seeking discussion versus adversarial collaboration.
- Majority verdicts, minority reports, safeguards, and unresolved objections.

The current shared scenario is public AI surveillance policy. Replace `scenario.title`, `scenario.question`, `scenario.background`, and `decision_options` to evaluate a different policy question.

## Configuration Model

Each config has four main sections:

| Section | Description |
| --- | --- |
| `scenario` | The question, background, decision options, and prompt variables. |
| `participants` | Agent ids, names, roles, role prompts, and optional attributes. |
| `harness` | Optional persona and interaction scaffold applied behind the scenes. |
| `rounds` | The deliberation protocol. |
| `metadata` | Experiment labels and analysis tags. |

Round fields:

| Field | Values |
| --- | --- |
| `mode` | `individual`, `group_chat`, or `synthesis` |
| `participants` | `"all"` or a list of participant ids |
| `transcript_visibility` | `named`, `anonymous`, or `hidden` |
| `speaker_id`, `speaker_name`, `speaker_role` | Identity used for synthesis rounds |
| `timebox_minutes` | Optional positive integer used in outputs and prompts |
| `max_turns` | Number of turns in a `group_chat` round |
| `turn_strategy` | `round_robin` or `interruptions` |
| `interruption_rules` | Round-specific guidance for interruption windows |

Prompt templates are strict. If a prompt references an unknown variable, the run fails instead of silently producing a bad prompt.

Common template variables:

- `{scenario_title}`
- `{scenario_question}`
- `{scenario_background}`
- `{decision_options}`
- `{participants}`
- `{transcript}`
- `{agent_id}`
- `{agent_name}`
- `{agent_role}`
- `{round_title}`
- `{round_timebox_minutes}`
- `{round_max_turns}`
- `{turn_number}`
- `{turns_remaining}`
- `{current_speaker}`
- `{event_type}`
- `{interruption_rules}`
- any custom key from `scenario.variables`

Runtime prompt inputs are injected as both `{challenge_prompt}` and `{challenge_brief}` for compatibility.

## Design Rationale

The hackathon flow is intentionally not a long open-ended debate. It uses a short independent-read phase, shared group-chat turns, an explicit interruption window, and a final recorder because current multi-agent and hackathon research points to a few practical constraints:

- Multi-agent systems benefit from configurable conversation patterns and dynamic group chat controls.
- Hackathon collaboration usually happens in small teams with divergent and convergent phases, plus checkpoints or facilitation.
- Debate can drift or collapse into social conformity, so the preset limits rounds, preserves dissent, and does not require consensus before output.
- The transcript is treated as the audit trail; the final artifact should be traceable to the deliberation.

Useful background:

- AutoGen multi-agent conversations and dynamic group chat: <https://autogenhub.github.io/autogen/docs/Use-Cases/agent_chat/>
- Online hackathon collaboration patterns: <https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2022.983164/full>
- Multi-agent debate failure modes and diversity effects: <https://arxiv.org/abs/2511.07784>
- Consensus-free debate and anti-conformity motivation: <https://arxiv.org/abs/2509.11035>

## Creating a New Simulation

Copy a nearby preset:

```bash
cp configs/hackathon_one_hour.json configs/my_simulation.json
```

Then update:

1. `name` and `description`
2. `scenario`
3. `participants`
4. `rounds`
5. prompt templates

Run a dry run before using a paid model:

```bash
PYTHONPATH=code python3 -m agent_simulation configs/my_simulation.json \
  --prompt "Your challenge here" \
  --max-participants 2
```

## Output

Each run writes two files under `runs/` unless `--output-dir` is set:

- JSON for programmatic analysis
- Markdown for human review

The output records provider, model, scenario, round settings, participant roles, generated messages, and run metadata.

## Testing

Run the unit tests:

```bash
PYTHONPATH=code python3 -m unittest discover -s tests -v
```

Run syntax checks:

```bash
python3 -m compileall -q code tests
```

Validate preset JSON:

```bash
for f in configs/*.json; do python3 -m json.tool "$f" >/dev/null; done
```

Smoke-test every preset:

```bash
for f in configs/*.json; do
  PYTHONPATH=code python3 -m agent_simulation "$f" --max-participants 2 --output-dir runs/smoke
done
```

## Repository Layout

```text
.
├── code/
│   ├── agent_simulation/
│   │   ├── cli.py          # command-line runner
│   │   ├── clients.py      # dry-run and OpenAI clients
│   │   ├── engine.py       # round execution
│   │   ├── io.py           # config and result IO
│   │   ├── prompts.py      # prompt rendering and transcripts
│   │   └── schema.py       # config/result dataclasses and validation
│   └── run_simulation.py
├── configs/                # reusable simulation presets
├── tests/                  # unit tests
├── notes/                  # research notes
├── data/                   # data files
├── paper.tex               # manuscript draft
└── README.md
```

## Research Materials

The original research materials are still present:

- `notes/sections/concept.md`
- `hypotheses.json`
- `papers.json`
- `proposals.json`
- `analyses.json`
- `paper.tex`

Those files describe the synthetic citizen-jury research agenda. The new engine makes it easier to run repeatable experiments across different deliberation protocols.
