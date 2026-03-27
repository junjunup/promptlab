# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-27

### Added

- YAML-driven evaluation configuration
- Multi-provider support (OpenAI, Anthropic, Ollama)
- Built-in evaluators: exact match, contains, regex, JSON validation, similarity, LLM-as-Judge, cost check
- Rich CLI with colorful terminal reports
- Evaluation result export (JSON/CSV)
- Token usage & cost tracking
- Parallel model evaluation with comparison matrix
- Async execution for concurrent API calls
