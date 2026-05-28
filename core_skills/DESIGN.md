# auto-agent-evoloop 设计方案

> **版本**：v3.4（2026-04-27 更新）
> **变更**：v3.4 — 引入 `framework-version` 层（业务项目按框架版本分组：`projects/<biz>/framework-version/<framework-id>/`），run_eval 按 framework 分组，evoloop 数据 framework-version 级隔离。v3.3 — 新增 §0 术语表（Experiment/Round/Batch/FIX 四层），明确 Round 边界（一个 approved plan = 一个 round），引入 `experiments/` 目录层级，`loop` 仅作品牌名保留。v3.2 — S4 执行工作区定义（git branch）、Decision Inputs 小节、幂等性定义收窄、tolerance 规则细化、删除 fuse_judge.py（路径 A 不需要）。v3.1 — 统一 Skill 2 命名为 `auto-single-case-analyzer`；合并 `scoring_error` 至 `reject`；Skill 3 显式继承 `repair-principles-v1.6.0.md` 和 `attribution-framework.md` v4；每个 FIX 新增 `fix_strategy` 字段；目录结构对齐 monorepo 二级结构。
>
> **适用范围**：本文档是将单体 `trace-badcase-analyzer` 扩展为 `auto-agent-evoloop`（Agent 自动进化闭环）的**结构性设计方案**。文中涉及的具体分析逻辑、报告模板、修复方案格式等仅作为结构说明的参考示例，**以实际 skill 的内容为准**。

---

## 0. 术语表

evoloop 系统的核心概念分为四层：

| 层级 | 英文 | 中文 | 定义 | 目录位置 |
|------|------|------|------|---------|
| L1 | **Experiment** | 实验 | 围绕一批 eval 数据 + 一个优化目标的完整优化周期。由 S1→S2→S3→S4 构成，允许多个 round 尝试 | `projects/<biz>/evoloop/experiments/<exp_id>/` |
| L2 | **Round** | 轮次 | 一次 approved `fix_plan.md` 的 S4 执行尝试。若需回流 S3 重新 planning → 启动新 round（round_{N+1}），**不在同一 round 内循环** | `experiments/<exp_id>/rounds/round_N/` |
| L3 | **Batch** | 批次 | S4 内一组 FIX 的 apply + eval + D1/D2 单元（当前 SKILL.md 中仍称为 "Iteration"/"Iter"，语义等同） | `progressive_log.json[iterations]` 数组元素 |
| L4 | **FIX** | 修复项 | 单个文件级的原子改动 | `fix_plan.md` 中的 `FIX_NNN` |

**关键约定**：

- **"loop" 不作为概念术语**：`evoloop` 是项目品牌名，**不**定义任何概念层级。所有精确术语使用上表四个词。
- **层级由输入输出+决策点定义**，与持续时间无关（一个 experiment 可能是一天也可能一季度，不由时间决定层级归属）。
- **Round 边界规则**：一个 round = 一个 approved plan + 一次 S4 执行 + 一份 optimization_report。S4→S3 回流产生新 round。
- **术语迁移状态**：目录路径已采用新结构（`experiments/<id>/rounds/round_N/`）。SKILL.md 内部文本中的 "Iteration"/"Iter"/"iter_N" 语义等同于 Batch，将在后续 PR 中完成重命名。

### 0.1 对内术语 vs 对外术语

上表四个词（Experiment / Round / Batch / FIX）是**对内·工程视角**术语，用于：

- 仓库目录命名
- SKILL.md / 代码 / 日志 / progressive_log.json
- 开发者与维护者日常交流

当系统走向产品化（多租户 Web UI / Agent IDE / SaaS）时，会在此之上套一层**对外·产品视角**术语（如"优化任务 / 版本 / 变更 / 修复项"）。两套术语一一对应但**不共享字符串**，互相之间通过 artifact 字段映射。

**当前阶段的具体 ask**：每个 experiment 同时持有两个名字，artifact 顶部预留映射字段。

| 字段 | 用途 | 稳定性 | 示例 |
|------|------|--------|------|
| `experiment_id` | 对内 ID：路径 / 日志 / 代码引用 | 不可变 | `exp_20260420_reduce_p0` |
| `display_name` | 对外名：可本地化、可优化表达 | 可变 | `业务A P0 问题降低专项` |

**原则**：

- 任何出现在用户界面（未来）或跨团队沟通（现在）的位置，使用 `display_name`
- 任何出现在路径、代码、日志、API 字段的位置，使用 `experiment_id`
- DESIGN.md / CONTRIBUTING.md 里的术语是**工程术语**，不应写进任何 UI 面向文本

> 为什么现在就分两个字段：多一个 YAML 字段成本接近零，但避免了未来产品化时的大规模重命名。详细演进路径见 §11。

### 0.2 Framework-version 维度

业务项目（biz_a / biz_b / biz_c）可能并行使用**不同的框架版本**。多框架并存通过 `framework-version` 目录层管理：

```
projects/<biz>/
├── evals/                                  # 业务级共享数据
└── framework-version/
    ├── <framework-legacy>/                         # 旧框架（biz_a 当前实现）
    │   ├── .space/ + app/ + main.py
    │   └── evoloop/                        # 本 framework-version 内的 experiments + knowledge
    └── <framework-current>/                        # 新框架（agent-engine PyPI 包架构）
        ├── pyproject.toml + bootstrap.yaml + Dockerfile
        ├── <biz>/                          # app.yaml + llm.yaml + prompts/ + skills/ + plugins/
        └── evoloop/
```

**核心约定**：

| 资产 | 归属层级 | 理由 |
|------|---------|------|
| `evals/`（数据集） | 业务级（`projects/<biz>/evals/`） | ground truth 是业务事实，跨 framework-version 共享。若不同 framework 需要不同输入格式，用文件命名区分（`input_biz_a.csv` vs `input_biz_a_<framework-name>.csv`） |
| `evoloop/`（实验产物） | framework-version 级 | 不同 framework 的优化路径、教训、决策都不可比，强制隔离 |
| `run_eval/`（runner） | framework-version 级（`scripts/run_eval/<framework-id>/`） | 不同 framework 的 API 形态不同（<framework-name> 用 legacy message transport，<framework-name> 用 agent-engine SDK） |
| `score.py` / `compare.py` / `extract_sample.py` | 仓库级（framework-agnostic） | 只看 CSV 字段，与 framework 无关 |
| Agent 引擎（`agent-engine`） | **不在 monorepo** | <framework-name> 框架引擎通过私有 PyPI（<private-package-host>）发布；项目通过 `pyproject.toml` 依赖。<framework-name> 框架引擎当前内嵌在业务代码中，未来抽离 |

**Framework-version ID 命名**：`<framework-name>-<YY>M<M>`，如 `<framework-legacy>`（<framework-name> 框架，2026 年 3 月版本）、`<framework-current>`（<framework-name> 框架，2026 年 4 月版本）。

**跨 framework-version 的教训迁移**：维护者手工从旧 framework 的 `evoloop/knowledge/lessons_learned.md` 提炼通用结论，复制到新 framework 的对应文件，**不自动同步**。原因：很多教训是 framework 特定的（如"profile_extraction_module skill 的 Few-shot 问题"），不能盲目带过去。

**业务迁移路径**：业务从 <framework-name> 迁到 <framework-name> 时，新建 `framework-version/<framework-current>/`（参考 `projects/biz_b/framework-version/<framework-current>/` 结构），旧目录保留至迁移测评通过后归档。

---

## 1. 设计目标

将单体 `trace-badcase-analyzer` 扩展为 **auto-agent-evoloop**——由 4 个幂等 skill 组成的 Agent 自动进化闭环，覆盖从 badcase 归因到自动修复验证的完整链路：

1. **通用能力复用**：物料准备、单 case 归因、修复方案制定、修复执行各自独立，可被不同流程组合调用
2. **幂等性**：每个 skill 的输入完全由文件（artifact）承载，不依赖对话上下文；同一输入重跑产出一致的结果
3. **最小化 HITL & 节点归并**：HITL 不作为独立流程节点，而是归并到所属 skill 内部作为最后一步；每个 HITL 仅产出一个确认后的 artifact 作为下游前置条件，减少人工介入频次
4. **多路径 / 渐进式调优探索**：executor 内部支持最小改进→复杂改进的渐进式 Level 升级（含三级熔断），闭环支持多条回流路径（版本向前 / 调整方案 / 重新分析），形成持续迭代的进化循环

