# Agent 自动化进化实验 (Auto-evoloop) 协作规范

本指南旨在为团队的 Agent 自动化调优、版本迭代与测评提供一个统一的工程底座。我们将代码托管平台视为**"配置即代码"**与**"实验数据库"**的结合体，采用**"Baseline 进化流 (Evolution Flow)"**来管理多版本、非严格并行的 Agent 实验。

> **本规范以概念为主、平台为辅**：分支模型、合并请求流程、AI 评审等核心概念以平台无关的方式陈述；具体平台命名（镜像平台 / 主开发平台）以括号或对照表给出例子。开发者可在任一平台跑流程。

---

## 0. 文档权威来源 (SoT) 规则

**核心规则：每条信息只在一个文件里完整存在，其他文件只能用 `> 见 X §Y` 引用，禁止复制粘贴。**

| 信息类别 | 权威来源 (SoT) | 其他文件处理方式 |
|---------|---------------|----------------|
| 四层术语 (Experiment/Round/Batch/FIX) | `core_skills/DESIGN.md §0` | 只写标题行 + 链接 |
| Framework-version 架构设计 | `core_skills/DESIGN.md §0.2` | CONTRIBUTING §3 保留"协作操作步骤"，不重复架构原理 |
| 目录结构图 (monorepo) | `CONTRIBUTING.md §1.2/§1.3` | 其他文件只引用 |
| 分支/commit/MR 流程 | `CONTRIBUTING.md §4–7` | AGENTS.md/<host_runtime_doc> 只保留 1–2 条禁止性约束 |
| Eval 命令完整 flag 表（按 framework 拆分） | `scripts/run_eval/<framework-id>/run_eval_guide.md`（当前：**`<framework-current>/`** 默认，`<framework-legacy>/` 已废弃） | <host_runtime_doc> 只保留最简示例 + 链接 |
| Runner 实现按 framework 归类 | `scripts/run_eval/<framework-id>/`（当前：**`<framework-current>/`** 默认；`<framework-legacy>/` [DEPRECATED] 仅过渡期回归对比，runner 入口已加 stderr warning） | 新增 framework runner 时同步更新 <host_runtime_doc> Directory Layout / Quick Start / Architecture Notes（PR template 已硬检查） |
| 评分/抽样 flag 表 | `scripts/score/score_guide.md` / `scripts/small_sample/extract_sample_guide.md` | 同上 |
| AI 护栏（禁止行为） | `AGENTS.md` | <host_runtime_doc> 不重复 |
| AI 运行时指令 | `<host_runtime_doc>` | 不在其他"人类读"文档里重复 |
| auto-* skill 在本仓库的 artifact 锚点（S1/S2/S3/S4 输出落在 `evoloop/experiments/` 何处） | `<host_runtime_doc> §"Skill artifact 锚点"` | `core_skills/*/SKILL.md` 描述输出契约时只引用，不在 skill 内硬编 host 布局；目录模板本身仍归 `CONTRIBUTING.md §1.3` |
| 当前运行状态/验证快照 | `docs/snapshots/YYYYMMDD_*.md` | 所有"活文档"禁止包含时态内容 |
| 历史过程稿（review notes / smoke guides / 一次性 validation 报告） | `docs/archive/` | 活文档禁止保留带日期后缀的过程稿；完成历史使命后归档 |
| P2/P3 backlog（暂不做但值得记一笔的事项；MR 评审 push back / `future direction` 段 / 实验踩坑均落于此） | `docs/backlog.md` | 各 SKILL/DESIGN 里的 "future direction" 段保留短语，但末尾必须 `> 详见 docs/backlog.md#<anchor>` 链接到 SoT；不复制叙述 |

### 0.1 过程稿生命周期

任何带以下特征的文档属于"过程稿"，**默认有时效**：

- 文件名带日期后缀（`*_YYYYMMDD.md`）
- 文件名含 `*_GUIDE.md`（一次性操作指南）、`*_review_notes_*.md`（一次性 review 记录）、`*_validation*.md`（一次性 validation 报告）
- 自述包含"试验完成后清理 / 当前不直接修改 / 仅作复盘参考"等限定语

**生命周期规则**：

