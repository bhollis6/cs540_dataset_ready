# Task Packet: encode/httpx / httpx_pr_2423

## Overview
- Harness: `codex_cli`
- Conditions: 2
- Successes: 1
- Failures: 1
- Errors: 0

## Findings
- Clean baseline passed with 4 pre-edit file opens and exploration_efficiency=0.75.
- `naming` failed with completion_reason=oracle_fail; FAIL_TO_PASS failures=0, PASS_TO_PASS regressions=26.
- `naming` reduced success_rate by 1.0 versus clean for this task.

## Condition Outcomes
- `clean`: status=SUCCESS reason=oracle_pass exploration_efficiency=0.75 total_duration_seconds=239.47594022750854
- `naming`: status=FAIL reason=oracle_fail exploration_efficiency=0.75 total_duration_seconds=312.16074681282043
  FAIL_TO_PASS failures=0 PASS_TO_PASS regressions=26

## Deltas Vs Clean
- `naming`: delta_success_rate=-1.0 delta_exploration_efficiency=0.0 delta_total_duration_seconds=72.6848
