# Token Figures

These figures answer: did the degradation make Codex spend more model tokens?

- `corrected_token_usage_by_condition/`: median clean vs degraded token usage by condition. Unit is thousands of corrected cumulative tokens.
- `paired_token_delta_by_condition/`: degraded minus clean token usage by paired comparison. Unit is thousands of corrected cumulative tokens.

Corrected tokens mean `input_tokens + output_tokens`. Cached input tokens are not added because they are a subset of input tokens.
