# Execution Observation Schema

```json
{
  "iteration_id": "",
  "timestamp": "",
  "adapter": "",
  "command": "",
  "status": "success|failed|skipped",
  "duration_seconds": 0,
  "stdout_summary": "",
  "stderr_summary": "",
  "follow_up_required": false
}
```

Record observations without including secrets, raw user data, or private service
URLs.
