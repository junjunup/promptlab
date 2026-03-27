<div align="center">

# 🧪 PromptLab

**轻量级、YAML 驱动的 Python LLM 评估工具包。**

测试你的 Prompt、对比不同模型、捕捉质量回归 —— 全在命令行完成。

[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue)](https://pypi.org/project/promptlab/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](.github/workflows/ci.yml)

[快速开始](#-快速开始) · [安装](#-安装) · [YAML 配置详解](#-yaml-配置详解) · [评估器](#-内置评估器) · [English](README.md)

</div>

---

## 🤔 为什么要用 PromptLab？

### 背景

[Promptfoo](https://github.com/promptfoo/promptfoo) 曾是 LLM 评估领域的标杆工具（10,800+ stars）—— 直到 2026 年 3 月被 OpenAI 以 8600 万美元收购。收购后社区对其供应商中立性产生了广泛担忧。

如果你是 **Python 开发者**，正在寻找一个**供应商中立、轻量级**的替代方案，PromptLab 就是为你而生的。

### 它解决了什么问题？

当你在开发 LLM 应用时，经常会遇到这些痛点：

- 🔄 **改了一行 Prompt，不知道有没有把别的场景搞坏** → PromptLab 提供回归测试
- 🤷 **GPT-4o-mini 和 Claude Haiku 哪个效果更好？** → PromptLab 并行对比多个模型
- 💸 **每次调试都在烧 API 费用，不知道花了多少** → PromptLab 内置成本追踪
- 📋 **评估全靠人肉看输出** → PromptLab 自动化评估，支持 7 种断言类型

### 和竞品的对比

| 特性 | PromptLab | Promptfoo | DeepEval |
|------|-----------|-----------|----------|
| 语言 | **Python** 🐍 | Node.js | Python |
| 配置方式 | **YAML**（简单直观） | YAML | Python 代码 |
| 上手难度 | ⭐ 极低 | ⭐ 低 | ⭐⭐⭐ 中等 |
| 供应商中立 | ✅ 完全中立 | ⚠️ 已被 OpenAI 收购 | ✅ |
| CLI 体验 | ✅ Rich 彩色输出 | ✅ 优秀 | ❌ 无 CLI |
| 安装体积 | **< 5MB** | ~50MB | ~20MB |
| 成本追踪 | ✅ 内置 | ❌ | ❌ |
| pytest 集成 | ✅ | ❌ | ✅ |

---

## 🚀 快速开始

**3 步上手，30 秒体验完整流程：**

**第 1 步：安装**

```bash
pip install promptlab
pip install promptlab[openai]  # 如果用 OpenAI
```

**第 2 步：生成示例配置**

```bash
promptlab init  # 自动生成 eval.yaml
```

**第 3 步：运行评估**

```bash
promptlab run eval.yaml
```

就这么简单！你会在终端看到一个漂亮的彩色结果矩阵：

```
🧪 PromptLab v0.1.0 — Running evaluation...

  📋 Config:     eval.yaml
  🤖 Providers:  1
  📝 Prompts:    2
  🧪 Tests:      4
  📊 Total:      8 evaluations

📊 Results — gpt4-mini
┌──────────────────────┬────────────┬────────────┐
│ Test Case            │ v1         │ v2         │
├──────────────────────┼────────────┼────────────┤
│ 明确正面评价          │ ✅ PASS    │ ✅ PASS    │
│ 明确负面评价          │ ✅ PASS    │ ✅ PASS    │
│ 中性表述              │ ❌ FAIL    │ ✅ PASS    │
│ 反讽/挖苦             │ ✅ PASS    │ ✅ PASS    │
├──────────────────────┼────────────┼────────────┤
│ Pass Rate            │ 75%        │ 100%       │
└──────────────────────┴────────────┴────────────┘

💰 Cost Summary
   gpt4-mini     $0.0012  (1,204 tokens, avg 320ms)
   Total         $0.0012

┌─────────────────────────────────────────────┐
│              Evaluation Complete             │
│                                             │
│ ✅ 7/8 passed (1 failed) — 88% pass rate    │
│ ⏱  Completed in 2.3s                       │
└─────────────────────────────────────────────┘
```

---

## 📦 安装

```bash
# 核心包（不含 LLM 提供商）
pip install promptlab

# 按需安装提供商
pip install promptlab[openai]        # OpenAI (GPT-4o, o1, o3-mini 等)
pip install promptlab[anthropic]     # Anthropic (Claude 3.5 等)
pip install promptlab[ollama]        # Ollama (本地模型: Llama, Qwen 等)
pip install promptlab[all]           # 全部安装
```

### 环境变量配置

API Key 通过环境变量传递（不要写在配置文件里！）：

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

也可以在 YAML 中显式引用：

```yaml
providers:
  - id: gpt4
    type: openai
    model: gpt-4o-mini
    api_key: ${OPENAI_API_KEY}  # 自动从环境变量读取
```

---

## 📝 YAML 配置详解

PromptLab 使用 YAML 文件定义评估计划。一个完整的配置包含 4 个部分：

```yaml
# eval.yaml — PromptLab 评估配置文件

# 1️⃣ 描述（可选）
description: "情感分析 prompt 评估"

# 2️⃣ 提供商 — 定义要评估的 LLM
providers:
  - id: gpt4                    # 自定义 ID，在结果中引用
    type: openai                # openai | anthropic | ollama
    model: gpt-4o-mini          # 模型名称
    temperature: 0              # 温度（建议评估时设为 0）
  - id: claude
    type: anthropic
    model: claude-3-5-haiku-20241022

# 3️⃣ Prompt 模板 — 支持 Jinja2 变量 {{var}}
prompts:
  - id: v1-简单
    content: |
      分析以下文本的情感倾向，返回 positive/negative/neutral。
      文本: {{text}}
  - id: v2-专家
    content: |
      你是一个情感分析专家。请分析以下文本的情感倾向。
      考虑讽刺、语境和隐含情绪。只返回一个词：positive、negative 或 neutral。
      文本: {{text}}

# 4️⃣ 测试用例 — 定义输入和预期断言
tests:
  - description: "积极评价"
    vars:
      text: "这个产品太棒了，我非常喜欢！"
    assert:
      - type: contains           # 输出应包含 "positive"
        value: "positive"
  - description: "消极评价"
    vars:
      text: "质量很差，完全是浪费钱。"
    assert:
      - type: contains
        value: "negative"
  - description: "中性表述"
    vars:
      text: "今天天气还行吧。"
    assert:
      - type: contains
        value: "neutral"
  - description: "反讽识别"
    vars:
      text: "哦太好了，又是周一早上，正是我需要的。"
    assert:
      - type: contains
        value: "negative"
      - type: cost               # 同时检查 token 用量
        max_tokens: 100

# 5️⃣ 全局设置
settings:
  concurrency: 5                # 并行请求数
  timeout: 30                   # 单次请求超时（秒）
  output: results/eval.json     # 结果保存路径
```

### 运行流程

当你执行 `promptlab run eval.yaml` 时，PromptLab 会：

1. 解析 YAML 配置
2. 对每个 **(测试用例 × Prompt 模板 × 提供商)** 的组合：
   - 用 Jinja2 渲染 Prompt（替换 `{{text}}` 等变量）
   - 异步并行调用 LLM API
   - 对返回结果运行所有断言/评估器
3. 汇总结果，输出彩色报告 + JSON/CSV 文件

---

## 🔍 内置评估器

PromptLab 内置 7 种评估器，覆盖常见的 LLM 输出检查场景：

| 类型 | 说明 | 配置示例 | 使用场景 |
|------|------|----------|----------|
| `exact` | 精确匹配 | `value: "Paris"` | 需要完全一致的回答 |
| `contains` | 包含子串（大小写不敏感） | `value: "positive"` | 分类任务、关键词检查 |
| `regex` | 正则表达式匹配 | `value: "\\d{4}-\\d{2}-\\d{2}"` | 格式验证（日期、邮箱等） |
| `json_valid` | JSON 格式验证 | `value: "name"` (可选检查 key) | 结构化输出场景 |
| `similarity` | 文本相似度 (0-1) | `threshold: 0.8` | 允许措辞不同但语义相近 |
| `llm_judge` | LLM 评委 | `value: "评判标准"` | 主观质量评估 |
| `cost` | Token 用量限制 | `max_tokens: 500` | 成本控制 |

### 评估器组合

每个测试用例可以组合多个评估器，**全部通过才算 PASS**：

```yaml
tests:
  - vars:
      question: "法国的首都是哪里？"
    assert:
      - type: contains          # 1. 输出必须包含 "Paris" 或 "巴黎"
        value: "Paris"
      - type: json_valid        # 2. 输出必须是合法 JSON
      - type: cost              # 3. token 用量不超过 200
        max_tokens: 200
```

---

## 🖥️ CLI 命令参考

```bash
# 运行评估（核心命令）
promptlab run eval.yaml                     # 基础运行
promptlab run eval.yaml -o results.json     # 指定输出文件
promptlab run eval.yaml -f csv              # 输出为 CSV 格式
promptlab run eval.yaml -p gpt4            # 只用某个提供商

# 初始化（快速上手）
promptlab init                              # 生成 eval.yaml 示例
promptlab init -o my_eval.yaml              # 自定义文件名

# 查看版本
promptlab version
```

### 退出码

- `0` — 所有测试通过
- `1` — 有测试失败或配置错误

适合在 **CI/CD 流水线** 中使用：

```bash
# GitHub Actions / GitLab CI 中
promptlab run eval.yaml || exit 1
```

---

## 🐍 Python API

除了 CLI，PromptLab 也提供编程接口：

```python
from promptlab import run_evaluation

# 运行评估
results = run_evaluation("eval.yaml")

# 访问结果
print(f"通过率: {results['overall_pass_rate']:.0%}")
print(f"总费用: ${results['total_cost_usd']:.4f}")
print(f"总耗时: {results['total_duration_ms'] / 1000:.1f}s")

# 遍历每条结果
for r in results["results"]:
    status = "✅" if r["passed"] else "❌"
    print(f"  {status} [{r['provider_id']}/{r['prompt_id']}] {r['test_description']}")
```

---

## 📐 架构概览

```
promptlab/
├── src/promptlab/
│   ├── cli.py                # Typer CLI 入口
│   ├── config.py             # YAML 配置解析 + 验证
│   ├── models.py             # Pydantic 数据模型
│   ├── runner.py             # 核心评估引擎（异步并行）
│   ├── exceptions.py         # 统一异常体系
│   ├── providers/            # LLM 提供商适配器
│   │   ├── openai.py         #   OpenAI (GPT-4o, o1, o3 等)
│   │   ├── anthropic.py      #   Anthropic (Claude 3.5 等)
│   │   └── ollama.py         #   Ollama (本地模型)
│   ├── evaluators/           # 评估器
│   │   ├── exact.py          #   精确匹配
│   │   ├── contains.py       #   包含检查
│   │   ├── regex.py          #   正则匹配
│   │   ├── json_valid.py     #   JSON 验证
│   │   ├── similarity.py     #   文本相似度
│   │   ├── llm_judge.py      #   LLM 评委
│   │   └── cost.py           #   成本限制
│   └── reporters/            # 结果报告
│       ├── console.py        #   Rich 彩色终端
│       ├── json_reporter.py  #   JSON 文件
│       └── csv_reporter.py   #   CSV 文件
├── tests/                    # 99 个测试用例
├── examples/                 # 示例配置文件
└── pyproject.toml            # 项目配置 (PEP 621)
```

---

## 🤝 参与贡献

欢迎贡献！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

```bash
# 开发环境搭建
git clone https://github.com/junjunup/promptlab.git
cd promptlab
pip install -e ".[dev]"

# 运行测试
pytest tests/ --cov=src/promptlab

# 代码检查
ruff check src/ tests/
ruff format src/ tests/
```

---

## 📄 许可证

[MIT](LICENSE) © 2026 junjunup