1. 创建时直接落在 `docs/archive/`，或落在 skill / project 临时位置；本仓库**不接受**裸挂在 `core_skills/` 或 `scripts/` 根目录的过程稿
2. 对应任务（MR / skill 实装 / 冒烟）完成后，过程稿归 `docs/archive/`；30 天内未归档由维护者强制归档
3. 归档时保留原文件名 + 日期后缀；归档文件**只读**，不再更新

### 0.2 过程稿 vs 快照 vs 活文档

| 类型 | 位置 | 时效性 | 修改频率 |
|------|------|--------|---------|
| 活文档 | `CONTRIBUTING.md` / `DESIGN.md` / `SKILL.md` 等 | 长期有效 | 高（随设计演进） |
| 快照 | `docs/snapshots/YYYYMMDD_*.md` | 一次性快照 | 创建后不改 |
| 过程稿 | `docs/archive/` | 已完成历史使命 | 归档后不改 |

### 0.3 平台映射（概念 → 镜像平台 / 主开发平台 例子）

仓库同时托管在 GitHub 与 主开发平台，当前 主开发平台 为主开发，GitHub 为定期镜像。本规范在条文中使用**平台无关概念**；以下表格给出两个平台的具体映射，是查阅这些概念时的唯一对照表。

| 概念 | GitHub 例子 | 主开发平台 例子 |
|------|-------------|-------------|
| 仓库地址 | `<mirror-repo-url>` | `primary.aliyun.com/<primary-org-id>/<primary-repo-path>` |
| **主干分支 (trunk)** | `main` | `master` |
| **合并请求 (merge request)** | Pull Request (PR) | Merge Request (MR) |
| **AI 评审 bot** | <mirror-ai-review-bot> | <primary-ai-review-bot> |
| 评审规则的执行机制 | `.github/CODEOWNERS` 文件由平台自动执行 | 仓库设置 → 评审规则（web UI） |
| MR/PR 模板的执行机制 | `.github/PULL_REQUEST_TEMPLATE.md` 文件被平台自动加载 | 仓库设置 → 合并请求模板（web UI） |
| 默认 remote 别名（建议） | `origin` | `primary` |

**约束**：

- 文中提到「合并请求」「主干」「AI 评审 bot」「主开发平台」等术语时，按本表映射理解；不要在新增条文里硬编码 PR/MR/main/master 字面量。
- `.github/CODEOWNERS` 与 `.github/PULL_REQUEST_TEMPLATE.md` 是上述两类规则的**唯一 SoT**：GitHub 自动生效；主开发平台 需在 web UI 手工同步（流程见 §8.2）。
- AI 评审 bot 的平台特定行为（如「草稿单不触发评审」）集中在 §8.3，其他文档不重复声明。

---

## 1. 核心理念与架构

### 1.1 资产打包原则 (Atomic Commits)

在执行任何代码合并前，必须遵循**"基因与表现型绑定"**的原则：**Agent 的配置/Prompt 代码，必须与其对应的测评报告 (Eval Report) 作为同一个 Commit 提交**。确保代码库的每一个历史节点都具备"自解释性"和可追溯性。

### 1.1.1 Skill 内容熵增治理

修改 `core_skills/**/SKILL.md` 的 MR，作者须自检、reviewer 须按 [`core_skills/00_meta/entropy-control/CHECKLIST.md`](core_skills/00_meta/entropy-control/CHECKLIST.md) 复核。详见该文件，此处不重述。

### 1.2 单体仓库 (Monorepo) 目录架构

所有基建脚本、实验核心逻辑与业务 Agent 实例均在单一仓库中收敛：

