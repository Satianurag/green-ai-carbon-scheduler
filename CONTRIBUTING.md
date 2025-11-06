# Contributing Guidelines

Thank you for your interest in contributing! This project aims to make ML training carbon‑aware, measurable, and production‑ready.

## How to Contribute

1. Fork the repository and create a feature branch:
   - `git checkout -b feature/your-feature`
2. Commit with clear messages:
   - `feat: add live CI provider`
   - `fix: handle API timeout`
   - `docs: update README quickstart`
3. Keep changes focused and small. One PR = one logical change.
4. Open a Pull Request describing:
   - What changed and why
   - How to test it
   - Any breaking changes

## Development

- Python 3.11+
- Install deps: `pip install -r requirements.txt`
- Quick run: `bash run.sh`
- CLI help: `python -m greenai.cli -h`

## Code Style

- Follow standard Python style (PEP8). Type hints encouraged.
- Prefer small, testable functions with clear names.
- Avoid hardcoding; pass configuration via CLI flags/env vars when possible.

## Tests (optional)

- If adding logic, consider adding a minimal test or a reproducible example.

## Reporting Issues

- Use the issue tracker with a clear, reproducible description.
- Include logs, commands, and environment details when relevant.

Thanks for helping make AI greener! 🌱
