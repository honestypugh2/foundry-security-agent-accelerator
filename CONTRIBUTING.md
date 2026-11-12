# Contributing

Use `make setup`, `make validate`, and `make dependency-scan`.
Add focused tests for changed boundaries. Preserve raw evaluator records,
unknown integration states, correlation IDs and fail-closed release gates.
No live credentials are needed for tests. Tests inject external dependencies.
Never use live tenant operations as a unit test.

Submit only synthetic data. Review `make secret-scan` output and the complete
staged file list before committing. Remote publishing and resource changes
require explicit owner authorization.