### 幂等性定义

- **结构幂等**：给定相同的文件输入和参数，产出的 artifact 结构、执行顺序和决策逻辑一致。具体文本表达和 eval 数值受 LLM 和运行环境影响，不保证字面一致
- **无隐式会话依赖**：所有输入通过文件路径或显式参数传入
- **可安全重跑**：重跑 skill 直接覆盖输出 artifact

> **注意**：S4 (auto-fix-executor) 的执行链路包含 agent 推理、LLM 评分、agent server 响应等不确定性来源。"可安全重跑"意味着重跑不会损坏状态（幂等），但不保证产出完全一致的 eval 分数或 D1/D2 决策。精确复现需冻结运行上下文（见 §3.4 run_metadata）。

### 4 个 Skill 总览

| Skill | 职责 | 核心输入 | 核心产出 |
|---|---|---|---|
| `auto-trace-prep` | 物料准备：加载评测集、获取 Harness、抓取 trace | ①Agent 文件 + ②Eval 结果 | `analysis_manifest.json` (confirmed) |
| `auto-single-case-analyzer` | 单 case 归因 + 结构化反馈收集 | manifest + traces + Harness.md | `case_report.md` + `feedback.json` |
| `auto-fix-planner` | 修复方案制定 + 分流 + 跨模型 review | feedback + 归因报告 + **Agent 源码** | `fix_plan.md` (approved) |
| `auto-fix-executor` | 渐进式执行修复 + 验证测评 + 效果总结 | fix_plan + **Agent 源码** (fork) | 新版 Agent 文件 + optimization_report.md |

> **元过程 Skill**：`core_skills/00_meta/` 存放 cross-cutting 元过程 skill，不属于 S1-S4 主进化链路，但可在主链路任一 stage 出口触发。当前已实装：`meta-reflection`（stage 出口元反思）。详见 [`core_skills/00_meta/meta-reflection/SKILL.md`](00_meta/meta-reflection/SKILL.md)。

---

## 2. 整体架构

```
Evaluation 测评
  ①Agent 文件 → 评估器 + 评测集 → ②Eval 结果
    │                                   │
    │  ┌────────────────────────────────┘
    ▼  ▼
┌─────────────────────────────────────────────────────────────┐
│  Skill 1: auto-trace-prep                                   │
│  输入: ①Agent 文件  ②Eval 结果                               │
│                                                             │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐  │
│  │ eval-data-     │ │ harness-       │ │ trace-         │  │
│  │ loading        │ │ loading        │ │ fetching       │  │
│  └───────┬────────┘ └───────┬────────┘ └───────┬────────┘  │
│          ▼                  ▼                   ▼           │
│    schema.json        Harness.md          traces/*.json     │
│          └──────────────────┼───────────────────┘           │
│                             ▼                               │
│             analysis_manifest.json (draft)                  │
│                             │                               │
│  ╔══════════════════════════╧════════════════════════════╗  │
│  ║  HITL: 信息澄清 + 分析范围标注                         ║  │
│  ║  确认 schema、标注 selected / analysis_mode            ║  │
│  ╚══════════════════════════╤════════════════════════════╝  │
│                             ▼                               │
│             analysis_manifest.json (confirmed)              │
└─────────────────────────────┬───────────────────────────────┘
                              │
             ┌────────────────┴────────────────┐
             ▼ artifact 前置条件                ▼
   analysis_manifest.json            Harness.md
   (confirmed, selected=true)        traces/*.json
             │                                 │
             └────────────────┬────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Skill 2: auto-single-case-analyzer  (× n, 自动并行/串行)       │
│                                                             │
│  ┌─────────────────────┐  ┌────────────────────────┐       │
│  │ mode A: 直接归因    │  │ mode B: 对比归因       │       │
│  │ 1 trace → 归因报告  │  │ 2 traces → 差异根因    │       │
│  └──────────┬──────────┘  └───────────┬────────────┘       │
│             ▼                         ▼                     │
│      case_report.md           case_report.md                │
│      case_summary.json        case_summary.json             │
│                         │                                   │
│         自动生成 feedback_viewer.html                        │
│                         │                                   │
│  ╔══════════════════════╧════════════════════════════════╗  │
│  ║  HITL: 结构化反馈 (可跳过 → status: incomplete)        ║  │
│  ║  ┌──────┐ ┌──────────┐ ┌──────┐ ┌──────┐            ║  │
│  ║  │ 采纳 │ │修改后采纳│ │ 归并 │ │ 拒绝 │            ║  │
│  ║  └──────┘ └──────────┘ └──────┘ └──────┘            ║  │
│  ╚══════════════════════╤════════════════════════════════╝  │
│                         ▼                                   │
│                  feedback.json                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
             ┌────────────┴────────────┐
             ▼ artifact 前置条件        ▼
    feedback.json              case_summary/report_*.json/md
    (status: complete)         Agent 文件 (源码)
             │                         │
             └────────────┬────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Skill 3: auto-fix-planner                                  │
│                                                             │
│  综合阅读: feedback + 归因报告(含渐进路径) + Agent 源码       │
│  → 提取全局约束 + 交叉对照 + 聚合根因 → 方案制定              │
│                         │                                   │
│        ┌────────────────┼────────────────┐                  │
│        ▼                                 ▼                  │
│  自动优化 Iteration 批次          转人工工单项                │
│  (低风险→高风险排序,              (需人工处理)               │
│   含 depends_on)                                            │
│        └────────────────┬────────────────┘                  │
│                         ▼                                   │
│  ┌─────────────────────────────────────┐                    │
│  │ Reviewer（需人工授权）              │                    │
│  │ 独立 review fix_plan 的合理性       │                    │
│  └──────────────────┬──────────────────┘                    │
│                     ▼                                       │
│               fix_plan.md (draft)                           │
│                     │                                       │
│  ╔══════════════════╧════════════════════════════════════╗  │
│  ║  HITL: 方案 review (文档评论方式)                       ║  │
│  ║  优化方案: 直接通过 / 文档评论修改建议                    ║  │
│  ╚══════════════════╤════════════════════════════════════╝  │
│                     ▼                                       │
│               fix_plan.md (approved)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
             ┌────────┴────────┐
             ▼ artifact 前置条件
    fix_plan.md (approved)
    Agent 文件 (当前版本源码, fork 基础)
    原始 Eval 结果 (效果对比)
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Skill 4: auto-fix-executor                                 │
│                                                             │
│  源码理解 + Fork Agent 文件                                  │
│  细化各 Iteration 实现层 (意图层不可变)                       │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────┐            │
│  │ 渐进式执行循环 (for each Iteration)          │            │
│  │                                              │            │
│  │  依赖检查 → 应用 Iter N → 小样本 eval        │            │
│  │  → 微调窗口 (实现层微调)                      │            │
│  │                                              │            │
│  │  D1: COMMIT / ROLLBACK (当前 Iter)           │            │
│  │    非预期退化 > tolerance → ROLLBACK          │            │
│  │    核心 Iter + target 无改善 → ROLLBACK       │            │
│  │    其他 → COMMIT                              │            │
│  │                                              │            │
│  │  D2: CONTINUE / EXIT (下一步)                │            │
│  │    COMMIT + 有更多 Iter + target 未全修好     │            │
│  │      → CONTINUE                              │            │
│  │    COMMIT + 无更多 Iter 或 target 全修好      │            │
│  │      → EXIT                                  │            │
│  │    ROLLBACK + 后续 Iter 不依赖当前            │            │
│  │      → CONTINUE (skip)                       │            │
│  │    ROLLBACK + 无可继续 Iter → EXIT           │            │
│  └──────────────────────┬──────────────────────┘            │
│                         ▼                                   │
│              新版 Agent 文件 (最后 COMMIT 的稳定快照)         │
│                         │                                   │
│              全样本 Eval → 新版 Eval 结果                     │
│                         │                                   │
│              原始 Eval vs 新版 Eval                           │
│              → optimization_report.md (9 维度)               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ optimization_report   │
              │ + 新版 Agent 文件      │
              └───────────┬───────────┘
                          │ 人工读 report 后决策 (§6)
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
    提升+无副作用     提升+退化         未提升
         │                │                │
         ▼                ▼                ▼
    merge 生效       回流 S3           三选一:
    (可选)新一轮     auto-fix-         ①回流 S1/S2
    → S1             planner           ②回流 S3
                                       ③人工介入
```

