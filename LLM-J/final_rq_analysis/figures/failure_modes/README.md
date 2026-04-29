# Failure-Mode Figures

Figures splitting failures into missed hidden bug-fix tests and regressions in previously passing tests.

## Why Failed Runs Failed

Folder: `failure_mode_stacked_bars/`

Files: `failure_mode_stacked_bars/failure_mode_stacked_bars.png`, `failure_mode_stacked_bars/failure_mode_stacked_bars.pdf`, `failure_mode_stacked_bars/failure_mode_stacked_bars.svg`

Failures are split into missed hidden bug-fix tests, regressions in previously passing tests, or both. Naming has the broadest failure shape.

## Hidden Bug-Fix Miss Burden

Folder: `hidden_bug_fix_test_miss_burden/`

Files: `hidden_bug_fix_test_miss_burden/hidden_bug_fix_test_miss_burden.png`, `hidden_bug_fix_test_miss_burden/hidden_bug_fix_test_miss_burden.pdf`, `hidden_bug_fix_test_miss_burden/hidden_bug_fix_test_miss_burden.svg`

Total number of hidden bug-fix tests still failing after the agent patch.

## Regression Burden: Previously Passing Tests That Failed

Folder: `regression_burden_previously_passing_tests/`

Files: `regression_burden_previously_passing_tests/regression_burden_previously_passing_tests.png`, `regression_burden_previously_passing_tests/regression_burden_previously_passing_tests.pdf`, `regression_burden_previously_passing_tests/regression_burden_previously_passing_tests.svg`

Total number of previously passing tests that failed after the agent patch. This is regression burden.
