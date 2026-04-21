# Repository Guidelines

## Project Structure & Module Organization
Core domain models live in `real/` (`event.py`, `team.py`, `match.py`, `alliance.py`). API and data-fetching code lives in `data/`, and tournament logic lives under `ruleset/`. Shared helpers belong in `utils/`. Tests are in `test/`. Cached API payloads are stored in `cache/<season>/`, and local environment files such as `.env` and `venv/` should stay out of commits unless explicitly required.

## Build, Test, and Development Commands
Use Python 3.13 with PDM.

- `pdm install -G typecheck`: install runtime and type-check dependencies.
- `pdm run test`: run the full `unittest` suite in `test/`; run this first after every change.
- `pdm run typecheck`: run `basedpyright` in strict mode against `real/`, `ruleset/`, and `data/`; run this after tests on every change.
- `python -m unittest discover -s test -p "*.py" -v`: direct test runner equivalent when PDM is unavailable.

## Coding Style & Naming Conventions
Follow the existing style: 4-space indentation, explicit type hints, and small focused modules. Use `camelCase` for variables and parameters, `lower_snake_case` for functions and methods, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants and enum-like values. Keep public APIs typed well enough to satisfy strict `basedpyright`. Prefer straightforward data plumbing over clever abstractions.

## Import Rules
Prefer keeping all imports at the top of the file. If an import is only needed for type annotations, guard it with `TYPE_CHECKING`. If a runtime circular dependency cannot be resolved cleanly otherwise, delayed imports may be used when necessary, but keep them rare and prefer file-top imports whenever possible. For example:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.frc_json import EventRequestType
```

## Testing Guidelines
Tests use the standard library `unittest` framework. Name files `test_*.py`, test classes `Test...`, and test methods `test_...`. Test method names should describe the function being tested without embedding a specific case or fixture detail; prefer names like `test_request_qualification_matches` over `test_matches` or `test_request_qualification_matches_uses_team_6907_match_data`. Keep assertions specific and message-bearing, matching the current suite style. After each modification, run `pdm run test` and then `pdm run typecheck`; if either fails, fix the issue before submitting. Some tests exercise live FRC API requests and populate `cache/`; make cache behavior explicit in tests and avoid relying on hidden local state.

## Commit & Pull Request Guidelines
Use concise imperative commit messages such as `Add alliance ranking validation`. Keep commits scoped to one change. Pull requests should describe the behavior change, list validation performed (`pdm run test`, `pdm run typecheck`), and include sample output or screenshots only when user-visible behavior changes.

## Security & Configuration Tips
Do not commit secrets from `.env`. Treat `cache/` as generated data unless the change intentionally updates fixtures or reproducible snapshots. If a change depends on network access, document the endpoint and the expected cached fallback path.

## Change Scope
Keep each patch or pull request focused on one modification item. If a larger effort is needed, split it into reviewable steps instead of bundling unrelated edits together.
