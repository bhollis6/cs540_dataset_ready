# Figures

This directory is grouped by analysis question. Each figure is exported as `.png`, `.pdf`, and `.svg`.

Plain-language terms used here:
- `Run`: one agent attempt on one historical PR under one condition.
- `Condition`: the codebase version shown to the agent, such as clean or naming-degraded.
- `Hidden bug-fix tests`: tests added by the original PR that should fail before the fix and pass after the fix.
- `Previously passing tests`: existing tests that passed before the agent changed code; failures here are regressions.
- `Tokens`: Codex token usage including cached input tokens unless the label says otherwise.

- `outcomes/`: Figures about whether the agent solved each historical task under each codebase condition.
- `failure_modes/`: Figures splitting failures into missed hidden bug-fix tests and regressions in previously passing tests.
- `repo_task_detail/`: Figures showing how outcomes vary by repository and historical pull request.
- `tokens_runtime/`: Figures showing run-time and token-use burden by condition.
- `process/`: Figures from recovered Codex event-log metrics such as command and validation counts.