---

## 3. Skill 详细设计

### 3.1 Skill 1: `auto-trace-prep`

**职责**：物料准备——加载评测数据、获取 Agent Harness、抓取并标准化 trace 文件。

**触发词**：准备 trace 分析、加载评测数据和 trace、拉取 trace、我要分析 badcase

#### 输入

| 物料 | 必选 | 说明 |
|------|:----:|------|
| **①Agent 文件** | ✅ | Agent 源码（prompt / tool / 编排代码）或 Agent 版本 ID（用于自动获取） |
| **②Eval 结果** | ✅（二选一） | (1) **已有 scored Excel/CSV**（含评分、thread_id 等）；或 (2) **测评集输入 CSV**（含 `user_query` / `dialog_history` 等输入列，无 `actual_output` 与评分）+ 已就绪的 Agent 服务/版本 → 由 1a-bis 调用 `scripts/run_eval/<framework>/` + `scripts/score/` 自跑产出 scored CSV（v1.3+） |
| Trace 数据 | 二选一 | (A) thread_id 列表（直接调用拉取脚本）（B) 从 Eval 结果 Excel 中提取 thread_id（仍走 A 的拉取流程）。**v1.3 起不再支持"用户直接提供 trace JSON 文件"路径**——下游 viewer / analyzer 已不再保留 raw 命名兼容性，统一走脚本拉取保证清洗格式一致 |

#### 子能力

> 以下子能力的具体实现逻辑以实际 skill v5 为准。

**eval-data-loading**：读取 Eval 结果 Excel/CSV，自动识别列类型，产出 `schema.json`。**v1.3+** 当用户只给"测评集输入 CSV + agent 版本/服务"而无 scored 数据时，启用 1a-bis 子能力（按需运行 eval）：调用 `scripts/run_eval/<framework>/` + `scripts/score/score.py` 跑出 scored CSV 后再回到本主流程；调用方式与 `auto-fix-executor` §3.3 复用同一组工具链，本 skill 仅做编排。

**harness-loading**：从 Agent 文件中提取并标准化 prompt、工具定义、编排逻辑，产出 `Harness.md`（供下游 auto-single-case-analyzer 做归因时使用的结构化摘要）。如提供的是 Agent 版本 ID 而非文件，则自动拉取对应版本的源码。

**trace-fetching**：**默认获取评测集中所有 badcase 的 trace**（而非等 HITL 圈选后再拉取），统一转换为 analysis-compact 格式，输出到 `traces/` 目录。后续增量分析时不需要重跑此 skill。**v1.3+** 提供 beta 后端：可改走 `scripts/traces_fetch/fetch_and_clean.py` 的 LangGraph 五步清洗管线（与默认 analysis-compact 互斥；体积更小、对 LangGraph 编排链路细节归因更友好；非 LangGraph framework 不可用）。manifest 中通过 `trace_fetch_backend` 字段记录用的哪条管线。

#### 内嵌 HITL: 信息澄清 + 分析范围标注

**位置**：skill 最后一步，物料准备完成后执行。

**人要做的决策**：
1. 确认 schema.json 列类型映射
2. 确认版本信息（单版本 vs 多版本 + 基线）
3. 通过 `selected` 标签筛选本轮分析范围（默认全选）
4. 通过 `analysis_mode` 标签配置分析模式（`direct` / `compare`）

#### 输出 Artifact

```
{analysis_root}/
├── analysis_manifest.json (confirmed)   # 含 selected / analysis_mode / agent_files_path
├── schema.json (confirmed)
├── Harness.md                           # 从 Agent 文件提取的结构化摘要
└── traces/*.json                        # 全量 badcase trace
```

> **Agent 文件的流转**：trace-prep 将 Agent 文件路径记录在 `analysis_manifest.json` 的 `agent_files_path` 字段中，同时从中提取 `Harness.md` 供 auto-single-case-analyzer 做归因。下游 auto-fix-planner 和 auto-fix-executor 通过 manifest 中的 `agent_files_path` 直接访问 Agent 源码，不经过 Harness.md 中转。

**`analysis_manifest.json` 核心字段**（仅为结构示例）：

```json
{
  "analysis_id": "badcase_analysis_032514",
  "created_at": "2026-03-25T14:00:00Z",
  "eval_source": "path/to/evaluation.xlsx",
  "agent_versions": ["v2.1-baseline", "v2.2-modified"],
  "agent_files_path": "path/to/agent/src/",
  "harness_path": "{analysis_root}/Harness.md",
  "schema_path": "{analysis_root}/schema.json",
  "cases": [
    {
      "case_id": "case_017",
      "thread_id": "p-20260302-182813-54eb5c",
      "trace_path": "{analysis_root}/traces/trace_p-20260302-182813-54eb5c.json",
      "eval_row": { "user_query": "...", "actual": "...", "reference": "...", "score": 0 },
      "version": "v2.2-modified",
      "paired_trace_path": null,
      "selected": true,
      "analysis_mode": "direct"
    }
  ]
}
```

**幂等性**：同一份 Excel + 同一组 thread_id → 产出相同 manifest。增量分析只需修改 `selected` 标签。

---

### 3.2 Skill 2: `auto-single-case-analyzer`

**职责**：核心归因引擎——对 n 个 case 逐条分析，收集结构化反馈。

**触发词**：分析 badcase、trace 归因、为什么 agent 回答错了

#### 前置条件

| Artifact | 状态要求 |
|---|---|
| `analysis_manifest.json` | confirmed，至少 1 个 `selected: true` |
| `traces/*.json` | 对应 case 的 trace 文件存在 |
| `Harness.md` | 存在（可选，不存在则降级为 trace 实录级归因） |

#### 两种分析模式

> 以下分析步骤仅为结构说明，具体归因逻辑以实际 skill v5 为准。

**Mode A: 直接归因**（单条 trace）：链路还原 → 逐层归因 → 修复方案 → 报告

**Mode B: 对比归因**（同一 case 的 baseline vs modified trace）：双链路对照还原 → 分歧点归因 → 修复方案 → 报告。需要同时看两条链路才能定位差异根因。

两种模式使用统一输出格式。

#### 并行执行策略

- **支持 subagent 的宿主环境**：subagent 并行，每个 case 独立子代理
- **不支持 subagent 的宿主环境**：串行逐条

由 skill 在提示词中根据环境自动配置，无需人工选择。

#### 输出 Artifact（分析阶段）

```
{analysis_root}/reports/
├── case_report_{case_id}.md       # 完整归因报告（含单 case 渐进修复路径）
└── case_summary_{case_id}.json    # 结构化摘要
```

#### 内嵌 HITL: 结构化反馈

**位置**：所有 case 分析完成后，自动生成查看器，作为 skill 最后一步。可跳过。

**查看器**：参考 `skill-creator` 的 `eval-viewer` 模式，通过 `scripts/generate_feedback_viewer.py` 生成自包含 HTML。

**反馈表单字段（schema 2.2）**：

```
verdict:        ○ 采纳 (accept) ── 零文本字段
                ○ 修改后采纳 (revise) → 展开 revision 文本框
                ○ 拒绝 (reject) → 自动弹出"评分器反馈"弹窗（默认必填，可显式跳过）

priority:       ○ P0  ○ P1  ○ P2  ○ 不纳入本轮修复  (verdict=reject 时隐藏)

group_id:       [可选；所有 verdict 通用 — "加入归并"按钮弹窗多选已审 case]

revision:       [verdict=revise 时必填 — 归因覆盖文本，Planner 必读]

scorer_feedback:[可选 · 顶层正交字段 · 所有 verdict 通用 · 弹窗交互]
                "+ 评分器反馈" 按钮触发 → 弹窗内填字段：
                rubric_ref:         [自由文本，可空，如 "biz_a_score.md §3.1（零重复）"]
                misjudge_pattern:   ○ 评分错误 (score_wrong)         → 派生 affects_score=true
                                    ○ 评分正确但理由错误 (reason_wrong_only) → 派生 affects_score=false
                suggested_revision: [自由文本（必填）]
                                    （affects_score 由 misjudge_pattern 派生，无独立 checkbox）
```

