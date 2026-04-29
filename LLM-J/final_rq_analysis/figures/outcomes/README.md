# Outcome Figures

Figures about whether the agent solved each historical task under each codebase condition.

## Same-Task Outcome Shifts Compared With Clean

Folder: `paired_degraded_vs_clean_outcome_shifts/`

Files: `paired_degraded_vs_clean_outcome_shifts/paired_degraded_vs_clean_outcome_shifts.png`, `paired_degraded_vs_clean_outcome_shifts/paired_degraded_vs_clean_outcome_shifts.pdf`, `paired_degraded_vs_clean_outcome_shifts/paired_degraded_vs_clean_outcome_shifts.svg`

For each degraded condition, this compares the same historical PR against its clean run. Red bars are the strongest evidence that the degradation hurt the agent.

## Repository Difficulty Distribution

Folder: `repo_difficulty_distribution/`

Files: `repo_difficulty_distribution/repo_difficulty_distribution.png`, `repo_difficulty_distribution/repo_difficulty_distribution.pdf`, `repo_difficulty_distribution/repo_difficulty_distribution.svg`

Overall solved-run share by repository. This shows why paired and per-repo sensitivity analyses matter.

## Solved And Failed Runs By Condition

Folder: `success_failure_counts_by_condition/`

Files: `success_failure_counts_by_condition/success_failure_counts_by_condition.png`, `success_failure_counts_by_condition/success_failure_counts_by_condition.pdf`, `success_failure_counts_by_condition/success_failure_counts_by_condition.svg`

Counts of the 30 runs in each condition. A run is one agent attempt on one historical PR under one condition.

## Agent Solve Rate By Codebase Condition

Folder: `success_rate_by_condition/`

Files: `success_rate_by_condition/success_rate_by_condition.png`, `success_rate_by_condition/success_rate_by_condition.pdf`, `success_rate_by_condition/success_rate_by_condition.svg`

Each bar is the share of 30 runs solved under one condition. Error bars are Wilson 95% confidence intervals. Naming is visibly lower than clean; removing visible tests is not.