```text
auto-evoloop-registry/
├── .github/                         # 平台 SoT：CODEOWNERS + MR/PR 模板（GitHub 自动生效；主开发平台 web UI 据此同步）
├── .primary/                         # 主开发平台 平台说明目录（README + 同步操作清单；不存独立 SoT）
├── CONTRIBUTING.md                   # 本文档
├── AGENTS.md                         # AI Agent 护栏指引
│
├── core_skills/                      # Auto-evoloop 自动化进化引擎核心
│   ├── DESIGN.md                     #   引擎架构设计文档
│   ├── CONTEXT.md                    #   开发者上下文文档
│   ├── 00_meta/                      # 元过程 skill（不属于 S1-S4 主链路）
│   │   ├── entropy-control/          # SKILL.md 内容熵增治理 checklist
│   │   │   └── trace warehouseECKLIST.md
│   │   └── meta-reflection/          # stage 出口元反思 (v1)
│   │       ├── SKILL.md
│   │       ├── stages/               # S1/S2/S3/S4 各自模块
│   │       └── references/
│   ├── 01_prepare/                   # 数据流准备与上下文构建
│   │   └── auto-trace-prep/          # 物料准备 (v1.2)
│   │       ├── SKILL.md
│   │       ├── references/
│   │       └── scripts/
│   ├── 02_analyze/                   # 瓶颈分析（多 skill）
│   │   ├── auto-single-case-analyzer/  # 单 case 深度归因 (v1.9.0)
│   │   │   ├── SKILL.md
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   │   └── viewer/
│   │   └── auto-case-summary/       # 汇总聚合 (v1.1, deprecated)
│   ├── 03_plan/                      # 优化策略生成
│   │   └── auto-fix-planner/        # 修复方案规划 (v2.1)
│   │       ├── SKILL.md
│   │       ├── references/
│   │       └── scripts/
│   └── 04_execute/                   # 方案执行与验证测评
│       └── auto-fix-executor/       # 渐进式修复执行 (v1.0)
│           ├── SKILL.md
│           └── references/
│
├── scripts/                          # 测评与评分工具链
│   ├── run_eval/
│   │   ├── <framework-current>/             # **默认 runner**（<framework-name> / agent-engine PyPI 框架；v2 单步调用 + replay_history）
│   │   └── <framework-legacy>/              # [DEPRECATED] <framework-name> 框架已废弃；过渡期保留供存量业务回归对比，runner 入口加 stderr warning
│   ├── score/                        # framework-agnostic 评分脚本
│   └── small_sample/                 # framework-agnostic 抽样脚本
│
└── projects/                         # 业务实验数据（agent 源码在 agent-source/agent-<biz>，不在本仓库）
    ├── biz_a/                        # 业务A
    │   ├── AGENT.md                  #   声明对应 agent-source 仓库 + 历史框架；对标 tag 使用时向人类确认
    │   ├── evals/                    #   原始测评数据集 + 历史报告
    │   └── evoloop/                  #   experiments + knowledge（业务级累积）
    │       ├── knowledge/
    │       │   └── lessons_learned.md
    │       └── experiments/
    │           └── exp_YYYYMMDD_<keyword>/
    ├── biz_b/                        # 业务B
    │   ├── AGENT.md                  #   → agent-source/agent-<biz_b>
    │   ├── evals/
    │   └── evoloop/
    └── biz_c/                      # 业务C
        ├── AGENT.md                  #   → agent-source/agent-<biz_c>
        ├── evals/
        └── evoloop/
```

> **Agent 源码外置**：v3.5 起业务 agent（biz_a / biz_b / biz_c）可部署代码迁出 monorepo，由 `agent-source/agent-<biz>` 独立维护。core 仓库只持有引擎（`core_skills/`）、工具链（`scripts/`）和实验数据（`projects/<biz>/evals/` + `evoloop/`）。具体仓库与对标 tag 见各业务的 `AGENT.md`。

### 1.3 业务项目标准目录模板 (Project Template)

新业务线接入时，分两步：

**Step 1**: 在 `agent-source/` 下新建独立仓库 `agent-<业务名>`，承载可部署 agent 代码（pyproject、bootstrap.yaml / main.py、`.space/` 或 `<业务名>/` 业务包等，按所选框架决定）。

**Step 2**: 在本仓库下初始化 `projects/<业务名>/`，仅承载实验数据：