> schema 2.2 关键变更（vs 2.1）：
> - **删除 `reject_subtype` 字段**：reject 含义统一为"不作为 badcase 进入修复流程"，不再细分 not_badcase / env_issue
> - **`misjudge_pattern` 收窄为两值**：`score_wrong`（评分错误）/ `reason_wrong_only`（评分正确但理由错误），值含义即决定 `affects_score`
> - **删除独立的 `affects_score` UI 字段**：由 `misjudge_pattern` 派生（schema 输出层仍含此字段，方便下游消费）
> - **scorer_feedback 改为弹窗交互**：避免折叠造成的页面跳顶问题；reject 时自动弹出（默认必填）
> - **Verdict UI 标签中文化**："Verdict" → "反馈"；"Rubric 引用" → "评分规则引用"
> - **原 `notes` 字段已在 2.1 删除**（与 revision 重叠）；`revision` 仅 verdict='revise' 时填

**归并交互**：在当前 case 点"加入归并"→ 弹窗多选已审过 case → 自动建组 `group_NNN`（可重命名）。组成员等价，每条 case 各自填 revision。归并后的 case 在 sidebar 显示 `[group_001]` 标签，可快速跳过。

**verdict / group_id / scorer_feedback / repair_priority 四正交关系**：

| 维度 | 表达什么 | 取值 | 消费方 | 举例 |
|---|---|---|---|---|
| `verdict` | 对 agent 的反馈方向（归因有效性） | accept / revise / reject | Planner（reject 跳过；accept/revise 进 fix_plan） | revise = 归因要改、改完后修 |
| `group_id` | 同根因聚类信号 | group_NNN 或 null | Planner（最高优先级聚类约束，覆盖 §3.3 四档聚类的语义判定） | group_001 含 case_A/B → 共用一个 FIX |
| `scorer_feedback` | 对评分器的反馈（独立维度） | object 或 null | Executor（§3.4 离线汇聚 + 可选剔除统计） | revise + scorer_feedback = B 情形：agent 真错 + 评分理由也错 |
| `repair_priority` | 本轮修复时间预算 | P0/P1/P2/skip | Planner（fix_plan 内排序与 Iter 分配） | accept + skip = 归因对、本轮不修；reject 时强制 N/A |
| `revision`（从属字段） | revise 路径下的归因覆盖文本 | string | Planner（仅 verdict='revise' 时存在；按此重写归因） | revise + revision="实际是 tool X 调参问题" |

> **设计原则**：用户对一条 case 的反馈本来就是多维的——"对 agent 的反馈方向" + "对评分器的反馈" + "聚类" 三者独立，不应强行塞进一个互斥的 verdict 选项。

`skip` vs `reject` 不重叠：reject = 这条不应是 badcase；skip = 是 badcase、归因也对，但本轮容量/业务策略不修。

**reject 含义（schema 2.2）**：

> **schema 2.2 重要变更**：reject 不再细分子类型。reject 的统一含义是 **"这条不作为 badcase 进入修复流程"**——可能因为评测标注问题、环境问题、或评分器问题（trace 行为对、评分错）。reject 时 viewer **自动弹出评分器反馈弹窗**（默认必填，因为多数 reject 场景与评分器有关）；用户可以点"取消"显式跳过。

**何时填 scorer_feedback**：

| 用户判断 | verdict | scorer_feedback | misjudge_pattern → affects_score |
|---|---|---|---|
| **A 情形**：agent 行为对、评分错（原 scorer_misjudge） | reject | 必填（弹窗自动弹出） | `score_wrong` → true（剔除统计） |
| **B 情形**：agent 真错（要修）+ 评分理由错（要给评分器反馈） | revise + revision | 填 | 评分结果错 → `score_wrong`；理由错但评分结果对 → `reason_wrong_only` |
| **C 情形**：agent 行为对、评分结果对、仅评分理由表达上有些瑕疵 | accept | 填（轻量备注） | `reason_wrong_only` → false（不剔除） |
| **D 情形**：agent 真错、评分理由也对 | accept / revise | 不填 | — |

#### 3.2.1 feedback.json schema 2.2

```jsonc
{
  "schema_version": "2.2",
  "analysis_id": "...",
  "status": "complete | incomplete",
  "total_cases": N,
  "reviewed_at": "ISO 8601",
  "groups": [
    { "group_id": "group_001", "name": "工具参数类问题", "member_case_ids": ["case_017","case_023"] }
  ],
  "feedback": [
    {
      "case_id": "case_017",
      "verdict": "accept | revise | reject | pending",
      "repair_priority": "P0|P1|P2|skip",        // verdict=reject 时省略或 null
      "group_id": "group_001",                    // 可选；所有 verdict 通用（正交）
      "revision": "...",                          // verdict='revise' 时必填、其他 verdict 不出现
      // schema 2.2：reject_subtype 字段已删除（reject 含义统一为"不作为 badcase 进入修复流程"）
      "scorer_feedback": {                        // 可选 · 顶层正交 · 所有 verdict 通用
        "rubric_ref": "如 biz_a_score.md §3.1",   // 可空
        "misjudge_pattern": "score_wrong | reason_wrong_only",  // 2.2 收窄为两值
        "suggested_revision": "对评分理由的建议改写",            // 必填
        "affects_score": true                     // 由 misjudge_pattern 派生：score_wrong→true / reason_wrong_only→false
      }
    }
  ]
}
```

> 字段消费方：`verdict` / `group_id` / `revision` → Planner（§3.3）；`repair_priority` → Planner 排序 fix_plan；`scorer_feedback` → Executor（§3.4）—— Planner 完全忽略 scorer_feedback（修复方向只看 verdict）。Executor 把所有 scorer_feedback 汇聚到离线 markdown；其中 `affects_score === true` 的 turn 还从当前轮 baseline/candidate pass 率统计中剔除。

> **schema 兼容性**：本次干净升级到 2.2，**不兼容旧 2.1 / 2.0 / 1.0**。Planner / Executor 检测到 `schema_version` ≠ "2.2" 时直接报错。仓库内无历史 feedback.json 样本，迁移成本为零。schema 2.1 → 2.2 的核心 breaking change：(a) 删除 `reject_subtype` 字段（reject 含义统一）；(b) `misjudge_pattern` 枚举从 5 值（过严/过松/...）收窄为 2 值（score_wrong / reason_wrong_only），值含义即决定 `affects_score`；(c) `affects_score` 由 `misjudge_pattern` 派生，UI 不再有独立 checkbox 但 schema 输出仍保留该字段。

#### 最终输出 Artifact

```
{analysis_root}/
├── reports/                         # 分析阶段产出
├── feedback_viewer.html             # 查看器
└── feedback.json                    # status: complete / incomplete
```

**幂等性**：同一份 manifest + trace + Harness → 产出相同归因报告。feedback.json 是 HITL 产物，非纯计算结果。

---

### 3.3 Skill 3: `auto-fix-planner`

**职责**：读取归因反馈和 Agent 源码，聚合根因，制定修复方案——分流为"可自动执行"和"需转人工工单"两类，通过跨模型 Reviewer 验证方案合理性。

**触发词**：制定修复方案、生成优化计划、分析完了怎么修

#### 前置条件

| Artifact | 状态要求 |
|---|---|
| `feedback.json` | `status: "complete"`，且 `schema_version === "2.2"`（≠ "2.2" 直接报错并要求用最新 viewer 重新生成） |
| `analysis_manifest.json` | confirmed。语义上不依赖 manifest 做 case 聚合（case 列表从 feedback.json 获取），但运行时仍依赖 manifest 的 `agent_files_path` 做 Agent 源码定位 |
| `case_summary_*.json` + `case_report_*.md` | 被采纳 case 的摘要和归因报告（含单 case 渐进修复路径） |
| **Agent 文件（源码）** | 通过 manifest 的 `agent_files_path` 定位 |
| `repair-principles-v1.6.0.md` | Skill 2 的修复原则文档（7 条硬约束 + 策略优先级 + 3D 评分公式），作为方案制定的**约束输入** |
| `attribution-framework.md` | Skill 2 的归因分类框架（failure_type × target_layer × fix_strategy），Planner 复用其分类体系 |
| 上轮 `optimization_report.md` + `progressive_log.json` + `lessons_learned.md` | 可选，回流场景（round > 1）时读取 |

