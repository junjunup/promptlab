<div align="center">

# 🧪 PromptLab

**A lightweight, YAML-driven LLM evaluation toolkit for Python.**

Test your prompts, compare models, catch regressions — all from the command line.

[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue)](https://pypi.org/project/promptlab/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](.github/workflows/ci.yml)

[Quick Start](#-quick-start) · [Installation](#-installation) · [YAML Reference](#-yaml-reference) · [Evaluators](#-evaluators) · [中文文档](README_CN.md)

</div>

---

## 🤔 Why PromptLab?

[Promptfoo](https://github.com/promptfoo/promptfoo) was the gold standard for LLM evaluation — until [OpenAI acquired it](https://dev.to/nebulagg/top-5-ai-agent-eval-tools-after-promptfoos-exit-576i) for $86M in March 2026. If you're a **Python developer** looking for a vendor-neutral, lightweight alternative, PromptLab is for you.

| Feature | PromptLab | Promptfoo | DeepEval |
|---------|-----------|-----------|----------|
| Language | **Python** 🐍 | Node.js | Python |
| Config | **YAML** (familiar!) | YAML | Python code |
| Learning curve | ⭐ Minimal | ⭐ Low | ⭐⭐⭐ Medium |
| Vendor-neutral | ✅ 100% | ⚠️ OpenAI-owned | ✅ |
| CLI experience | ✅ Rich colors | ✅ Excellent | ❌ No CLI |
| Install size | **< 5MB** | ~50MB | ~20MB |
| Cost tracking | ✅ Built-in | ❌ | ❌ |
| pytest integration | ✅ | ❌ | ✅ |

## 🚀 Quick Start

**1. Install**

```bash
pip install promptlab
pip install promptlab[openai]  # For OpenAI support
```

**2. Create a config**

```bash
promptlab init  # Generates eval.yaml
```

**3. Run evaluation**

```bash
promptlab run eval.yaml
```

That's it! You'll see a colorful results matrix in your terminal:

```
🧪 PromptLab v0.1.0 — Running evaluation...

📊 Results Matrix
┌──────────────────────┬────────────┬────────────┐
│ Test Case            │ v1         │ v2         │
├──────────────────────┼────────────┼────────────┤
│ Clearly positive     │ ✅ PASS    │ ✅ PASS    │
│ Clearly negative     │ ✅ PASS    │ ✅ PASS    │
│ Neutral statement    │ ❌ FAIL    │ ✅ PASS    │
│ Sarcastic positive   │ ✅ PASS    │ ✅ PASS    │
├──────────────────────┼────────────┼────────────┤
│ Pass Rate            │ 75%        │ 100%       │
└──────────────────────┴────────────┴────────────┘

💰 Cost Summary
   gpt4-mini     $0.0012  (1,204 tokens, avg 320ms)
   Total         $0.0012

✅ 7/8 passed (1 failed) — 88% pass rate
   ⏱  Completed in 2.3s
```

## 📦 Installation

```bash
# Core (no LLM providers)
pip install promptlab

# With providers
pip install promptlab[openai]        # OpenAI
pip install promptlab[anthropic]     # Anthropic
pip install promptlab[ollama]        # Ollama (local)
pip install promptlab[all]           # Everything
```

## 📝 YAML Reference

```yaml
# eval.yaml
description: "Sentiment analysis evaluation"

providers:
  - id: gpt4
    type: openai              # openai | anthropic | ollama
    model: gpt-4o-mini
    temperature: 0
  - id: claude
    type: anthropic
    model: claude-3-5-haiku-20241022

prompts:
  - id: v1
    content: |
      Classify sentiment as positive/negative/neutral.
      Text: {{text}}
  - id: v2
    content: |
      You are a sentiment expert. Classify: {{text}}
      Reply with ONE word only.

tests:
  - description: "Happy review"
    vars:
      text: "This product is amazing!"
    assert:
      - type: contains
        value: "positive"
      - type: cost
        max_tokens: 100

settings:
  concurrency: 5
  timeout: 30
  output: results/eval.json
```

### Environment Variables

API keys can be set via environment variables:

```yaml
providers:
  - id: gpt4
    type: openai
    model: gpt-4o-mini
    api_key: ${OPENAI_API_KEY}
```

## 🔍 Evaluators

| Type | Description | Config |
|------|------------|--------|
| `exact` | Exact string match | `value: "expected"` |
| `contains` | Substring match (case-insensitive) | `value: "keyword"` |
| `regex` | Regular expression match | `value: "\\d+"` |
| `json_valid` | Valid JSON check (+ optional key check) | `value: "key_name"` |
| `similarity` | Text similarity (0-1 score) | `value: "expected"`, `threshold: 0.8` |
| `llm_judge` | LLM-as-judge evaluation | `value: "criteria"`, `judge_provider: "gpt4"` |
| `cost` | Token usage limit | `max_tokens: 500` |

## 🖥️ CLI Reference

```bash
# Run evaluation
promptlab run eval.yaml
promptlab run eval.yaml --output results.json --format json
promptlab run eval.yaml --provider gpt4    # Single provider

# Initialize
promptlab init                             # Generate example config
promptlab init --output my_eval.yaml

# Version
promptlab version
```

## 🐍 Python API

```python
from promptlab import run_evaluation

results = run_evaluation("eval.yaml")
print(f"Pass rate: {results['overall_pass_rate']:.0%}")
print(f"Total cost: ${results['total_cost_usd']:.4f}")
```

## 🤝 Contributing

Contributions are welcome! Please see our [contribution guidelines](CONTRIBUTING.md).

```bash
# Development setup
git clone https://github.com/junjunup/promptlab.git
cd promptlab
pip install -e ".[dev]"

# Run tests
pytest tests/ --cov=src/promptlab

# Lint
ruff check src/ tests/
ruff format src/ tests/
```

## 📄 License

[MIT](LICENSE) © 2026 junjunup
