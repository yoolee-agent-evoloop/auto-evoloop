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

## How It Differs From Runtime Self-Evolution

Auto-evoloop is complementary to systems such as OpenClaw-style self-evolving
skills and Hermes Agent Self-Evolution, but it optimizes a different layer.

OpenClaw is an agent runtime: its skill system extends what a live assistant can
do, and self-evolution plugins can learn from runtime feedback by writing
reusable episodic memory. Hermes is also positioned as a self-improving agent;
its self-evolution tooling uses DSPy/GEPA to mutate skills, tool descriptions,
system prompts, and code, then evaluate candidate variants.

Auto-evoloop is not a live agent runtime and does not let an agent rewrite its
own behavior directly from online experience. It is a development-time
optimization harness:

- **Sample scope**: runtime self-evolution learns from local online episodes;
  Auto-evoloop optimizes against an eval suite and badcase set.
- **Learning target**: runtime systems usually update memory, skills, prompts,
  or tool descriptions inside the agent harness; Auto-evoloop produces reviewed
  fixes to agent behavior, prompts, code, scoring rules, or evaluation setup.
- **Reasoning unit**: runtime learning often stores "what worked here";
  Auto-evoloop asks "why did this class of cases fail?" before planning a fix.
- **Decision boundary**: runtime self-evolution can be automatic; Auto-evoloop
  keeps policy-changing steps behind artifacts, diffs, eval comparison, and
  human-in-the-loop gates.
- **Generalization strategy**: online task samples are useful but narrow; an
  eval suite gives a broader view of whether a change improves global policy or
  merely overfits one session.

In short: OpenClaw/Hermes-style systems help an agent improve while it is
running. Auto-evoloop helps engineers decide what should become the next
reviewed baseline before that behavior is shipped back into a runtime agent.

Reference points for this comparison: [OpenClaw](https://github.com/openclaw/openclaw),
[OpenClaw skills](https://openclawdoc.com/docs/skills/overview/),
[OpenClaw self-evolve plugin](https://github.com/longmans/self-evolve),
[Hermes Agent](https://hermes-agent.nousresearch.com/docs/), and
[Hermes Agent Self-Evolution](https://github.com/NousResearch/hermes-agent-self-evolution).

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

## 与运行时自进化的区别

Auto-evoloop 和 OpenClaw 式自进化技能、Hermes Agent Self-Evolution 是互补关系，
但优化的是不同层。

OpenClaw 更像一个 Agent runtime：skill 系统扩展在线助手能做什么，自进化插件可以从
运行时反馈中学习，把经验写成可复用的 episodic memory。Hermes 也把自己定位为
self-improving agent；它的 self-evolution 工具使用 DSPy/GEPA 去变异 skills、tool
descriptions、system prompts 和 code，再评估候选版本。

Auto-evoloop 不是在线 Agent runtime，也不让 Agent 直接基于线上经验改写自己的行为。
它是开发/离线阶段的优化 harness：

- **样本视角**：运行时自进化主要从局部在线任务学习；Auto-evoloop 面向 eval suite
  和 badcase 集合优化。
- **学习对象**：运行时系统常更新 memory、skills、prompts 或工具描述；Auto-evoloop
  产出经过 review 的行为、prompt、代码、评分规则或评测配置修复。
- **推理单元**：运行时学习更容易沉淀“这次什么有效”；Auto-evoloop 先追问“一类 case
  为什么失败”，再规划修复。
- **决策边界**：运行时自进化可以自动发生；Auto-evoloop 把会改变 policy 的步骤放在
  artifact、diff、eval 对比和 human-in-the-loop gate 后面。
- **泛化策略**：线上小样本有价值但视野窄；eval suite 能更好判断一个改动是在提升全局
  policy，还是只过拟合了某个 session。

一句话：OpenClaw/Hermes 式系统帮助 Agent 在运行中变强；Auto-evoloop 帮工程团队判断
哪些变化应该成为下一版可审计 baseline，再回流到运行时 Agent。

本段对比参考：[OpenClaw](https://github.com/openclaw/openclaw)、
[OpenClaw skills](https://openclawdoc.com/docs/skills/overview/)、
[OpenClaw self-evolve plugin](https://github.com/longmans/self-evolve)、
[Hermes Agent](https://hermes-agent.nousresearch.com/docs/) 和
[Hermes Agent Self-Evolution](https://github.com/NousResearch/hermes-agent-self-evolution)。

核心方法论见 [core_skills/DESIGN.md](core_skills/DESIGN.md)，公开实现上下文见
[core_skills/CONTEXT.md](core_skills/CONTEXT.md)。

## 当前 alpha 能力边界

当前已经可用：离线合成 demo、CSV 抽样、本地规则评分、baseline/candidate 对比、trace key 脱敏 helper、S1-S4 方法论契约。

后续 alpha 才会补齐：生产 runner adapter、trace backend 集成、LLM scoring、自动 planner/executor 编排。

## 公开边界

本仓只包含公开安全的源码、合成样例和脱敏后的方法论文档。不要提交真实用户数据、业务 trace、`.env`、token、内部仓库地址、私有包源、部署细节或任何闭源仓历史。