> **viewer 降级通道**：如 `reports/` 目录不可用但 `feedback_viewer.html` 存在，Planner 可从 viewer 内嵌 JSON 的 `summaries[]` 和 `reports[]` 中降级提取归因数据。禁止一次性 Read 整个 viewer HTML（~1MB）。

#### 处理逻辑

> 以下逻辑仅为结构说明，以实际 skill 为准。

**Step 1: 综合阅读**

消费 feedback.json + 归因报告 + Agent 源码（通过 `analysis_manifest.json` 的 `agent_files_path` 定位源码）：
- 过滤 rejected
- 对 revise 案例使用人工修正后的归因
- **继承修复原则**：以 `repair-principles-v1.6.0.md` 的 7 条硬约束和策略优先级作为方案制定的全局约束基线，Planner 不重新提取这些已固化的规则
- **提取跨 case 增量约束**：从 feedback 自由文本中识别重复出现的、超出 repair-principles 范围的方法论指令，作为本次任务的增量全局规则
- 交叉对照归因报告中的修复位置 vs Agent 实际代码结构
- 聚合 merge group 的共性根因
- 回流场景时读取上一轮产物（见 §6 回流规则）

**Step 2: 方案制定（分流 + Iteration 批次编排）**

- 基于 Agent 源码精确定位修复的代码位置
- 分流为自动优化项 / 转人工工单项
- **Iteration 批次编排**：以 Skill 2 的单 case 渐进路径为核心参考输入，将风险/置信度相近、逻辑相关的修改打包为一个 Iteration，按低风险→高风险排序。每个 Iteration 是 executor 可独立 eval 的原子批次
- 每个 Iteration 标注**类型**和**依赖**：

| 字段 | 说明 |
|---|---|
| `type: 基础 / 核心` | 基础 = 铺垫性低风险修改（退出判断宽松），核心 = 主力修复（退出判断严格） |
| `requires: [iter_N]` | 硬依赖——前置 Iter 被 ROLLBACK 时自动跳过。软依赖通过排序隐含 |

- 每个 FIX 分为**意图层**（不可变：根因、目标、约束、`expected_tradeoffs`、`fix_strategy`）和**实现层**（Executor 可细化）
- 每个 FIX 标注 `fix_strategy`（复用 `attribution-framework.md` v4 的 4 种分类：约束型/能力型/工程型/保障型）+ `target_layer`（P0~P3/PX），用于 Reviewer 校验和 Executor 理解修复意图
- 从 feedback 自由文本中提取的**跨 case 全局约束**作为 fix_plan 的全局规则段
- **`blocked_by_tickets`**：tool-first / knowledge-first 原则落地到执行层——当某个 FIX 依赖人工工单（如数据补全、工具开发）才能生效时，标注 `blocked_by_tickets: [ticket_001]`。S4 Executor 遇到此字段时自动 SKIP 该 FIX
- **`regression_scope`**：每个 Iteration 标注其改动可能影响的 session/turn 范围，指导 S4 抽样和 D1 退化分析聚焦
- **FIX 间交互效应自检**：所有 FIX 生成后，对每对 (FIX_i, FIX_j) 检查路径干扰、规范矛盾、副作用传导。如发现矛盾则标注警告并建议调整
- **不动项显式管理**：fix_plan 中列出不修改的文件及原因，防止误认为遗漏
- **熔断条件与回滚策略**：fix_plan 末尾输出通过/警告/熔断三级条件和回退优先级

**Step 3: Reviewer 授权审查**

Reviewer 是标准化接口，但不是自动外发机制。任何会把 fix_plan、业务上下文、
代码片段、trace 摘要或评分反馈发送给外部模型 / 独立 Agent 的动作，必须先由
用户明确授权。授权前需说明发送范围、调用方式、隐私影响、耗时/成本和是否会
产生评论或修改工作树；默认只允许 read-only / no-fix / no-comment。

授权后可走本地只读 reviewer CLI 或宿主 Agent subagent；未授权或不可用时生成
占位 `reviewer_findings.json`（`findings: []`），HITL 阶段提示用户改由人工审查。

> `scripts/reviewer_adapters/` 目录为早期设计残留，实际不使用。

结果存为独立 artifact `reviewer_findings.json`。

#### 内嵌 HITL: 方案 review

**位置**：fix_plan.md (draft) + reviewer_findings.json 产出后。

**交互方式**：文档评论——优化方案直接通过，或通过文档评论给出修改建议。

#### 输出 Artifact

```
{analysis_root}/{current_round}/
├── fix_plan.md (approved)           # 含意图层/实现层、expected_tradeoffs
├── reviewer_findings.json           # Reviewer 独立产出
└── fix_tickets/                     # 人工工单
    ├── ticket_001.md
    └── ...
```

**幂等性**：同一份 feedback.json + case 报告 + Agent 源码 → 产出相同结构的 fix_plan。

---

### 3.4 Skill 4: `auto-fix-executor`

**职责**：按 approved fix_plan 的 Iteration 批次渐进式执行修复——理解 Agent 源码语义，逐批验证效果，产出新版 Agent 文件和优化效果总结报告。

**触发词**：执行修复方案、应用修复、跑修复

#### 前置条件

| Artifact | 状态要求 |
|---|---|
| `fix_plan.md` | approved，至少 1 个 Iteration 含自动优化项 |
| **Agent 文件（源码）** | 通过 manifest 的 `agent_files_path` 定位，作为 fork 基础 |
| 原始 Eval 结果 | 通过 manifest 的 `eval_source` 定位，用于效果对比 |
| `feedback.json` (schema 2.2) | 用于提取两个集合：(a) **`scorer_feedback_all`** — 所有填了 `scorer_feedback` 的 case（不论 verdict），用于汇聚到 scorer_feedback markdown；(b) **`scorer_excluded_turns`** — 其中 `scorer_feedback.affects_score === true`（即 misjudge_pattern=`score_wrong`）的 case 的 (session, turn)，用于剔除 baseline/candidate pass 率统计 |

**scorer_feedback 处理策略（schema 2.2）**：Executor 启动时加载当前 round 的 feedback.json，按上述两个集合分别处理：

1. **scorer_feedback_all → 离线汇聚**：所有 scorer_feedback（含 rubric_ref / misjudge_pattern / suggested_revision）合并写入 `projects/<biz>/evoloop/scorer_feedback/<YYYYMMDD>_<exp_id>.md`，供下一轮人工迭代评分 prompt 离线消费
2. **scorer_excluded_turns → 当前轮剔除统计**：仅 `affects_score === true` 的 turn 从 baseline/candidate pass 率分子分母双侧剔除（保持比率有意义）。剔除明细全部进 optimization_report §8 单独列。tolerance 判定基于剔除后的 pass 率；剔除明细不参与 D1/D2

**Executor 不自动 override score**——评分 prompt 是离线人工迭代的，自动 override 容易跑偏。`affects_score` checkbox 让用户精细控制：评分理由瑕疵但结果对（不勾）只走离线通道；评分结果不可信（勾上）才剔除当前轮统计。

#### 执行工作区（Execution Workspace）

> 以下执行逻辑仅为结构说明，以实际 skill 为准。

**工作区模型：git branch**

Executor 在 Agent 源码目录原地操作，使用 git branch 管理快照和回滚：

1. **初始化**：在 Agent 源码目录创建执行分支 `evoloop/round_N`，记录初始 commit hash 作为 `stable_snapshot_commit`
2. **每个 Iter 的改动**：在执行分支上直接 Edit/Write，改完后 `git add + git commit`（commit message = `iter_N: <summary>`）
3. **COMMIT**：更新 `stable_snapshot_commit` 为当前 commit
4. **ROLLBACK**：`git checkout <stable_snapshot_commit> -- <changed_files>` 精确恢复，然后 commit 恢复操作
5. **EXIT**：最终 `stable_snapshot_commit` 指向的代码即为新版 Agent 文件

