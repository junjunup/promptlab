# Contributing to PromptLab

Thanks for your interest in contributing! 🎉

## Development Setup

```bash
git clone https://github.com/junjunup/promptlab.git
cd promptlab
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ --tb=short -q --cov=src/promptlab
```

## Code Quality

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/
```

## Pull Request Process

1. Fork the repo and create a feature branch
2. Write tests for any new functionality
3. Ensure all tests pass and ruff reports zero errors
4. Submit a PR with a clear description

## Code Style

- Use type annotations on all function signatures
- Write Google-style docstrings for all public APIs
- Keep line length ≤ 88 characters
- Use `from __future__ import annotations` in every file

## Adding a New Evaluator

1. Create `src/promptlab/evaluators/my_evaluator.py`
2. Inherit from `BaseEvaluator` and implement `evaluate()`
3. Register in `evaluators/registry.py`
4. Add the type to `AssertionType` enum in `models.py`
5. Write tests in `tests/test_evaluators/`

## Adding a New Provider

1. Create `src/promptlab/providers/my_provider.py`
2. Inherit from `BaseProvider` and implement `complete()`
3. Register in `providers/registry.py`
4. Add the type to `ProviderType` enum in `models.py`
5. Write tests in `tests/test_providers/`