```text
projects/<业务名>/
├── AGENT.md                        # 声明对应 agent-source 仓库地址、历史框架与对标 tag 约定
├── evals/                          # 原始测评数据集 + 历史报告
│   ├── input_<业务名>.csv
│   └── reports/
│       └── <YYYYMMDD>_<exp-id>.csv
└── evoloop/                        # Evoloop 产物（业务级累积，不再按 framework 分目录）
    ├── knowledge/                  #   跨 experiment 长期沉淀
    │   └── lessons_learned.md      #     维护者手工提炼
    └── experiments/                #   每个 experiment 一个子目录
        └── exp_YYYYMMDD_<keyword>/
            ├── goal.md                  #   目标、baseline、对标 agent-source tag、数据批次
            ├── analysis/                #   S1/S2 产物
            ├── rounds/                  #   S3/S4 产物，按 round 隔离
            │   └── round_N/
            │       ├── fix_plan.md
            │       ├── reviewer_findings.json
            │       ├── meta_reflection/         #   S3/S4 出口元反思
            │       │   ├── S3.md
            │       │   └── S4.md
            │       ├── execution/
            │       │   ├── diffs/
            │       │   ├── new_agent_files/     #   evoloop 变异产物（不是被评测的源码）
            │       │   ├── eval_results/
            │       │   ├── progressive_log.json
            │       │   └── execution_observations.jsonl
            │       └── optimization_report.md
            └── lessons_learned.md       #   本 experiment 教训（跨 round 累积）
```

> **关键约定**：
>
> - **agent 源码外置**：每个业务的可部署代码在独立仓库 `agent-source/agent-<biz>`，core 仓库不再持有；跑 eval 通过 `--agent-dir` 指向本机 clone（脚本 `scripts/setup/clone_agent_delivery.sh` 可一键拉取）
> - **对标 tag 使用时向人类确认**：AGENT.md 不锁定具体 tag，因为 evoloop 经常需要"当前生产 vs 实验产物"对比；跑实验前与维护者确认当前对标的 agent-source 分支/tag
> - **evals/ 业务级**：测评数据集和历史报告均归属业务，与所用 framework 无关
> - **evoloop/ 业务级**：v3.5 起取消 framework-version 目录层；如需对比不同框架版本，在 experiment 的 `goal.md` 中显式记录对标的 framework + agent-source commit
> - **runner 按框架分组**：`scripts/run_eval/<framework-id>/` 下的 runner 知道如何驱动该类型框架的 agent；framework-agnostic 的 `score.py` / `compare.py` / `extract_sample.py` 在 `scripts/score/` / `scripts/small_sample/` 共享
> - **agent 引擎依赖**：<framework-name> 框架的引擎通过私有 PyPI（<private-package-host>）发布；<framework-name> 框架的引擎暂内嵌于 agent-source 仓库

---

## 2. Experiment 目录与命名约定

### 2.1 术语定义

本仓库的 evoloop 系统采用四层术语（详见 `core_skills/DESIGN.md` §0）：

| 层 | 术语 | 语义 |
|----|------|------|
| L1 | Experiment | 一批 eval 数据 + 一个优化目标的完整优化周期 |
| L2 | Round | 一次 approved `fix_plan.md` 的 S4 执行尝试 |
| L3 | Batch | S4 内一组 FIX 的 apply+eval+D1/D2（SKILL.md 中仍称 "Iter"） |
| L4 | FIX | 单文件原子改动 |

> `loop` 只是 evoloop 的项目品牌名，不用于定义任何概念层级。

### 2.2 Experiment ID 命名规范

格式：`exp_YYYYMMDD_<keyword>`

- `YYYYMMDD`：experiment 启动日期
- `<keyword>`：目标关键词，小写 + 下划线，≤ 3 个词（如 `reduce_p0`、`speed_up_router`）

示例：`exp_20260420_reduce_p0`、`exp_20260505_memory_leak`

### 2.3 对内 ID vs 对外展示名

每个 experiment 有**两个名字**，一一对应但不共享字符串：

- **`experiment_id`**（对内 / 工程视角）：稳定、跨系统唯一，用于路径 / 日志 / 代码引用。格式 `exp_YYYYMMDD_<keyword>`。**一旦确定不可改**。
- **`display_name`**（对外 / 产品视角）：对团队或用户展示的名字，可本地化、可优化表达。**可变**。

`goal.md` 顶部 YAML frontmatter 必须同时包含两个字段：

```yaml
---
experiment_id: exp_20260420_reduce_p0
display_name: 业务A P0 问题降低专项
baseline_commit: <40-char git sha>
created_at: 2026-04-20
---
```

**使用约束**：

- 路径、目录名、日志、代码字段、commit message → 一律用 `experiment_id`
- 飞书文档标题、团队 Slack / 邮件、MR 描述、未来 UI → 一律用 `display_name`
- 禁止在 SKILL.md 指示用户看"某某 experiment（display_name）"——SKILL.md 里只提 `experiment_id`