> **为什么不用 worktree 隔离**：Agent server 读取本地文件（`.space/agents/*.md`），eval 需要 server 加载改动后的文件。worktree 隔离意味着需要在 worktree 中启动 server，路径配置和环境管理显著复杂化。git branch 在原地操作，server 重启即可加载最新代码。

#### 源码理解 + Fork

读取 Agent 全量源码，理解代码结构。创建执行分支并记录 stable_snapshot_commit。对 fix_plan 中各 Iteration 的实现层，根据代码实际状态细化。意图层不可修改。

#### 小样本构成规则

每个 Iteration 的小样本 eval 包含两部分：

- **target cases**：feedback.json 中 `verdict != reject` 的所有 case（不按 Iter 过滤，因为交叉影响需要检测）
- **regression guardrail**：全量 eval 集减去 target cases 后，随机抽样 20-30%

**冻结规则**：同一 round 内，guardrail sample 必须固定（seed = round 编号）。每个 Iter 使用相同的 regression 样本，确保 D1 决策之间的比较基准一致。样本列表记录在 `sample_manifest.json` 中。

#### 渐进式执行循环

每个 Iteration 执行后，做两个独立决策——**D1: 当前 Iter 是否接受（COMMIT / ROLLBACK）** 和 **D2: 是否继续（CONTINUE / EXIT）**。全程无人工介入。

```
stable_snapshot_commit = 初始 commit

for each Iter in fix_plan.iterations (按顺序):
    if Iter.requires 中有已 ROLLBACK 的 Iter → SKIP

    应用 Iter 全部改动 → git commit
    小样本 eval (target cases + 冻结的 regression guardrail)
    微调窗口: 根据 eval 信号微调实现层 / 标记已解决的 target case

    D1: COMMIT or ROLLBACK
    D2: CONTINUE or EXIT

    记录 progressive_log
```

#### Decision Inputs（D1 所需的结构化数据）

D1 决策依赖 `compare.py --json` 输出的结构化 summary，而非解析文本表格：

```json
{
  "summary": {
    "baseline_pass": 19,
    "candidate_pass": 13,
    "regressions": 6,
    "improvements": 0
  },
  "changes": [
    {
      "session_number": "12",
      "turn_number": "10",
      "change": "regression",
      "ai_reason_b": "漏回用户提问"
    }
  ]
}
```

D1 的判断流程：
1. 从 `changes` 中筛选 `change == "regression"` 的条目
2. 排除**空输出退化**（`actual_output` 为空 = agent 环境问题，不计入 tolerance）
3. 对剩余质量退化，LLM 模式匹配：将 `ai_reason_b` 与 fix_plan 的 `expected_tradeoffs` 对照，分为预期/非预期
4. 非预期质量退化 > tolerance → ROLLBACK

**D1: COMMIT / ROLLBACK**（当前 Iter 是否接受）

| 条件 | 决策 |
|------|------|
| 非预期**质量**退化 > tolerance | ROLLBACK → `git checkout <stable_snapshot_commit> -- <files>` |
| 核心 Iter + target 无改善 (target_improved == 0) | ROLLBACK |
| 其他 | COMMIT → stable_snapshot_commit = 当前 commit |

tolerance：基础 Iter = 3，核心 Iter = 小样本 case 数的 5%（至少 3）。

> **tolerance 校准依据**（v3.2.1, 2026-04-12 冒烟验证）：同一 sample 两次 eval 的质量退化数波动 ±2 条（8→6），说明 scorer 方差约 ±2。tolerance=1 会将几乎所有有效改动误判为 ROLLBACK。tolerance=3 刚好过滤 scorer 噪声。

> **tolerance 设计依据**：业务A 10% 抽样验证中观察到 agent 输出随机波动（S2T14、S14T6）和 LLM 评分波动（temperature=0.2 仍有噪声）。tolerance=0 会导致虚假 ROLLBACK。

**D2: CONTINUE / EXIT**（是否继续下一个 Iter）

| 前置 | 条件 | 决策 |
|------|------|------|
| COMMIT | 有更多 Iter 且 target 未全部修好 | CONTINUE |
| COMMIT | 无更多 Iter 或 target 全部修好 | EXIT |
| ROLLBACK | 存在后续 Iter 且不 requires 当前 Iter | CONTINUE (当前 Iter 标记 skipped) |
| ROLLBACK | 无可继续的后续 Iter | EXIT |

**微调窗口**：每次小样本 eval 后，Executor 可在实现层范围内做微调。约束：
- 只能修改**当前 Iter 改动过的文件**，跨 Iter 文件修改 = 新 FIX，需回到 planner
- 不可修改意图层、不可新增/删除 FIX 项、不可改变 Iteration 顺序
- 微调后**不**重新 eval（效果在下一个 Iter 的 eval 中自然体现，避免微调→eval 无限循环）

#### 新版 Agent 文件 → 全样本 Eval → 优化效果总结

EXIT 后，用最后一次 COMMIT 的 stable_snapshot 跑全样本评测，结合原始 Eval 输出 `optimization_report.md`（9 个维度：总览指标、Session 级对比、改善归因分析、退化归因分析（区分预期/非预期）、退出判断回顾、优化目标对照、性能开销、疑似评估器问题、下一步建议）。

#### 输出 Artifact

```
{analysis_root}/{current_round}/
├── execution/
│   ├── diffs/                       # 每个 Iter 的变更 diff
│   ├── new_agent_files/             # stable_snapshot 最终状态
│   ├── eval_results/                # 全样本 + 小样本 eval CSV
│   ├── sample_manifest.json         # 冻结的小样本 (session, turn) 列表
│   └── progressive_log.json         # 每个 Iter 的 eval + D1/D2 + run_metadata
└── optimization_report.md           # 优化效果总结（9 维度）
```

#### 闭环（见 §6）

| 场景 | 后续 |
|------|------|
| 提升 + 无副作用 | merge，版本向前 |
| 提升 + 引入退化 | 回流 auto-fix-planner（读 progressive_log.json 的 summary 段） |
| 未提升 | 重新分析 / 调整方案 / 人工核实 |

**结构幂等性**：同一份 fix_plan + 同一份 Agent 文件 → 相同的 Iteration 执行顺序和 D1/D2 决策逻辑。具体代码改动和 eval 结果受 LLM 和运行环境影响不保证字面一致。精确复现需冻结 `progressive_log.json` 中的 `run_metadata`（见 CONTEXT.md）。

---

## 4. HITL 节点汇总

HITL 节点嵌入在各自所属的 skill 内部。每个 HITL 的输出是一个**确认后的 artifact**，作为下游 skill 的前置条件。

| HITL | 所属 Skill | 输出 Artifact | 下游前置条件 |
|---|---|---|---|
| 信息澄清 + 范围标注 | `auto-trace-prep` | `analysis_manifest.json` (confirmed) | auto-single-case-analyzer 检查 |
| 结构化反馈 (查看器) | `auto-single-case-analyzer` | `feedback.json` (complete) | auto-fix-planner 检查 |
| 方案 review (文档评论) | `auto-fix-planner` | `fix_plan.md` (approved) + `reviewer_findings.json` | auto-fix-executor 检查 |

**评估器问题双通道**（schema 2.0）：

- **通道 1（S2 HITL）**：用户在查看器**任意 verdict**（accept / revise / reject）下展开"+ 评分器反馈"，填 `scorer_feedback{rubric_ref, misjudge_pattern, suggested_revision, affects_score}`。`affects_score=true` 时才剔除当前轮统计；否则仅汇聚到下一轮人工 prompt 迭代通道。
- **通道 2（S4 optimization_report §8）**：Executor 跑 baseline/candidate eval 后逐 session 比对，若发现"评分理由与 actual_output 不符"等情形，自动写入 §8 表。

**汇入位置**：`projects/<biz>/evoloop/scorer_feedback/<YYYYMMDD>_<exp_id>.md`（markdown 格式，供下一轮人工迭代评分 prompt 离线消费）。SoT 模板：`core_skills/04_execute/auto-fix-executor/references/scorer_feedback_template.md`（运行时按需 mkdir + 复制并填充）。

