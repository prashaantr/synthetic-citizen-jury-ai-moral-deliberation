# Model-Backed Citizen Jury Results

These files are sample transcripts from a four-protocol comparison run on June 12, 2026. Each run used the same scenario and participant roles with `gpt-4o-mini` through the OpenAI provider.

Scenario: Should a city deploy AI-enabled public camera analytics to detect violent incidents in real time?

| Protocol | Config | Markdown transcript | JSON output | Final outcome |
| --- | --- | --- | --- | --- |
| Foreperson-led jury | `citizen-jury-with-foreperson` | [`citizen-jury-with-foreperson-2026-06-12-2011125397780000.md`](citizen-jury-with-foreperson-2026-06-12-2011125397780000.md) | [`citizen-jury-with-foreperson-2026-06-12-2011125397780000.json`](citizen-jury-with-foreperson-2026-06-12-2011125397780000.json) | Limited pilot with strict oversight; rights-focused minority objection preserved. |
| Leaderless consensus | `citizen-jury-without-foreperson-consensus` | [`citizen-jury-without-foreperson-consensus-2026-06-12-2012333413010000.md`](citizen-jury-without-foreperson-consensus-2026-06-12-2012333413010000.md) | [`citizen-jury-without-foreperson-consensus-2026-06-12-2012333413010000.json`](citizen-jury-without-foreperson-consensus-2026-06-12-2012333413010000.json) | Limited pilot with community engagement, audits, and enforceable safeguards. |
| Anonymous Delphi | `citizen-jury-without-foreperson-delphi` | [`citizen-jury-without-foreperson-delphi-2026-06-12-2013439087810000.md`](citizen-jury-without-foreperson-delphi-2026-06-12-2013439087810000.md) | [`citizen-jury-without-foreperson-delphi-2026-06-12-2013439087810000.json`](citizen-jury-without-foreperson-delphi-2026-06-12-2013439087810000.json) | Rejected deployment until stronger safeguards exist. |
| Adversarial collaboration | `citizen-jury-without-foreperson-adversarial` | [`citizen-jury-without-foreperson-adversarial-2026-06-12-2021098125990000.md`](citizen-jury-without-foreperson-adversarial-2026-06-12-2021098125990000.md) | [`citizen-jury-without-foreperson-adversarial-2026-06-12-2021098125990000.json`](citizen-jury-without-foreperson-adversarial-2026-06-12-2021098125990000.json) | Hardened limited-pilot recommendation with stronger scope limits, oversight, and bias controls. |

The main demonstration is protocol sensitivity: foreperson-led, leaderless consensus, and adversarial collaboration converged on a limited-pilot answer, while the anonymous Delphi protocol converged on rejection until stronger safeguards exist.

To reproduce a comparable run:

```bash
export OPENAI_API_KEY='your-key'

for config in \
  configs/citizen_jury_with_foreperson.json \
  configs/citizen_jury_without_foreperson_consensus.json \
  configs/citizen_jury_without_foreperson_delphi.json \
  configs/citizen_jury_without_foreperson_adversarial.json
do
  PYTHONPATH=code python3 -m agent_simulation "$config" \
    --provider openai \
    --model gpt-4o-mini \
    --output-dir results
done
```

These are sample runs, not benchmark evidence. The JSON files are included so later analysis can inspect round structure and generated messages programmatically.