> **为什么分两个字段**：当前是内部工具，未来可能走向产品化。产品化时用户界面展示 `display_name`，工程内部仍用 `experiment_id`。现在多一个字段的成本接近零，但为未来保留了演进空间。详见 `core_skills/DESIGN.md` §0.1 与 §11。

### 2.4 `exp/` 分支 vs Experiment（弱引用约定）

**两者是不同的载体**：

- `exp/` Git 分支是**代码协作载体**（rebase、冲突、拆 MR 会改变分支形态）
- Experiment 是**产品/评测/目标载体**（身份由 `experiments/<exp_id>/` 目录定义，不由分支定义）

**约束**：

1. Experiment 身份**由目录定义**，不由 Git 分支定义
2. 一个 experiment 可能跨多个 `exp/` 分支（如回流 S3 后重新起分支）
3. `goal.md` 中应记录 `baseline_commit` 和相关 `branches[]` 作为**弱引用**
4. 分支名与 experiment ID **不必**保持一致（但推荐：`exp/<biz>-<exp_keyword>-<date>`）

### 2.5 命名冲突面声明

`Experiment` 术语与仓库既有概念的冲突矩阵：

| 冲突面 | 是否冲突 | 缓解方式 |
|--------|---------|---------|
| Git `exp/` 分支 | 语义相近但边界不同 | 弱引用（见 §2.3） |
| Agent version（v2.x, v3.x） | 不冲突 | 两者正交，agent version 描述"当前代码态"，experiment 描述"优化过程" |
| Eval 数据批次 | 1:1 绑定 | 在 `goal.md` 中固定数据批次 |
| Baseline tag | 不冲突 | `goal.md` 记录 `baseline_commit` |
| 业务版本号 | 不冲突 | experiment 是优化流程，不是业务侧迭代 |
| 报告编号 | 不冲突 | report 从属于 round |

---

## 3. Framework-version 维度（标签化）

v3.5 起 `framework-version` 不再是 core 仓库下的目录层，而是 **experiment 的元数据标签**。业务 agent 代码统一放在 `agent-source/agent-<biz>` 仓库，不同框架版本通过 git tag / 分支区分。

### 3.1 ID 命名规范（仍沿用）

格式：`<framework-name>-<YY>M<M>`

- `<framework-name>`：框架名（小写，无空格）
- `<YY>M<M>`：年月版本（2026 年 3 月 = `26M3`）

示例：
- `<framework-legacy>`：<framework-name> 框架，2026 年 3 月版本
- `<framework-current>`：<framework-name> 框架，2026 年 4 月版本

每个 experiment 的 `goal.md` 必须记录当前对标的 `framework-id` 与 `agent-source` 的 commit/tag。

### 3.2 资产归属规则

| 资产 | 归属层 | 路径 |
|------|--------|------|
| 数据集 evals | 业务级 | `projects/<biz>/evals/` |
| 实验产物 evoloop | 业务级 | `projects/<biz>/evoloop/` |
| 业务代码（prompt / config / plugins） | **agent-source 仓库** | `agent-source/agent-<biz>`（独立仓库，git tag 锁版本） |
| Runner（run_eval） | 框架级 | `scripts/run_eval/<framework-id>/` |
| 评分 / 抽样 / 比较 | 仓库级（framework-agnostic） | `scripts/score/`、`scripts/small_sample/` |
| Agent 引擎 | **不在 monorepo** | <framework-name>: 私有 PyPI `agent-engine`；<framework-name>: 暂内嵌于 agent-source |

### 3.3 业务切换框架的路径

业务在 agent-source 仓库内从一个框架迁到另一个时：

1. 在 `agent-source/agent-<biz>` 开新分支，完成框架迁移与基础测试
2. 在 core 仓库的 `projects/<biz>/evoloop/experiments/exp_YYYYMMDD_<keyword>/` 启动新实验，`goal.md` 中记录新 framework-id + 对标 commit
3. 旧框架的实验在新框架基线稳定前继续保留 `evoloop/experiments/` 中的历史，作为对照
4. agent-source 切默认分支前与 core 维护者同步，更新各业务 `AGENT.md`