**关键约束**：
- S4 不自动 override score，仅做"剔除统计 + 列明细"——避免自动改动评分链路引入新偏差
- 剔除发生在 baseline/candidate pass 率分子分母双侧，保持比率有意义
- 当某轮 `scorer_feedback.affects_score === true` 的 case 占比 > 总样本 20% 时，Executor 输出 WARN 提示"评估器问题占比异常高，建议优先迭代评分 prompt 再进入下一轮 fix"

---

## 5. 旧→新映射关系

| 旧 skill 能力 | 新归属 |
|---|---|
| Phase 1: 物料采集 & Trace 获取 | `auto-trace-prep` |
| Phase 1.5: 分析范围确认 | `auto-trace-prep` 内嵌 HITL（标签筛选） |
| Phase 2-5: 归因分析 + 报告 | `auto-single-case-analyzer` |
| Phase 5.5: 人工反馈确认 | `auto-single-case-analyzer` 内嵌 HITL（查看器） |
| Phase 6-7: 批量/交叉汇总 | `auto-fix-planner`（聚合归因 → 修复方案） |
| Phase 0: 矩阵构建 + 轨迹分类 | `auto-trace-prep`（manifest 标记版本和配对） |
| *新增* 修复方案制定 + 分流 | `auto-fix-planner` |
| *新增* 修复执行 + 测评验证 | `auto-fix-executor` |

---

## 6. 闭环设计

> 本节为操作指南——Skill 4 执行完产出 optimization_report 后，人读完 report 决定下一步，不嵌入任何 skill。

auto-fix-executor 产出 optimization_report.md + 新版 Agent 文件后，人工基于 report 决策。executor 内部的渐进式循环（Batch 级 COMMIT/ROLLBACK，当前 SKILL.md 仍称 Iteration）不纳入闭环——闭环仅基于全样本 Eval 结果确定后的场景。

**Round 边界**：一个 round 对应**一次 approved `fix_plan` 的完整 S4 执行**。S4 → S3 回流（无论是因为引入退化还是方案调整）都会启动新的 round（round_{N+1}），**不在同一 round 内循环**。

```
              optimization_report.md
              + 新版 Agent 文件
                        │
                   人工读 report 后决策
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
  提升+无副作用     提升+退化         未提升
       │                │                │
       ▼                ▼                ▼
  merge 生效       回流 S3           三选一:
  (可选)新一轮     auto-fix-         ①回流 S1/S2
  → S1             planner           ②回流 S3
                   (读 report +      ③人工介入
                    progressive_log)
```

### 路径 A: 版本向前（分数提升、无副作用）

确认 merge，新版 Agent 文件生效。可选择用新版 Agent 的 Eval 结果开启新一轮 auto-trace-prep。

### 路径 B: 调整方案（分数提升、引入退化）

版本不动，回流 auto-fix-planner。Planner 的回流规则（v2.1 已实装）：

1. **始终基于 baseline Agent 源码**制定方案（`agent_files_path` 指向的版本），不基于上轮修改后的 agent 文件。与 CONTRIBUTING.md 的 Baseline Evolution Flow 一致
2. **最近一轮完整读，历史轮次只读摘要**：round_N 完整读取 fix_plan + report + log；round_1~N-1 仅读 report 的总览指标和退出判断回顾
3. **lessons_learned.md 累积维护**：两级归属——`experiments/<exp_id>/lessons_learned.md`（本 experiment 内跨 round 累积）和 `projects/<biz>/evoloop/knowledge/lessons_learned.md`（跨 experiment 长期沉淀，由维护者手工提炼）。累积内容包含"已验证有效策略"、"已证明无效策略"、"反复出现的退化模式"。Planner 禁止重复已证明无效的策略
4. **保留有效修复**：上轮 COMMIT 的 Iteration 视为已生效基线，不重复。ROLLBACK 的 Iteration 需重新制定（降级/拆分/转人工）
5. **Iteration 编号延续**：上轮最后 iter_5 → 本轮从 iter_6 开始

### 路径 C: 分数未提升

人工三选一：重新分析（回流 S1/S2）/ 调整方案（回流 S3）/ 引入人工分析核实（退出自动化）。

---

## 7. 典型使用流程

### 流程 A: 完整闭环（分析 → 修复 → 验证）

```
用户: "分析评测 badcase 并自动修复"
  → auto-trace-prep
    → 输入: Agent 文件 (src/) + Eval 结果 (evaluation.xlsx)
    → 从 Agent 文件提取 Harness.md, 从 Eval 拉取全量 trace
    → HITL: 确认 schema, 标注 5 条 selected=true
    → 产出 analysis_manifest.json (confirmed)

  → auto-single-case-analyzer
    → 5 条 case 并行归因
    → 生成 feedback_viewer.html
    → HITL: 审查报告 (accept/revise/merge/reject)
    → 产出 feedback.json (complete)

  → auto-fix-planner
    → 综合阅读: feedback + 归因报告 + Agent 源码
    → 编排 5 个 Iteration (按风险排序):
       Iter 1 [基础]: 语气规范 (3 文件)
       Iter 2 [基础]: CoT 优化 (profile_extraction_module)
       Iter 3 [核心]: router 硬约束 + domain specialist agent, requires:[1,2]
       Iter 4 [核心]: 子 Agent 推进补强, requires:[3]
       Iter 5 [核心]: 代码层修复 (<module>.py)
    → 分流: Iter 1-5 自动 + 1 条评估器工单
    → Reviewer（授权后）审查
    → HITL: 文档评论 review
    → 产出 fix_plan.md (approved)

  → auto-fix-executor
    → Fork Agent 文件
    → Iter 1: apply → eval → COMMIT, CONTINUE
    → Iter 2: apply → eval → COMMIT, CONTINUE
    → Iter 3: apply → eval → COMMIT, target 未全修好 → CONTINUE
    → Iter 4: apply → eval → ROLLBACK (非预期退化), CONTINUE (Iter 5 不依赖 4)
    → Iter 5: apply → eval → COMMIT, EXIT (无更多 Iter)
    → 全样本 Eval → optimization_report.md
    → 人工读 report → 闭环决策 (§6)
```

### 流程 B: 仅分析（不修复）

```
用户: "帮我分析这批 badcase，不用自动修"
  → auto-trace-prep → auto-single-case-analyzer → 结束
  （feedback.json 可供后续 auto-fix-planner 消费）
```

### 流程 C: 单条快速归因

```
用户: "分析这条 trace: p-20260302-182813"
  → auto-trace-prep (1 条 case)
  → auto-single-case-analyzer × 1 (跳过查看器)
  → 输出 case_report.md (结束)
```

### 流程 D: 增量分析

```
用户: "上次分析了 5 条，再加 3 条"
  → 在 manifest 中将 3 条标记 selected=true (trace 已存在)
  → auto-single-case-analyzer × 3
  → HITL 反馈 → auto-fix-planner (合并新旧反馈)
```

---

## 8. 文件目录结构

### Skill 源码结构

```
core_skills/
├── 00_meta/
│   └── meta-reflection/               # 元过程反思 (v1)
│       ├── SKILL.md
│       ├── stages/
│       │   ├── S1.md                  # draft
│       │   ├── S2.md                  # draft
│       │   ├── S3.md                  # draft
│       │   └── S4.md                  # v1 已实测 (已验证轮次)
│       └── references/
│           ├── output-template.md
│           └── human-review-checklist.md
│
├── 01_prepare/
│   └── auto-trace-prep/                # v1.2
│       ├── SKILL.md
│       ├── scripts/
│       └── references/
│
├── 02_analyze/
│   ├── auto-single-case-analyzer/       # v1.9.0
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   ├── viewer/
│   │   └── references/
│   └── auto-case-summary/              # deprecated
│       └── SKILL.md
│
├── 03_plan/
│   └── auto-fix-planner/              # v2.1
│       ├── SKILL.md
│       ├── scripts/
│       └── references/
│           ├── fix-plan-templates.md
│           ├── repair-principles-v1.6.0.md
│           └── attribution-framework.md
│
└── 04_execute/
    └── auto-fix-executor/              # v1.0
        ├── SKILL.md
        └── references/
            └── optimization-report-template.md
```

### 运行时产物结构

> 详见 `CONTRIBUTING.md §1.2/§1.3`（项目目录模板）。核心规则：S1/S2 产物在 experiment 内跨 round 共享；S3/S4 产物在 `rounds/round_N/` 内按轮次隔离。`projects/<biz>/evoloop/iterations/round_*` 为 v3.2 之前的 legacy 数据，保留只读。

