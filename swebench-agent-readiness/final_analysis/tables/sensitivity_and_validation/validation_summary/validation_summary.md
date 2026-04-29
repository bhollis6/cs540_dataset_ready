| name | expected | observed | passed | notes |
| --- | --- | --- | --- | --- |
| RQ1 CSV row count | 128 | 128 | True |  |
| RQ1 JSON row count | 128 | 128 | True |  |
| RQ2 CSV row count | 256 | 256 | True |  |
| RQ2 JSON row count | 256 | 256 | True |  |
| No duplicate RQ1 instance/condition/replication rows | 0 | 0 | True |  |
| Fully complete repos | astropy/astropy, django/django, matplotlib/matplotlib, psf/requests, pydata/xarray, pylint-dev/pylint, pytest-dev/pytest, scikit-learn/scikit-learn, sphinx-doc/sphinx, sympy/sympy | astropy/astropy, django/django, matplotlib/matplotlib, psf/requests, pydata/xarray, pylint-dev/pylint, pytest-dev/pytest, scikit-learn/scikit-learn, sphinx-doc/sphinx, sympy/sympy | True | Definition: at least three tasks, each with all four degradation families. |
| Fully complete repo count | 10 | 10 | True |  |
| Represented repo count | 11 | 11 | True |  |
| Unique task count | 32 | 32 | True |  |
| Clean-success to degraded-failure transitions | 11 | 11 | True |  |
| Regression-test damage rows | 11 | 11 | True |  |
| RQ1 rows match comparison JSON packets | 0 | 0 | True | Checks success flags, target/regression failure counts, selected condition, replication index, and core deltas. |
| Corrected clean token formula input+output | 0 | 0 | True | cached_input_tokens is diagnostic and must not be added. |
| Corrected degraded token formula input+output | 0 | 0 | True | cached_input_tokens is diagnostic and must not be added. |
| RQ2 has clean and degraded side for every comparison | 0 | 0 | True |  |
| RQ2 comparison files join to RQ1 | 0 | 0 | True |  |