### 3.4 跨 framework 知识迁移

不自动同步。维护者从旧 framework 的相关 experiment / `lessons_learned.md` 手工提炼通用结论，写入新 framework 下对应 experiment 的 lessons_learned。

理由：很多教训是 framework 特定的（如 prompt 结构、tool 接口、orchestration 模式），盲目搬运可能在新框架下产生反效果。

---

## 4. 分支管理模型

本仓库不采用传统的 GitFlow，而是基于实验进化周期的 **Baseline 进化流**。

- **主干分支 (trunk)：** 永远代表各业务线**当前最优的 Baseline 版本**。禁止直接 Push（在主开发平台受分支保护规则约束）。
  - 主开发平台主干名见 §0.3 平台映射表（当前主开发：主开发平台 `master`；镜像：GitHub `main`，由维护者周期性同步）。
- **`exp/` 实验分支：** 所有的多维度探索、自动化优化流均在此类分支上独立进行。
  - **命名规范：** `exp/<业务名>-<优化方向>-<日期>`
  - **示例：** `exp/biz_a-multi-model-router-0409` 或 `exp/biz_c-prompt-compress-0410`

---

## 5. 标准进化操作流程 (Evoloop SOP)

### Step 1: 孵化实验基线 (Hatch)

启动新实验前，必须以当前最优基因（主开发平台主干分支）为起点进行分支孵化。

```bash
# 占位符：<trunk> = 主干分支名（GitHub: main；主开发平台: master）
#         <primary-remote> = 指向主开发平台的 remote 别名（GitHub-only: origin；双平台: 建议 primary + origin）
git checkout <trunk>
git pull <primary-remote> <trunk>
git checkout -b exp/biz_a-your-experiment-name
```

**双平台 remote 配置参考**（一次性）：

```bash
# 假设当前主开发是 主开发平台
git remote add primary https://primary.aliyun.com/<org>/<repo>.git
git remote add origin https://github.com/<org>/<repo>.git    # 仅作镜像，不主动 push 业务分支
git config branch.master.remote primary
git config branch.master.merge refs/heads/master
```

> 如果你的本地 remote 别名与上面不同（例如 `origin` 已指向 主开发平台），请在脑内做映射，不要照抄字面量。

### Step 2: 变异与交叉 (Mutate & Cross)

- **变异：** 运行 `core_skills` 下的引擎，生成针对当前业务 Agent 的改进代码与 Prompt。
- **交叉：** 若需参考其他并行实验的阶段性成果，使用 `git cherry-pick <commit-hash>` 将其优势代码合入当前分支。

### Step 3: 打包测评 (Eval & Bundle)

在实验结束并准备提交时，必须运行测评脚本。**默认走 <framework-current>**（<framework-legacy> 已废弃，仅过渡期回归对比）：

```bash
# 默认（<framework-current>，agent-engine 框架）—— 启动 agent-engine serve 后直接调 .py
python scripts/run_eval/<framework-current>/run_eval.py --url http://localhost:8088 -i <input.csv> -o <output.csv>

# [DEPRECATED] <framework-legacy>（仅过渡期回归对比；运行时会打 deprecation warning）
# bash scripts/run_eval/<framework-legacy>/run_eval.sh <agent项目目录> <API地址> <输入CSV> <输出CSV>
# powershell scripts/run_eval/<framework-legacy>/run_eval.ps1 <agent项目目录> <API地址> <输入CSV> <输出CSV>
```

> 详细参数说明：默认走 `scripts/run_eval/<framework-current>/run_eval_guide.md`；<framework-name> 历史用法见 `scripts/run_eval/<framework-legacy>/run_eval_guide.md`（过渡期保留）。

脚本执行完毕后，将**代码改动**与**测评结果**一并 `git add` 并提交至 `projects/<业务名>/evals/`。

### Step 4: 晋升跃迁 (Promote)

如果当前分支的测评指标**超越当前的 Baseline 阈值**，则在主开发平台发起指向主干的**合并请求**（GitHub: PR；主开发平台: MR；下文统称 MR/PR）。