### Artifact 流转与前置条件汇总

| 下游 Skill | 前置 Artifact | 状态要求 |
|---|---|---|
| `auto-single-case-analyzer` | `analysis_manifest.json` | confirmed，≥1 个 `selected: true` |
| `auto-single-case-analyzer` | `Harness.md` | 存在（可选，不存在则降级） |
| `auto-single-case-analyzer` | `traces/*.json` | 对应 case 的 trace 存在 |
| `auto-fix-planner` | `feedback.json` | `status: "complete"` 且 `schema_version === "2.2"` |
| `auto-fix-planner` | `case_summary_*.json` + `case_report_*.md` | 被采纳 case 的摘要和归因报告 |
| `auto-fix-planner` | **Agent 文件（源码）** | 通过 manifest `agent_files_path` 定位 |
| `auto-fix-planner` (回流) | optimization_report + progressive_log | 上一轮产物（可选） |
| `auto-fix-executor` | `fix_plan.md` | approved，≥1 个自动项 approved |
| `auto-fix-executor` | **Agent 文件（源码）** | 通过 manifest `agent_files_path`，fork 基础 |
| `auto-fix-executor` | 原始 Eval 结果 | 通过 manifest `eval_source`，效果对比 |

---

## 9. 设计决策日志

以下设计决策已基于实践反馈纳入正式章节（源自工作流复盘 2026-04-08）：

| 编号 | 决策 | 纳入章节 | 依据 |
|------|------|---------|------|
| P3-1 | 移除 feedback_manifest.json，Planner 直接消费 feedback.json | §3.3 | 实践验证直接消费效果等价 |
| P3-2 | Planner Iteration 编排以 Skill 2 渐进路径为核心参考 | §3.3 | Skill 2 已提供单 case 渐进路径 |
| P3-3 | Reviewer 标准化接口 + 独立 artifact | §3.3 | 宿主 Agent 集成成本高，需标准化 |
| P4-1 | Eval 策略：小样本先行 → 全样本确认 | §3.4 | 避免每 Iter 全量 eval 的时间浪费 |
| P4-2 | COMMIT/ROLLBACK + expected_tradeoffs 区分预期/非预期退化 | §3.4 | "任意退化即熔断"会否决 +7.1pp 的有效修复 |
| P4-3 | Executor 具备代码理解能力，fix_plan 分意图层/实现层 | §3.3/3.4 | 执行修复需理解代码语义 |
| P4-4 | optimization_report 扩展为 9 个维度 | §3.4 | 改善/退化归因是回流 planner 的核心输入 |
| S1 | Artifact 版本化 (iterations/round_N/) | §8 | 回流场景需要历史可追溯 |
| S2 | 评估器问题通过 reject + optimization_report 双通道反馈 | §3.4 + §4 | Skill 4 eval 阶段同样发现评估器问题 |
| D1 | 渐进粒度从 per-FIX + Level 改为 Iteration 批次 | §3.3/3.4 | 实操中风险相近的修改打包执行 |
| D2 | 全局约束双轨：单次 Planner 提取 + 跨任务 SKILL.md 继承 | §3.3 | feedback 中重复出现的方法论约束需自动识别 |
| D3 | Iteration 类型标注（基础/核心）+ requires 依赖 | §3.3 | 基础 Iter 不做严格退出判断 |
| D4 | 双决策模型（D1: COMMIT/ROLLBACK + D2: CONTINUE/EXIT） | §3.4 | 四种组合覆盖所有场景，全程无人工 |
| D5 | 微调窗口：Executor 可在实现层范围内微调 | §3.4 | eval 信号可用于调整实现细节 |
| D6 | 闭环决策为操作指南（人工读 report 后决策） | §6 | 不嵌入 skill |
| D7 | FIX 间交互效应自检（路径干扰/规范矛盾/副作用传导） | §3.3 | Round 2 复盘：P0/P1 设计矛盾（router 截留 vs 子Agent推进）导致回流 |
| D8 | fix_plan 增加熔断条件 + 回滚策略 + 不动项显式管理 | §3.3 | Round 2 复盘：缺少安全网和显式不改声明 |
| D9 | Anti-Few-shot 检测扩展到引号包裹的具体话术 | §3.3 | 跨项目 dry-run：业务A FIX_005 灰色地带（`"我先给您出个参考方案"`） |

---

## 10. 待决事项

1. **查看器 Markdown 渲染**：feedback_viewer.html 需要 Markdown → HTML 转换，建议引入 `marked.js`。

2. **Reviewer adapter 实现**：reviewer adapter 在非 git 仓库、Windows、中文内容场景下需特殊处理，需封装为稳定脚本。

3. **小样本 regression 抽样策略**：随机 / 按 session 分层 / 按场景分层，需实践确定。

4. **非预期退化 tolerance**：基础 Iter = 3，核心 Iter = max(3, 小样本 case 数 5%)。已通过冒烟测试验证（scorer 方差 ±2）。

5. **人工工单格式**：fix_tickets/*.md 格式需与接收方对齐。

6. **回流 planner 行为模式**：建议局部调整（仅修改引发退化的 Iteration），保留已验证有效的修复。

7. ~~**feedback.json revision 字段结构化**~~（schema 2.0 已部分处理）：原议题为拆分 revision 为子字段；schema 2.0 已通过 verdict 三态化 + group_id 正交 + reject_subtype 子类型完成主要结构化。剩余可演进项：scorer_feedback markdown 通道升级为 jsonl + 自动 prompt patch；revision 内嵌 corrected_root_cause / corrected_fix_target 拆分（仍可作为 P2 优化）。

8. **Round 间状态传递**（P2 未来方向）：增加 `round_context` 结构化输入，包含上轮 fix_plan 摘要、执行结果、保留/回退的 FIX、教训总结。使 Planner 感知"这是第几轮"和"上轮做了什么"。

9. **变体生成能力**（P2 未来方向）：当 feedback 中存在互斥的 revision 意见时（如"放开约束" vs "新增 subagent"），生成多个变体方案供决策者选择，附差异对照表。

---

## 11. 产品化演进路径（前瞻）

当前架构为**工程阶段**设计：四层术语直接作为文件系统 + git 状态。这适合单团队 / 少数维护者的快速迭代，但在产品化（多租户 Web UI / Agent IDE / SaaS）阶段需要重构。本节记录已识别的障碍与演进方向，**不是当前阶段的实施任务**。

### 11.1 已识别的产品化障碍

1. **术语直接面向用户**：Experiment / Round / Batch 对产品用户（非工程师）有心智负担，需要产品术语层
2. **git 作为状态源**：阻碍多租户隔离、实时协作、审计日志、并发操作
3. **目录深度**：`experiments/<id>/rounds/round_N/execution/eval_results/` 不适合 REST API 扁平建模
4. **缺失用户/权限/运行实体建模**：当前无 owner / tenant / access control / 运行环境隔离
5. **HITL 交互方式**：通过文档评论的审批流不适合产品界面，需结构化审批模型

### 11.2 三阶段演进

| 阶段 | 做法 |
|------|------|
| **现在（内部工具）** | 保持当前四层命名 + git 实验数据库。在 artifact 中预留 `display_name` 映射层（§0.1）。 |
| **产品化前夕** | 在现有基础上套一个产品层抽象（任务 / 版本 / 变更 / 修复项）。内部仍跑四层，但对外接口（API / UI）只暴露产品术语。引入 owner / tenant / visibility。 |
| **产品化成熟期** | 逐步把状态从文件 + git 迁到 DB；git 退回 CI/CD 角色，`experiments/` 目录作为只读导出或归档格式。 |

### 11.3 当前阶段的具体保障

为避免产品化时做大规模重命名或数据迁移：

1. 所有 artifact（`goal.md`、`progressive_log.json`、`optimization_report.md`）**顶部**包含 `display_name`
2. DESIGN.md / CONTRIBUTING.md / SKILL.md 里的术语是**工程术语**，不应写入任何 UI 面向文本
3. 未来需要新增用户 / 权限 / 租户模型时，在 `goal.md` 增量添加 `owner` / `tenant` / `visibility` 字段，不破坏现有结构
