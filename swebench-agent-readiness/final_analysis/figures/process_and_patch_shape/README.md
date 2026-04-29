# Process and Patch-Shape Figures

These figures answer: did the degradation change how Codex searched or patched, even when official success stayed the same?

- `changed_file_delta_by_condition/`: degraded minus clean changed-file count. Positive means Codex touched more files after degradation.
- `files_opened_exploration_by_condition/`: degraded minus clean files opened before the first edit.
- `exploration_efficiency_delta_by_condition/`: degraded minus clean ratio of useful early file opens. Negative means early exploration became less focused.

Main read: non-outcome effects are real but heterogeneous.