- **状态要求：** 直接以 **ready for review** 状态创建——草稿状态不会触发 AI 评审 bot（详见 §8.3）。
- **MR/PR 模板：** 由平台自动加载/粘贴自 `.github/PULL_REQUEST_TEMPLATE.md`（见 §0.3）。
- **描述要求：**
  1. **变异内容：** 清晰描述改动逻辑（例如修改了 Analyze skill 的判定条件）。
  2. **核心指标：** 对比上一代，核心数据（准确率、幻觉率等）的变化幅度。
- **合并与里程碑：** Review 通过并 Merge 后，为新主干打上 Tag 标记进化节点（如 `biz_a-v1.3.0`）。
- **合并方式选择（核心权衡：SHA 稳定性 vs 主干线性历史，二者不可兼得）：**

  这两件事在分支落后时**互斥**——任何把 exp 分支顶到 trunk 顶端的操作要么改 SHA（rebase / squash），要么留 merge commit（merge into trunk）。先识别该 MR 当前最重要的属性，再选合并策略：

  | 情形 | 选择 | 取舍 |
  |------|------|------|
  | 分支天然可 fast-forward（`ahead≥1, behind=0`） | **Fast-forward only**（默认） | 同时拿到 SHA 稳定 + 主干线性，不用妥协 |
  | 分支 `behind>0`，且 commit SHA **未被** AI 评审 / 归档脚本 / 外部链接引用 | rebase exp 到主干顶 → ff-merge | 保线性历史，**主动接受 SHA 重写** |
  | 分支 `behind>0`，且 commit SHA **已被引用**（典型：开了 MR 已收到 <primary-ai-review-bot> / <mirror-ai-review-bot> 评审） | merge trunk into exp（生成 merge commit）→ 再 ff-merge | 保 SHA 稳定，主干历史**接受非线性**；评审引用全部可解析 |
  | 长期未跟主干 + 强冲突 | merge into trunk（生成 merge commit） | 主干非线性兜底；事后在 MR 描述里说明 |
  | 一次性脚本类改动，无 SHA 引用 | squash 可选 | 历史更紧凑；本仓库默认不用 |

  > **可执行规则（替代「rebase 前手动检查所有引用」）**：
  > - **MR 已开 + 已收到任意 AI 评审** → 默认走 *merge trunk into exp* 路径，不再 rebase。
  > - 仅在私有未推送或未开 MR 的分支上才 rebase。
  > - 如果坚持要 rebase 已被引用的分支，请新开分支推送，并在原 MR 关上前在描述里标注「已切到新分支，旧 SHA 引用失效」。

---

## 6. 并行冲突与"落后分支"处理策略

当某个实验分支成功合入主干成为新一代 Baseline（如 v2.0）时，其他正在基于 v1.0 进行的并行实验分支即成为"落后分支"。

- **策略 A：平滑变基 (Rebase) 继续实验**

  若你的实验方向独立（如你在做技能重构，别人优化了底层模型参数），请执行 Rebase，将你的实验平滑迁移至 v2.0 基线上：

  ```bash
  # 占位符：<primary-remote> = 主开发平台的 remote 别名；<trunk> = 主干分支名（见 §0.3）
  git fetch <primary-remote>
  git rebase <primary-remote>/<trunk>
  # 解决冲突后继续测评
  ```

- **策略 B：果断废弃 (Drop)**

  若你的实验方向与新 Baseline 严重重合或发生方向性冲突，且你的中期测评指标不如新 Baseline，请直接废弃该分支，重新基于新 Baseline 开启下一轮循环，避免无效内耗。

---

## 7. Commit 提交规范

遵循约定式提交（Conventional Commits），并在头部增加针对 Agent 体系的专属前缀：

| 前缀 | 用途 |
|------|------|
| `prompt:` | 针对提示词、System Instruction 的文本调优 |
| `skill:` | 针对 core_skills 核心流程或工具函数的代码调整 |
| `eval:` | 测评脚本修改，或新测评报告集的打包提交 |
| `config:` | 模型切换、调度策略（Roundtable）、超参数等配置文件调整 |
| `docs:` | 项目文档、进化报告等更新 |

**示例：**

```text
prompt: biz_a 优化了行程推荐环节的 Few-shot 数据
eval: biz_c 准确率提升至 91% (Baseline: 85%) | 打包分析报告
```

---

## 8. 治理目录维护与 AI 评审

