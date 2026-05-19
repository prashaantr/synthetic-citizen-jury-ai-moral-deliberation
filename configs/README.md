# Simulation Presets

This directory contains JSON presets for the reusable agent simulation runner.

## Citizen Jury Variants

- `citizen_jury_with_foreperson.json`
  - Foreperson-led deliberation with midpoint synthesis and a final verdict.
- `citizen_jury_without_foreperson_consensus.json`
  - Equal-status deliberation where a neutral recorder maps consensus and disagreement.
- `citizen_jury_without_foreperson_delphi.json`
  - Anonymous Delphi process with private ballots and anonymized revision.
- `citizen_jury_without_foreperson_adversarial.json`
  - Adversarial collaboration without a foreperson: proposal, critique, steelman, repair, outcome.

These variants are intended for comparing how group structure affects final recommendations, minority reports, and safeguards.

## Hackathon Variant

- `hackathon_one_hour.json`
  - A 60-minute peer deliberation that accepts `--prompt` or `--prompt-file`, uses configurable personality traits, runs group-chat and interruption rounds, and converges on one final answer artifact.

Pass the actual challenge prompt at runtime:

## Running a Preset

From the repository root:

```bash
PYTHONPATH=code python3 -m agent_simulation configs/hackathon_one_hour.json \
  --prompt "Design an AI workflow for triaging city pothole reports."
```

Use `--max-participants 2` for cheap smoke tests.
