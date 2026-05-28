# Auto-evoloop

Auto-evoloop is an open-source framework for evaluating AI agents, analyzing
failures, planning targeted fixes, and validating improvements through iterative
experiments.

This is a `v0.1-alpha` project. It is useful for learning, demos, and lightweight
local workflows, but it is not a production agent platform. Internal evaluation
data, customer conversations, traces, credentials, proprietary prompts, private
deployment code, and private repository history are intentionally excluded.

## Quickstart

```bash
git clone https://github.com/yoolee-agent-evoloop/auto-evoloop.git
cd auto-evoloop
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
evoloop demo run
```

The demo is fully offline and writes synthetic outputs to
`/tmp/auto-evoloop-demo/` by default.

## Current Alpha Capabilities

Available now:

- offline synthetic demo,
- CSV sample extraction,
- local rule-based scoring,
- baseline/candidate comparison,
- trace key redaction helper,
- public S1-S4 methodology and skill contracts.

Reserved for later alphas:

- production runner adapters,
- trace backend integrations,
- LLM scoring,
- automated planner/executor orchestration.

## CLI

```bash
evoloop --help
evoloop demo run
evoloop sample extract --input examples/synthetic_demo/input.csv --output /tmp/sample.csv --sessions 1,2
evoloop score --input /tmp/auto-evoloop-demo/demo_output.csv --output /tmp/demo_scores.csv --scorer local
evoloop compare --baseline /tmp/auto-evoloop-demo/demo_baseline_scores.csv --candidate /tmp/auto-evoloop-demo/demo_scores.csv --output /tmp/demo_compare.md
evoloop trace clean --input examples/synthetic_demo/synthetic_trace.json --output /tmp/synthetic_trace.clean.json
```

## What It Is For

Auto-evoloop helps teams structure iterative agent improvement work:

- freeze evaluation inputs,
- run an agent or deterministic demo runner,
- collect outputs and traces,
- analyze failures case by case,
- plan focused fixes,
- validate candidate changes against a baseline,
- record evidence for human review.

The public methodology is documented in:

- [docs/quickstart.md](docs/quickstart.md) for setup and expected demo outputs,
- [core_skills/DESIGN.md](core_skills/DESIGN.md) for workflow design,
- [core_skills/CONTEXT.md](core_skills/CONTEXT.md) for public implementation context,
- [docs/concepts.md](docs/concepts.md) for glossary and artifact terms,
- [docs/architecture.md](docs/architecture.md) for package and workflow mapping,
- [docs/sanitization-policy.md](docs/sanitization-policy.md) for public boundary rules.

## Public Boundary

This repository contains only public-safe source code, synthetic examples, and
sanitized methodology docs.

Do not commit:

- real customer or user conversations,
- health, financial, contract, payment, or support records,
- private trace exports, logs, screenshots, or case reports,
- `.env` files, credentials, cookies, tokens, keys, or sessions,
- internal endpoints, private repositories, private package indexes, or
  deployment details.

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Security

Please do not open public issues for suspected leaks or vulnerabilities. See
[SECURITY.md](SECURITY.md).

---

# Auto-evoloop 中文说明

Auto-evoloop 是一个用于 AI Agent 评测、失败归因、修复规划和迭代验证的开源框架。

当前仓库是 `v0.1-alpha` 阶段：适合学习、演示和轻量本地流程，不代表生产级 Agent 平台。真实业务评测数据、客户对话、trace、凭据、私有 prompt、私有部署代码和闭源仓历史都不会进入这个公开仓库。

## 快速开始

```bash
git clone https://github.com/yoolee-agent-evoloop/auto-evoloop.git
cd auto-evoloop
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
evoloop demo run
```

离线 demo 只使用合成数据，默认输出到 `/tmp/auto-evoloop-demo/`。

## 它解决什么问题

Auto-evoloop 帮团队把 Agent 优化过程结构化：

- 固化评测输入；
- 运行 Agent 或确定性 demo runner；
- 收集输出和 trace；
- 逐 case 分析失败原因；
- 生成聚焦的修复方案；
- 用 baseline/candidate 对比验证效果；
- 留下可供人类 review 的证据。

核心方法论见 [core_skills/DESIGN.md](core_skills/DESIGN.md)，公开实现上下文见
[core_skills/CONTEXT.md](core_skills/CONTEXT.md)。

## 当前 alpha 能力边界

当前已经可用：离线合成 demo、CSV 抽样、本地规则评分、baseline/candidate 对比、trace key 脱敏 helper、S1-S4 方法论契约。

后续 alpha 才会补齐：生产 runner adapter、trace backend 集成、LLM scoring、自动 planner/executor 编排。

## 公开边界

本仓只包含公开安全的源码、合成样例和脱敏后的方法论文档。不要提交真实用户数据、业务 trace、`.env`、token、内部仓库地址、私有包源、部署细节或任何闭源仓历史。
