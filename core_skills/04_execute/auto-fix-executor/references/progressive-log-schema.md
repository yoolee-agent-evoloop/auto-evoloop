# Progressive Log Schema

```json
{
  "experiment_id": "",
  "round": "round_1",
  "iterations": [
    {
      "iteration_id": "iter_001",
      "fixes": [],
      "commands": [],
      "baseline_scores": {},
      "candidate_scores": {},
      "regressions": [],
      "d1_decision": "COMMIT|ROLLBACK",
      "d2_decision": "CONTINUE|EXIT",
      "notes": ""
    }
  ]
}
```

Write this file after every iteration so execution can be audited or resumed.
