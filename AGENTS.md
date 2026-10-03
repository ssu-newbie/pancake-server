# Working on PancakE

- Read `README.md`, `docs/architecture.md`, and `docs/handoff.md` before changing behavior.
- Keep `python -m uvicorn pancake_server:app` working. Preserve the default JSON data paths unless a migration is part of the task.
- Install development dependencies with `python -m pip install -r requirements-dev.txt`; run `python -m pytest -q`.
- Tests must use temporary directories. Never test writes or load against the deployed server without an explicit task to do so.
- Keep changes to API validation, persistence and structure reviewable separately. Existing truncation, empty-response HTTP 200, and score handling are characterized in the contract tests.
- Do not commit real survey responses, scores, credentials, or generated environments.
- Treat the imported Claude handoff as historical context. Verify source and runtime behavior before describing an assertion as independently confirmed.
- Record meaningful behavior changes, verification outcomes and remaining limitations in `docs/`.