本章是 §0.3 平台映射的执行细则。**仓库内只有一份 SoT，跨平台同步靠 web UI 手工配置**——本章定义谁、什么时候、做哪些动作。

### 8.1 治理目录的角色

```text
.github/                              # 平台 SoT（GitHub 自动执行 + 主开发平台 同步参考）
├── CODEOWNERS                        # 路径 → 评审人映射
└── PULL_REQUEST_TEMPLATE.md          # MR/PR 描述模板

.primary/                              # 主开发平台 平台说明目录（无独立 SoT）
└── README.md                         # 双平台映射 + 主开发平台 web UI 同步操作清单
```

> **为什么 SoT 集中放在 `.github/`**：GitHub 把这些路径作为**自动执行入口**；主开发平台 把同类规则放在 web UI。把唯一 SoT 放在自动执行的一侧，能让 GitHub 镜像直接生效，又不与 主开发平台 的 UI 配置冲突——主开发平台 一侧是「读 SoT → UI 同步」的单向流。

### 8.2 改动 SoT 时的同步流程

修改 `.github/CODEOWNERS` 或 `.github/PULL_REQUEST_TEMPLATE.md` 时：

1. **改文件**：在 MR/PR 中提交对应改动。
2. **同步 主开发平台 web UI**：仓库设置 → 评审规则 / 合并请求模板，按文件内容更新。
3. **MR/PR 描述自查**：在「治理目录同步自查」复选框中确认 UI 已同步，避免 SoT 漂移。

> **配置漂移的当前姿态与未来工作（参考 <primary-ai-review-bot> v1 #1 / v2 #1 评审意见）**：
> - **当前**：CODEOWNERS 只有一个 owner、几乎不变；MR 模板 checkbox 即可覆盖 SoT 漂移检查，过度自动化是 over-engineering。
> - **触发自动化的阈值**：当 owners ≥ 3 人，或 CODEOWNERS 月均改动 ≥ 1 次时，再考虑下列任一方案：
>   1. CI 步骤：`.github/CODEOWNERS` 改动时 fail-loud 提醒维护者「需同步 主开发平台 web UI」。
>   2. 定期审计脚本：解析 `.github/CODEOWNERS` + 调 主开发平台 OpenAPI 拉评审规则，diff 报警。
>   3. Pre-commit hook：本地 hash 校验 `.github/CODEOWNERS` 与上次同步快照。
> - 上述三选一即可，不必同时上。

### 8.3 AI 评审 bot 的平台特定行为

> 本节是 AI 评审相关说明的**唯一权威**——`AGENTS.md` / `<host_runtime_doc>` / MR 模板等其他文档只引用本节，不重复声明，避免平台变化时多处更新失同步（<primary-ai-review-bot> 评审意见 #4）。

| 概念 | GitHub | 主开发平台 |
|------|--------|--------|
| Bot 名 | <mirror-ai-review-bot> | <primary-ai-review-bot> |
| 触发条件 | PR 状态切到 ready for review（非 draft） | MR 状态切到 ready for review（非 draft） |
| 触发时机 | 创建/更新 PR 时自动 | 创建/更新 MR 时自动 |
| 主动触发方式 | 在 PR 评论里 `<mirror-ai-review-bot> review` | 在 主开发平台 MR 详情页手动点 AI 评审按钮 |
| 评审产物 | PR 评论 + inline 评论 | MR 全局评论 + inline 评论 |

**作者侧规则（核心，所有 AI 都按此协作）**：

- 创建 MR/PR 时直接用 ready for review 状态，不建草稿单——草稿单不会触发 bot 评审。
- bot 评审给出"代码实现建议 / 架构设计建议"两类。架构建议常涉及跨文件，作者要做"采纳 / 推回 / 已规划"判断而非全盘照办。
- **收到任意 AI 评审之后**，该 MR 分支默认进入「保 SHA 模式」——后续要跟主干同步走 *merge trunk into exp*，不再 rebase。完整合并策略表见 §5 Step 4。

### 8.4 治理目录改动的提交习惯

- 治理目录改动用 `docs:` 前缀，独立 commit，便于回溯。
- 跨多平台的治理变更（例如新增一类评审规则），在 commit 描述里说明：「**SoT**：改了哪些文件；**UI 同步**：在哪些平台 web UI 同步了什么」。
