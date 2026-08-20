# qFoldIT Platform Integration

Virtual Lab is the protocol-execution and educational experience layer for qFoldIT missions.

## Flow

```text
qFoldIT Mission
      |
      v
Protocol / Experiment Definition
      |
      v
Scientific State + UAG bindings
      |
      v
Virtual Lab runtime
      |
      v
Submission / Observation
      |
      v
CAMEO / Scientific Validation
```

Virtual Lab owns protocol presentation, interactive learning and observation capture. Scientific truth remains in the configured scientific services.

## Canonical boundaries

- Missions are identified by `qfoldit.mission/1.0`.
- Runtime outputs are normalized to `qfoldit.submission/1.0` where scientific evaluation is required.
- Scientific validation outputs are represented by `qfoldit.evidence/1.0`.
- Runtime and laboratory lifecycle notifications use `qfoldit.event/1.0`.
- World objects are represented through Scientific Object Schema and UAG-compatible bindings.

## Educational and research profiles

The same runtime can support educational protocol simulations and research-oriented experimental workflows. Mission policy determines which scientific validators, data retention rules and publication permissions apply.
