---
name: auto-fix-planner-pure-attribution-v2.1
version: 2.1.0
description: >
  修复方案制定 skill（纯归因版）——读取归因反馈（feedback.json）和 Agent 源码，聚合共性根因，
  独立制定修复方案（fix_plan.md）并分流为"可自动执行"和"需转人工工单"两类。
  通过跨模型 Reviewer 验证方案合理性，产出 reviewer_findings.json。

  v2.1 字段简化适配（对应 analyzer v1.9.0 + attribution-framework v6）：
  - root_cause schema 不再含 stage / mode 字段；失败的认知阶段语义和集合差类型语义
    以自然语言写入 description / evidence
  - §1.5 共性根因聚合算法重写：旧"(component, stage, mode) 三元组档位"坍缩为
    "结构共性 / 规则共性 / 因果共性 / 语义聚类"四档；语义判断由 description 文本承担

  v2.0 纯归因变体（与 auto-fix-planner v1.2 并存）：
  - 仅消费 auto-single-case-analyzer 的归因字段（scope、root_causes[]、causal_edges）
  - **显式忽略** skill 02 输出的 repair_path / fix_step1_* 字段，不读取 skill 02 的 Step 1/2/3 修复建议
  - 由 Planner 从"原始归因 + Agent 源码"独立推导修复方案，验证归因-修复解耦后的修复质量
  - 核心假设：修复方案的锚点选择应基于全局视角（跨 case 聚合 + 源码架构），而非单 case 局部建议

  核心能力：综合阅读（继承修复原则 + 提取增量约束 + 交叉对照源码）、
  方案制定（Iteration 批次编排 + FIX 双层结构 + 全局规则段）、
  跨模型 Reviewer（标准化接口 + 适配器模式）。

  当用户提到以下任何场景时务必触发此 skill：
  制定修复方案（纯归因版）、v1.9.0 归因制定修复、pure-attribution planner、
  验证归因-修复解耦效果、从 root_causes 独立推导修复。

  与 auto-single-case-analyzer 的边界：该 skill 输出单 case 归因报告（含 repair_path），
  本 skill **仅使用归因部分**（root_causes + causal_edges），从全局视角聚合为可执行的 Iteration 批次方案。
  与 auto-fix-executor 的边界：本 skill 产出 fix_plan.md (approved)，
  Executor 消费 fix_plan 执行修复，可细化实现层但不可修改意图层。
---

# Fix Planner

读取归因反馈和 Agent 源码，聚合共性根因，制定修复方案——分流为"可自动执行"和"需转人工工单"两类，通过跨模型 Reviewer 验证方案合理性。

## 输入

| 物料 | 必选 | 说明 |
|------|:----:|------|
| `feedback.json` | ✅ | Skill 2 HITL 产出，`status` 须为 `"complete"` 且 `schema_version === "2.2"`（≠ "2.2" 直接报错并要求用最新 viewer 重新生成）。Planner **完全忽略** `scorer_feedback` 字段——它由 Executor 消费（剔除统计 + 离线 markdown），不影响 Planner 的修复决策 |
| `analysis_manifest.json` | ✅ | Skill 1 产出，仅用于读取 `agent_files_path`（Agent 源码路径）。case 列表从 feedback.json 获取，不从 manifest 获取 |
| `case_summary_*.json` | ✅ | 被采纳 case 的结构化摘要（每个 ~0.5-1KB），从 `{analysis_root}/reports/` 读取 |
| `case_report_*.md` | 按需 | 完整归因报告（每份 ~5-10KB）。仅在需要深挖渐进修复路径时 Read 对应文件 |
| **Agent 文件（源码）** | ✅ | 通过 `analysis_manifest.json` 的 `agent_files_path` 定位 |
| 上轮 `optimization_report.md` + `progressive_log.json` | 可选 | 回流场景时读取，位于 `{round_dir}/` |

> **修复原则**：§1.3 内联了 7 条硬约束的摘要；完整的策略优先级、评分公式和检查清单见 `references/repair-principles-v1.6.0.md`。**归因框架**：scope / component / rule_violation / fix_strategy / target_layer 的枚举值定义见 `references/attribution-framework.md` v6。
>
> **viewer 降级通道**：如 `reports/` 目录不可用但 `feedback_viewer.html` 存在，可从 viewer 内嵌 JSON 的 `summaries[]` 和 `reports[]` 中提取数据。**禁止一次性 Read 整个 viewer HTML**（~1MB），应使用 Grep 定位 `<script id="embedded-data">` 后按需提取。

> **⚠️ v2.0 纯归因消费约束（与 v1.2 的核心区别）**：
>
> 本 skill **仅读取** `case_summary_*.json` 的归因字段：`scope`、`root_causes[]`、`causal_edges`、`root_cause_chain`、`one_line_summary`、`typical_snippet`、`tags`。
>
> **显式忽略**以下字段（即使 summary JSON 中存在也不得参考）：
> - `repair_path.steps[]`（skill 02 的 Step 1/2/3 修复建议）
> - `fix_step1_component` / `fix_step1_target_layer` / `fix_step1_strategy`（skill 02 的 Step 1 三元组）
>
> **为什么**：验证"归因-修复解耦"后的修复质量——如果 Planner 从 root_causes 独立推导出的方案质量不低于 v1.2（消费 skill 02 Step 1 建议）的方案，说明修复阶段的锚点选择只需原始归因即可，skill 02 不必输出修复建议。
>
> **如何执行**：在 §1.2 归因报告阅读时，只提取上述归因字段，跳过 repair_path 等字段。在 FIX 生成（§2.1）时，fix_strategy / target_layer / fix_location 由 Planner 从 root_causes + Agent 源码独立决策，而非从 skill 02 的 repair_path.steps 复制。

## 输出 Artifact

```
{round_dir}/
├── fix_plan.md (approved)           # 含全局规则、Iteration 编排、FIX 双层结构
├── reviewer_findings.json           # Reviewer 独立产出
└── fix_tickets/                     # 人工工单
    ├── ticket_001.md
    └── ...
```

> 完整模板结构见 `references/fix-plan-templates.md`。

---

## 前置条件检查

> **路径变量定义**（v3.3 新结构）：
>
> - **`{experiment_root}`**：一个 experiment 的根目录，形如 `projects/<biz>/framework-version/<framework-id>/evoloop/experiments/<exp_id>/`
> - **`{analysis_root}`**：`{experiment_root}/analysis/`——S1/S2 产物（feedback.json、reports/、traces/）所在目录
> - **`{round_dir}`**：`{experiment_root}/rounds/round_N/`——当前 round 的 S3/S4 产物目录
>
> `feedback.json` 所在目录即为 `{analysis_root}`。
>
> **v3.3 vs legacy 判定**：若 `{analysis_root}` **自身**的目录名为 `analysis`（即 feedback.json 路径形如 `.../experiments/<exp_id>/analysis/feedback.json`），为 v3.3 新结构，此时 `{experiment_root}` = `{analysis_root}` 的父目录。否则为 legacy（v3.2 旧结构），`{analysis_root}` 就是 `projects/<biz>/evoloop/` 根目录，`{experiment_root}` 不存在，round 产物路径回退为 `{analysis_root}/iterations/round_N/`。新 experiment 必须使用 v3.3 结构。

skill 启动时按以下顺序执行检查：

1. **检查 feedback.json**：
   - 不存在 → 报错，提示用户先完成 auto-single-case-analyzer 的 HITL 反馈
   - `schema_version` ≠ "2.2" → **直接报错**："检测到 schema_version={X}，本 Planner 仅消费 schema 2.2（v2.1/v2.0/v1.0 已废弃）；请用最新 feedback_viewer 重新生成 feedback.json"
   - `status: "incomplete"` → 提示用户在查看器中完成反馈后再继续
   - `status: "complete"` 且 `schema_version === "2.2"` → 继续。将 feedback.json 所在目录设为 `{analysis_root}`；若 `basename({analysis_root}) == "analysis"` → `{experiment_root}` = `{analysis_root}` 的父目录（v3.3）；否则走 legacy 路径
2. **定位 analysis_manifest.json**：在 `{analysis_root}/` 下查找，仅读取 `agent_files_path` 字段（不使用其 cases 列表——case 列表以 feedback.json 为准）
3. **过滤 feedback**（schema 2.2：verdict 三态 + group_id 正交 + scorer_feedback 顶层正交；reject 不再细分 subtype）：
   - `verdict: "reject"` 的 case **不纳入修复流程**（schema 2.2：reject 含义统一为"不作为 badcase 进入修复流程"，无 reject_subtype 字段）。`scorer_feedback` 是顶层正交字段，由 Executor 消费，Planner 不读不写
   - 收集 `verdict ∈ {"accept", "revise"}` 的 case
   - 解析顶层 `groups[]` 数组与各 case 的 `group_id` 字段：同 `group_id` 的 case 在 §1.5 聚合阶段视为最高优先级聚类约束（覆盖语义判定）。注意：`group_id` 与 verdict 正交，accept + group_id / revise + group_id 都合法
4. **验证归因报告**：对每个纳入的 case，确认 `{analysis_root}/reports/case_summary_{case_id}.json` 存在。缺失则检查是否有 viewer HTML 可降级（见输入说明）
5. **验证 Agent 源码**：确认 `agent_files_path` 指向的目录可访问
6. **回流检测**：v3.3 新结构下检查 `{experiment_root}/rounds/` 是否存在；legacy 场景下检查 `{analysis_root}/iterations/`。如存在，找到最大 `round_N`，检查其下是否有 `optimization_report.md` 和 `progressive_log.json`。如有则进入回流模式，当前 round = max(N) + 1；如无则 round = 1

---

> **encoding 硬规则**：所有 `open()` / py -c 内联脚本必须显式指定 `encoding='utf-8'`。Windows Python 默认 GBK，不加 encoding 的 JSON/CSV 读写遇到中文必崩。

---

## Step 1: 综合阅读

直接消费 feedback.json + 归因报告 + Agent 源码，不产出中间 artifact。本步骤的输出是 skill 内部的工作状态，直接输入 Step 2。

### 1.1 Feedback 解析与过滤

读取 `feedback.json`（schema 2.2）：
- **reject**：跳过，不纳入任何修复流程。在最终覆盖矩阵中标记"不纳入（reject）"——schema 2.2 reject 不再细分子类型，含义统一为"不作为 badcase 进入修复流程"。`scorer_feedback` 字段由 Executor 处理，Planner 不读
- **accept**：直接使用 `case_summary` 的 **归因字段**（scope / root_causes / causal_edges），不读取 repair_path
- **revise**：`revision` 字段包含人工修正后的归因（schema 2.2：仅 verdict='revise' 时存在）。当 `revision` 与原始报告冲突时，**以 `revision` 为准**。具体处理：
  - `revision` 中对 root_causes 的修正（如 component 应改为 tool、rule_violation 判断错误、description 失败语义不准确）覆盖原始值
  - `revision` 未涉及的归因字段（`component`、`rule_violation`、`description`、`evidence`）保留原始值
  - `revision` 中对 skill 02 Step 1/2/3 的评价（如"step1 不采纳"）**本 skill 忽略**——v2.0 不消费 skill 02 的修复建议，仅以修正后的归因作为本 skill 独立推导的输入
- **group_id（正交字段）**：feedback.json 顶层的 `groups[]` 给出 group_id → member_case_ids 映射。组成员等价（schema 2.0 不引入 representative），各 case 各自填 revision；Planner 在 §1.5 §"合并 group" 把同组 case 的 root_causes 全量保留作为同根因聚类，优先级高于自动四档聚类

### 1.2 归因报告阅读（v2.0 纯归因模式）

**先读 summary（轻量）**：对每个纳入的 case，读取 `{analysis_root}/reports/case_summary_{case_id}.json`（每个 ~0.5-1KB）。

**第一步：scope 过滤（强制先行）** — 读取顶层 `scope` 字段：
- `scope=external`：仅读取 `external_reason` 与 `hitl_ref`，将该 case 加入 external 工单清单（§4 输出），**跳出本步骤后续字段提取**，不进 FIX 生成、不进 §1.5 共性聚合
- `scope=in_agent`：继续以下归因字段提取

**第二步：归因字段提取（仅 scope=in_agent）**：

| 字段 | 用途 | 是否强制 |
|------|------|:--------:|
| `scope` | 判定 in_agent / external（已在第一步过滤） | ✅ |
| `root_causes[]` | 每个独立失败节点的 component/rule_violation/rule_ref/trace_refs/description/evidence。**v2.1 起 stage / mode 已从字段中移除**——失败的认知阶段语义和集合差类型语义在 description 自由文本中表达，聚类和锚点推断时基于 description 做语义判断 | ✅ |
| `causal_edges[]` | 根因间的因果关系（用于 §1.5 共性聚合和 §2.1 杠杆点识别） | ✅ |
| `root_cause_chain` | 根因链的一句话描述（辅助阅读） | 可选 |
| `one_line_summary` | 根因一句话总结 | 可选 |
| `typical_snippet` | 代表性 input→output 片段 | 可选 |
| `tags` | 跨 case 聚合辅助标签 | 可选 |

**显式跳过**（v2.0 核心约束）：`repair_path`、`repair_path.steps[]`、`fix_step1_component`、`fix_step1_target_layer`、`fix_step1_strategy`。读取 JSON 时可用 `dict.get(...)`，**不得**将其纳入 Planner 的决策输入。

对 revise case，将 `revision` 文本与 root_causes 字段交叉对照，生成"修正后归因"。例如：
- feedback 说"component 应该是 tool:preference 而不是 agent:profile_extraction_module" → 修正对应 root_cause 的 component
- feedback 说"description 应该是'信息检索阶段漏掉关键词'，不是'意图理解阶段误判'" → 修正 description 文本（对应 v1.8.0 的 stage/mode 修正，现在通过自由文本承载）
- feedback 说"这是 rule_violation=true，违反输出格式规则 §3.2" → 修正 rule_violation 与 rule_ref

**按需读 report（重量）**：仅在某个 case 需要看 trace 原文、细节补充时，才 Read 对应的 `case_report_{case_id}.md`（每份 ~5-10KB），且阅读时**跳过"四、修复方案"章节**——v2.0 不消费 skill 02 的修复建议。不要一次性读取所有 report。

### 1.3 全局约束继承与提取

**基线约束（继承）**：

完整读取 `repair-principles-v1.6.0.md`。以下 7 条硬约束作为本次方案制定的不可违反规则：

1. Anti-Few-shot 规则（最高优先级）
2. Agent 能力边界（Master Agent 仅路由/整合，Sub-Agent 在 skill 范围内生成内容）
3. 路由/编排优先（现有架构有对应子 Agent → 先修路由）
4. 知识/数据优先（先补知识 → 再加逻辑）
5. 工具优先（计算/查询/格式问题 → 工具层解决）
6. Step 1 充分性（Step 1 须独立解决或显著缓解核心问题）
7. 新 Skill 创建门槛（高频 + ROI 合理 + 清晰能力边界）

同时读取修复策略优先级和三维优先级评分公式（杠杆率 × 成本分 × 确定性分），用于 FIX 排序。

**增量约束（提取）**：

扫描所有 feedback 条目的 `revision` 字段（schema 2.0 已删除 `notes`，`revision` 是承载用户修改意见的唯一文本字段），识别重复出现的方法论指令。提取规则：
- 同一指令在 **≥ 3 条** feedback 中出现 → 提取为本轮增量全局约束
- 记录出处频次（如"8/9 条 feedback 提及"）
- 增量约束不得与基线约束冲突；如重叠，视为对基线约束的强化确认

### 1.4 Agent 源码阅读

通过 `agent_files_path` 读取 Agent 全量源码，建立架构心智模型：

1. **Agent 架构识别**（按优先级阅读）：
   - **优先读取** Agent 定义文件（如 `.space/agents/*.md`），识别各 Agent 的角色定位、路由关系和工具清单。这是建立架构心智模型的核心输入
   - **按需读取** Skill 定义文件（如 `.space/skills/*/SKILL.md`）——仅读取与纳入 case 的 root_causes 的 `component`（如 `tool:preference` 映射到对应 skill 或工具源码）相关的 skill，不需要全量阅读所有 skill
   - 识别工具（tools）定义和调用方式
   - 如有编排代码（如 LangGraph 配置），一并阅读

2. **交叉对照**（v2.0：从 root_causes.component 定位，不从 skill 02 repair_path）：
   - 对每条 root_cause 的 `component`（如 `agent:router`、`tool:quotation`），在 Agent 源码中定位对应的定义文件（如 `.space/agents/router.md`、`.space/tools/quotation.py`）
   - 结合 root_cause 的 `description`（含失败语义概括）、`evidence`、`trace_refs`，推断"修复锚点最可能落在哪个文件/段落"——这一步完全由 Planner 独立判断，不参考 skill 02 输出的 `fix_step1_component` 或 `repair_path.steps[].location`
   - 锚点候选产出格式：`{component} → {file_path} → {段落/函数名}`。这是后续 §2.1 FIX 生成中 `fix_location` 字段的来源
   - 如 revise feedback 已修正了 component（如"不是 agent:profile_extraction_module，是 tool:preference"），优先使用修正后的 component 重新定位

### 1.5 共性根因聚合（v2.1：基于 component 结构维度 + description 语义聚类）

跨 case 识别共性模式。**v2.1 算法重写说明**：v2.0 的"(component, stage, mode) 三元组档位"在 attribution-framework v6 移除 stage / mode 后失效，本节重写为"结构共性 / 规则共性 / 因果共性 / 语义聚类"四档。stage 表达的"认知阶段"和 mode 表达的"集合差类型"已下沉到 `description` 自由文本，Planner 通过对 description 文本做**语义判断**决定"是否同一类失败"，而非依赖固定枚举字段。**好处**：避免上游 stage/mode 误判导致的错误聚类；**代价**：聚类置信度依赖 description 写作质量——如发现某 case 的 description 过短或缺失失败语义概括，应在 §1.1 的 revise 处理中先补全 description，再进入聚类。

把所有 case 的 root_causes 展开成一张扁平表，按以下四档进行聚类（一条 root_cause 可同时归入多档）：

1. **结构共性**：`component` 相同（位置一致）→ 同一处 agent / tool / memory 出问题。这是最基础的位置维度共性，覆盖最广。
2. **规则共性**：`rule_violation=true` 且 `rule_ref` 指向同一规则条款 → 同一条 system prompt 规则被反复违反。**独立于 component**（同一规则可能在多个 component 触发），但需在结果中标注涉及的 component 列表。
3. **因果共性**：利用 `causal_edges`——如果多个 case 的 causal_edges 都指向同一上游 rc（同一 `component` + `description` 语义近似）→ 识别为"共性上游根因"，下游连锁失败可由统一修复杠杆点解决。
4. **语义聚类**：对结构共性内部、以及跨 component 的 root_causes，由 Planner **基于 description / evidence / trace_refs 做语义判断**，识别同一类失败模式或同一系统性问题。例如：
   - 同 component 内部：多条 root_cause 都描述"在意图理解阶段漏掉时间维度判断"——尽管 description 文本不完全相同，但失败模式同质，归为一类
   - 跨 component：多条 root_cause 都描述"在结果整合阶段输出多余字段"——可能指向跨组件的输出规范缺失，识别为系统性问题

**聚类执行顺序**：先做结构共性（机械分组）→ 再叠加规则共性（横切）→ 再做因果共性（穿透因果图）→ 最后做语义聚类（LLM 语义判断）。前三档是确定性分组，第四档由 Planner 主观判断。

**合并 group**（schema 2.0：`group_id` 正交字段）：feedback.json 顶层 `groups[]` 数组定义的 group_id → member_case_ids 映射，组内 root_causes 全部保留，作为最高优先级聚类约束（高于上述四档自动聚类）。组成员等价（无 representative），组内每条 case 的 revision（若有）独立处理。注意：`group_id` 与 verdict 正交——组内可同时含 accept 与 revise 的 case，仅 reject case 由 §1.1 已剔除。

**每组产出**：
- 共性根因描述（一句话概括，包含失败语义——哪个认知阶段、何种集合差）
- 涉及 case 列表 + root_cause id 列表
- 共享的 `component` 列表 + `rule_violation` 状态 + 所属聚类档位（结构 / 规则 / 因果 / 语义）
- 共性 description 摘要（从组内多条 description 中提炼共同语义）
- 由 Planner **独立推断**的建议 `fix_strategy`（从 attribution-framework.md v6 的 4 种分类中选取）
- 由 Planner **独立推断**的建议 `target_layer`（从 P0_prompt/P1_skill/P2_tool/P3_orchestration 中选取）
- 推断依据：基于 `component` + `rule_violation` + `description / evidence` 语义概括 + Agent 源码架构，而非 skill 02 的 fix_step1_* 字段

### 1.6 回流阅读（条件执行）

仅在回流模式（round > 1）下执行：

1. 读取上一轮 `optimization_report.md`：关注"退化归因分析"和"版本迭代建议"章节
2. 读取上一轮 `progressive_log.json`：识别每个 Iteration 的 D1（COMMIT/ROLLBACK）结果
3. **保留策略**：上轮 COMMIT 的 Iteration 对应的 FIX 不再重复制定
4. **重制策略**：上轮 ROLLBACK 的 Iteration 需重新分析原因（非预期退化/target 无改善），针对性调整：
   - 降级改动范围
   - 拆分为更细粒度的 Iteration
   - 转为人工工单
5. **约束继承**：从上轮退化归因中提取教训，作为本轮额外约束

---

## Step 2: 方案制定

基于 Step 1 的阅读结果，产出 `fix_plan.md`。

### 2.1 FIX 生成（v2.0：从归因独立推导）

对每个共性根因组（或未聚合的独立 case），生成 1 个或多个 FIX 项。每个 FIX 采用**双层结构**。

> **⚠️ v2.0 硬约束**：FIX 的 `fix_strategy`、`target_layer`、`fix_location`、`before`、`after` 全部由 Planner 基于 root_causes + Agent 源码 **独立推导**，**不得**从 skill 02 的 `repair_path.steps[]` 或 `fix_step1_*` 字段复制或参考。如发现自己写的 FIX 与 skill 02 的建议高度相似，应自查：是潜意识读取了 skill 02 输出？还是纯粹的独立推导恰好收敛？前者须重做，后者应在 FIX 的推导说明中注明"根因→修复"的独立推理链。

#### 意图层（Executor 不可修改）

| 字段 | 说明 | 必填 |
|------|------|:----:|
| `fix_id` | 唯一编号（FIX_001, FIX_002, ...） | ✅ |
| `title` | 一句话修复标题（用于 Iteration 总览表和标题展示） | ✅ |
| `root_cause` | 根因描述（来自 §1.5 共性根因聚合，包含 component + rule_violation 结构特征 + 失败语义概括） | ✅ |
| `source_root_causes` | 本 FIX 覆盖的 root_cause id 列表（格式：`case_xxx#rc_1`，来自 case_summary.root_causes[].id） | ✅ |
| `source_cases` | 本 FIX 覆盖的 case_id 列表 | ✅ |
| `derivation_note` | 推导说明：简述从 root_causes 到当前 fix_strategy/target_layer 的推理链（v2.0 特有，用于区分独立推导 vs 参考 skill 02） | ✅ |
| `target` | 行为目标（修复后 Agent 应如何表现） | ✅ |
| `constraints` | 本 FIX 须遵守的约束（来自全局规则或 case 特定 revision） | ✅ |
| `expected_tradeoffs` | **必填**：预期副作用描述。Executor 的 D1 退出判断依赖此字段 | ✅ |
| `regression_scope` | 改动影响面描述：哪些当前通过的 turn/场景可能受影响，Executor 据此抽样回归验证 | 可选 |
| `fix_strategy` | 从 `attribution-framework.md` 选取，**允许多值数组**：[约束型修复, 能力型修复, 工程型修复, 保障型修复]。同一 FIX 可能同时涉及约束+能力两种策略 | ✅ |
| `target_layer` | 从 `attribution-framework.md` 选取，**允许多值数组**：[P0_prompt, P1_skill, P2_tool, P3_orchestration, PX_eval]。跨层修复时列出所有涉及层 | ✅ |

#### 实现层（Executor 可细化）

| 字段 | 说明 | 必填 |
|------|------|:----:|
| `fix_location` | Agent 源码中的精确位置（文件路径 + 段落/字段名） | ✅ |
| `before` | 修改前代码的**定位描述**（文件路径 + 行号或段落标题 + 关键行摘要）。用于让 Executor 定位修改位置，**不要粘贴全文**——Executor 会自行 Read 源码确认 | ✅ |
| `after` | 修改后的**精确文本**（仅含变更行 ± 3 行上下文）。Executor 用此文本做 Edit 操作 | ✅ |
| `implementation_notes` | 给 Executor 的实现指引（如"若源码已变更，按此意图调整"） | 可选 |

#### FIX 生成规则

1. **修复策略优先级**：严格遵循 `repair-principles-v1.6.0.md` 的策略优先级。高优先级策略（工具/知识/路由修复）须先尝试，不可无理由跳到低优先级策略（prompt 约束堆积）
2. **三维优先级评分**：对每个 FIX 计算 `Priority = 杠杆率 × 成本分 × 确定性分`（具体定义见 repair-principles），用于 Iteration 内部排序
3. **Anti-Few-shot 检查**：`after` 字段中**禁止**出现枚举式示例（如 `（如"X"、"Y"、"Z"等）`）。因为 v2.0 不读取 skill 02 的 repair_path，Planner 自主撰写 after 文本时须直接遵守此约束——不得产生 few-shot，必须用纯逻辑原则或 CoT 推理引导
4. **Agent 能力边界检查**：不可要求 Master Agent 直接生成业务内容（仅路由/整合），不可要求 Sub-Agent 执行 skill 范围外的任务
5. **`expected_tradeoffs` 必须具体**：不可写"可能有副作用"等空泛描述。须指出具体可能受影响的场景和预期表现变化。Executor 的 D1 算法用此字段做语义匹配，越具体越准。

   **写法对比**：
   - ❌ 空泛（D1 无法匹配）：`"修改后某些场景可能出现退化"`
   - ❌ 过宽（所有退化都能匹配，失去筛选作用）：`"Agent 回复风格可能发生变化"`
   - ✅ 具体（D1 可精确匹配）：`"延后信号内嵌于业务推进场景，若边界判断不精确，可能引入'保留价值理由'话术 → 被动回复/无效请示模式"`

   **原则**：描述退化的具体**行为模式**（"被动回复/无效请示"），而非抽象影响（"可能退化"）。

### 2.2 分流规则

将 FIX 分为两类：

**可自动优化**（纳入 Iteration 编排）：
- `target_layer` 为 P0_prompt / P1_skill / P3_orchestration
- `fix_strategy` 为 约束型修复 / 能力型修复
- 修改对象为 prompt/config 文件（如 `.md`、`.yaml`）

**需转人工工单**（输出到 `fix_tickets/`）：
- `target_layer` 为 P2_tool（需代码改动）
- `target_layer` 为 PX_eval（评估器/评测集问题，非 Agent 修复）
- `fix_strategy` 为 工程型修复 且涉及 `.py` 等代码文件改动
- 需要业务数据/知识补充（非 Agent 可自动完成）

每条人工工单遵循 `references/fix-plan-templates.md` 中的 ticket 模板。

### 2.3 Iteration 批次编排

将所有可自动优化的 FIX 编排为有序的 Iteration 批次。每个 Iteration 是 Executor 可独立评测的原子批次。

#### 编排流程

1. **收集所有自动优化 FIX**
2. **参考 Skill 2 的单 case 渐进路径**：case_report 中的修复方案通常按 Step 1（高杠杆低风险）→ Step 2 → Step 3 排列。这个自然排序是 Iteration 编排的核心参考。Planner 从全局视角合并裁剪，而非逐条照搬
3. **分组原则**：
   - 修改同一文件或逻辑相关文件的 FIX 归入同一 Iteration
   - 单个 Iteration 内的所有改动应可作为整体评测
   - **同类修改隔离**：若多个 FIX 向不同 Skill 添加相同性质的约束（如"直接行动原则"），必须每 Skill 独立为一个 Iter，禁止打包。原因：同类修改的副作用叠加会导致退化数远超单 Skill 改动，且退化无法归因到具体 Skill（Round 1/2 经验：3 Skill 同批次 → 19 条退化）
   - **单 Iter 文件上限**：≤ 3 个文件。高风险文件（router.md / profile_extraction_module.md 等 Master Agent 文件）必须单独成 Iter
4. **排序**：基础 Iteration 在前，核心 Iteration 在后

#### Iteration 标注

每个 Iteration 包含以下字段：

| 字段 | 说明 |
|------|------|
| `iter_id` | 唯一编号（iter_1, iter_2, ...） |
| `type` | `基础` 或 `核心` |
| `requires` | 硬依赖的 iter_id 列表。前置 Iter 被 ROLLBACK 时自动跳过本 Iter |
| `blocked_by_tickets` | 依赖的人工工单编号列表（如 `[ticket_001]`）。所列工单未完成时，Executor 跳过本 Iter 并标注原因。用于 tool-first/knowledge-first 原则——当 prompt 修复依赖 tool/data 前置修复时声明 |
| `fixes` | 本 Iteration 包含的 fix_id 列表 |
| `description` | 一句话描述本批次的修复目标 |
| `target_cases` | 本批次预期改善的 case_id 列表 |
| `expected_outcome` | 预期效果描述（如"router 不再跳过路由直接回复"），用于 Iteration 总览表 |

#### 类型判定规则

**基础**（Executor 退化容忍度 = 0）：
- 纯约束添加（如增加硬约束禁止某行为）
- 格式/语气规范修正
- 防御性守卫（fallback、异常处理）
- 特征：这些改动退化风险极低，但仍需通过交互效应自检（§2.6）确认不与其他 FIX 矛盾。零容忍度意味着一旦出现任何非预期退化即 ROLLBACK

**核心**（Executor 退化容忍度 = 小样本 case 数的 5%）：
- 路由逻辑变更
- Skill 内容重写
- 行为模式调整（如从直接回复改为必须调用工具）
- 特征：这些改动"主动改变 Agent 行为，可能引入预期内的权衡"

#### 依赖规则

- Iteration B 修改的文件假设 Iteration A 的修改已存在 → `requires: [iter_A]`
- Iteration B 添加的内容依赖 Iteration A 新增的约束 → `requires: [iter_A]`
- 软依赖（顺序偏好但非硬性要求）通过排序隐含，不写入 `requires`
- `requires` 依赖链不得有环
- **依赖最小化**：`requires` 仅用于文件级冲突（两 Iter 改同一文件），不用于语义级依赖（"iter_B 效果更好如果 iter_A 先上线"）。原因：`requires` 构成单点失败链——前置 Iter ROLLBACK 会级联 SKIP 所有依赖 Iter，代价极高（Round 2 经验：iter_3 ROLLBACK → iter_4 4 个 FIX 全部落空）

#### 合并检测

编排完成后检查是否有可合并的 Iteration。当 iter_i 和 iter_j 满足以下**全部**条件时，建议合并为一个 Iteration：
1. 两者互不 `requires`
2. 两者的修改文件不重叠（无冲突风险）
3. 两者均为 `type: 基础`

### 2.4 全局规则段

在 fix_plan.md 的开头，写入全局规则段：

**继承约束**：列出 repair-principles-v1.6.0.md 的 7 条硬约束（摘要形式，非全文）。标注"继承自 auto-single-case-analyzer v1.6.0 修复原则"

**增量约束**：列出本轮从 feedback 中提取的增量规则，每条标注出处频次。例如：
```
- 禁止 few-shot 枚举式表述，优先纯逻辑原则 — 出现在 8/9 条 feedback 中
- Master Agent 仅具备路由和整合能力，不应具备直接回复能力 — 出现在 3/9 条 feedback 中
```

全局规则对所有 FIX 项和所有 Iteration 生效。Executor 执行每项修改时须检查是否违反全局规则。

### 2.5 覆盖验证矩阵

在 fix_plan.md 末尾，写入覆盖验证矩阵，确保无遗漏：

| Case | Verdict | 归因根因 | 覆盖 FIX | Iteration | 状态 |
|------|---------|---------|---------|-----------|------|
| case_001 | revise | [根因] | FIX_001 | iter_1 | 已覆盖 |
| case_058 | reject | — | — | — | 不纳入（reject） |

**自检**：每个非 reject 的 case 必须至少被 1 个 FIX 覆盖。如有未覆盖的 case，须补充 FIX 或说明原因。

### 2.6 FIX 间交互效应自检

所有 FIX 生成后、Iteration 编排完成后，执行交互效应检查。此步骤是 case-level 分析方法论的关键补充——单个 FIX 各自合理，但组合执行时可能存在设计矛盾。

对每对 (FIX_i, FIX_j)，检查：

1. **路径干扰**：FIX_i 改变的路由/约束是否影响 FIX_j 的 target case 的执行路径？
   - 例：router 路由约束收紧（FIX_i）可能导致某些 turn 不再到达 FIX_j 修复的子 Agent
2. **规范矛盾**：FIX_i 新增的行为规范是否与 FIX_j 的改动存在矛盾？
   - 例：router 禁止直接回复（FIX_i）vs 子 Agent 推进约束要求主动给出方案（FIX_j）——当 router 截留消息时，子 Agent 的推进约束无法生效
3. **副作用传导**：FIX_i 的 expected_tradeoffs 是否可能导致 FIX_j 的 source_cases 退化？

如发现矛盾：
- 在 fix_plan.md 中标注 `⚠️ 交互风险: FIX_i × FIX_j: [描述]`
- 建议调整策略：将矛盾的 FIX 合并为同一 Iteration（确保原子性评测）/ 调整执行顺序 / 修改其中一方的实现层以消除矛盾

### 2.7 不动项说明

在 fix_plan.md 中显式列出 Agent 源码中**不修改**的文件及原因，防止 Executor 或 reviewer 误以为是遗漏：

| 文件 | 不改原因 |
|------|---------|
| warmup.md | 本轮无涉及该 Agent 的 case |
| planner.md | 本轮 case 未涉及行程定制专家 |

### 2.8 熔断条件与回滚策略

在 fix_plan.md 末尾输出熔断条件和回滚策略，为 Executor 提供安全网：

**熔断条件**：

| 级别 | 条件 |
|------|------|
| 通过 | target cases 改善率 ≥ 50% 且 非预期退化 ≤ 2 turns |
| 警告 | target cases 改善率 < 50% 或 非预期退化 3-5 turns |
| 熔断 | 非预期退化 > 5 turns 或 净通过率下降 |

**回滚策略**（触发熔断时按优先级执行）：
1. 回退最后执行的 Iteration（依赖链逆序）
2. 仅保留 `type: 基础` 的 Iterations
3. 完全回退到基线

**验证要点**：
- 列出 target cases 中每个 turn 的预期修复机制
- 指出需抽样回归验证的已通过 turn（特别是与改动文件相关的 turn）

---

## Step 3: Reviewer 授权审查

fix_plan.md (draft) 完成后，优先通过 Reviewer 验证方案合理性；但任何会把
fix_plan、业务上下文、代码片段、trace 摘要、评分反馈发送给外部模型或独立
Agent 的动作，都必须先经过显式人工授权。

### 3.1 授权门（强制）

执行 Reviewer 前，Planner 必须先向用户说明：

- **发送范围**：将发送哪些文件或字段（至少包括 fix_plan.md；如包含 feedback /
  attribution / trace 摘要必须逐项列出）
- **调用方式**：本地只读子进程、宿主 Agent subagent、或其他外部 reviewer
- **隐私影响**：材料可能包含业务逻辑、prompt 片段、评测结论或内部路径
- **成本/副作用**：可能产生模型调用成本、耗时、日志 artifact；默认禁止自动发布评论或修改工作树

只有用户明确同意后，才进入 §3.2；未获授权时直接生成占位
`reviewer_findings.json`（`reviewer_model: "skipped_requires_authorization"`，
`findings: []`），并在 HITL 阶段提示本轮改由人工审查。

### 3.2 适配器选择（授权后）

授权后可选择：

1. **本地只读 reviewer CLI**：只允许 read-only / no-fix / no-comment 模式；将 §3.3 的 Reviewer Prompt 写入 `{round_dir}/reviewer_prompt.md`，输出保留为审计 artifact。
2. **宿主 Agent subagent**：只在用户授权“可发送给宿主 subagent”后执行；prompt 内容使用 §3.3。
3. **skipped**：未授权或均不可用时生成占位 `reviewer_findings.json`（`reviewer_model: "skipped"`，`findings: []`），在 HITL 阶段提示用户。

不需要 `scripts/reviewer_adapters/` 下的脚本文件——Reviewer 调用属于宿主
Agent 环境能力，不进入本仓库公开代码。

### 3.3 Reviewer Prompt

向 Reviewer 发送以下 prompt：

```
## 任务

审查以下修复方案（fix_plan.md），从独立视角验证其合理性。

## 审查维度

1. **逻辑一致性**：FIX 项之间是否存在矛盾？一个 FIX 的 after 是否可能破坏另一个 FIX 的意图？
2. **expected_tradeoffs 完整性**：每个 FIX 的预期副作用是否充分描述？是否存在未声明的潜在风险？
3. **约束遵守**：所有 FIX 的 after 内容是否遵守全局规则段的约束？是否存在 few-shot 残留？
4. **Iteration 编排合理性**：基础 Iter 是否在核心 Iter 之前？requires 依赖是否合理？是否有可以合并或需要拆分的 Iteration？
5. **覆盖遗漏**：是否有 adopted case 未被任何 FIX 覆盖？是否有明显的修复遗漏？

## 输出格式

对每个发现，输出一条 finding（所有字段必填）：
- id: RF_001, RF_002, ...
- severity: high / medium / low / info
- target_fix: 相关的 FIX 编号（如 FIX_003），或 "global" 表示全局问题
- target_iteration: 相关的 Iteration 编号（如 iter_2），或 null
- category: 逻辑冲突 / 约束违反 / 覆盖遗漏 / 副作用风险 / 编排问题
- finding: 问题描述
- recommendation: 建议的修改方式
- adopted: null（初始值，HITL 阶段由用户标记 true/false）

## 审查材料

{fix_plan.md 全文}
```

### 3.4 结果处理

Reviewer 返回的 findings 写入 `reviewer_findings.json`（格式见 `references/fix-plan-templates.md`）。

对 severity 为 `high` 的 finding：
- 在 fix_plan.md (draft) 中对应 FIX 旁标注 `⚠️ Reviewer 发现: [finding 摘要]`
- 在 HITL 阶段引导用户重点关注

---

## HITL: 方案 review

**位置**：fix_plan.md (draft) + reviewer_findings.json 产出后，作为 skill 的最后一步执行。

**Step A: 自行处理 Reviewer findings**

Reviewer findings 产出后，Planner **自行处理** severity 为 high 和 medium 的 finding：
1. 根据 finding 的 recommendation 调整 fix_plan.md 中受影响的 FIX/Iteration
2. 将处理结果记录到 `reviewer_findings.json` 的 `adopted` 字段（`true` = 已采纳修改，`false` = 不采纳并说明原因）
3. 在 fix_plan.md 末尾的「改动日志」中记录每项改动

**Step B: 展示给用户**

使用 AskUserQuestion 向用户展示处理后的方案：

```
## 修复方案审批

已生成 fix_plan.md (draft)，包含：
- N 个自动优化 FIX 项，编排为 M 个 Iteration
- K 条人工工单
- Reviewer 发现 X 条 finding，已自行处理 Y 条（见改动日志）

### 全局规则摘要
[列出增量约束]

### Iteration 编排总览
[Iteration 总览表]

### 改动日志（Reviewer 处理）
[列出已处理的 finding 及改动]

请选择：
(a) 直接通过 → 标记为 approved
(b) 修改建议 → 请指出需调整的 FIX 编号和修改意见
```

当 `reviewer_model` 为 `"skipped"` 时，额外提示：
```
⚠️ 未配置或未授权 Reviewer。
建议在确认发送范围、调用方式、隐私影响与成本后，再配置只读 reviewer。
本次方案由用户人工审查。
```

**Step C: 处理用户反馈**

- **(a) 直接通过**：将 fix_plan.md 状态标记为 `approved`
- **(b) 修改建议**：根据用户意见调整 fix_plan.md，并在「改动日志」中追加记录。修改范围：
  - 可修改实现层（before/after、fix_location）
  - 可修改 Iteration 编排（调整顺序、合并、拆分）
  - 可将自动优化项转为人工工单
  - **不可删除意图层已确定的根因和目标**（除非用户明确要求）
  - 修改完成后**重新执行质量自检（10 项）**，确保改动未引入新问题
  - 重新展示，直到用户确认通过

**改动日志格式**（追加在 fix_plan.md 末尾）：

```markdown
## 改动日志

| 来源 | 改动 | 原值 | 新值 |
|------|------|------|------|
| Reviewer RF_001 (high) | FIX_003 after 文本清理 fewshot | "如X、Y..." | 纯逻辑原则 |
| HITL 用户评论 | iter_2 合并至 iter_1 | 独立 Iteration | 合并 |
```

**输出**：`fix_plan.md (approved)`（含改动日志）+ `reviewer_findings.json`（每条 finding 标记 `adopted: true/false`）

---

## 回流场景处理

当 round > 1（从 Skill 4 回流重新制定方案）时，Step 1-2 的行为有以下调整。

### 回流基线原则

Planner **始终基于 baseline Agent 源码**制定方案（`agent_files_path` 指向的版本），不基于上轮修改后的 agent 文件（`{round_dir}/execution/new_agent_files/`）。这与 CONTRIBUTING.md 的 Baseline Evolution Flow 一致：实验在同一 baseline 上进行多轮优化，直到人工决策 merge 形成新 baseline。

### 回流输入（round > 1）

除常规输入外，额外读取历史 round 产物（v3.3 路径：`{experiment_root}/rounds/`；legacy：`{analysis_root}/iterations/`）：

| 物料 | 来源 | 用途 |
|------|------|------|
| 上轮 `fix_plan.md` | `round_N/` | 了解"试过什么"——避免重复无效策略 |
| 上轮 `optimization_report.md` | `round_N/` | 了解"效果如何"——退化归因、有效改动 |
| 上轮 `progressive_log.json` | `round_N/execution/` | 了解每个 Iter 的 D1/D2 结果 |
| `lessons_learned.md` | `iterations/` | 历史教训清单（如存在） |
| 上轮 `new_agent_files/` | `round_N/execution/` | **不读取**——Planner 始终基于 baseline |

### 多轮经验回溯策略

当 `{experiment_root}/rounds/`（或 legacy `{analysis_root}/iterations/`）下存在多个 `round_N` 目录时：

1. **最近一轮（round_N）**：完整读取 `fix_plan.md` + `optimization_report.md` + `progressive_log.json`
2. **更早轮次（round_1 ~ round_N-1）**：仅读取每轮 `optimization_report.md` 的「总览指标」和「退出判断回顾」章节，提取每轮的净效果和关键教训
3. **经验聚合**：将所有轮次的教训合并，更新「历史教训清单」

### 历史教训清单维护

文件位置（v3.3 新结构）：`{experiment_root}/lessons_learned.md`（experiment 内累积）。跨 experiment 的长期教训归入 `projects/<biz>/evoloop/knowledge/lessons_learned.md`，由维护者从 experiment lessons 手工提炼。

Legacy（v3.2）位置：`{analysis_root}/iterations/lessons_learned.md`。

**生命周期**：
- Round 1（首轮）：不产出此文件（无历史可回溯）
- Round 2+（回流）：Planner 在 Step 1 回流阅读完成后，创建或追加更新此文件
- 此文件跨轮次累积，是所有历史教训的唯一汇总点

**内容结构**：

```markdown
# 历史教训清单
> 最后更新: round_N, YYYY-MM-DD

## 已验证有效的策略
| 策略 | 验证轮次 | 证据 |
|------|---------|------|
| router 路由硬约束强化 | round_1 iter_1 COMMIT | target 3/3 改善，无退化 |

## 已证明无效的策略（禁止重复）
| 策略 | 失败轮次 | 失败原因 |
|------|---------|---------|
| P0 硬约束全面降级 | round_1 iter_3 ROLLBACK | 与 P1 子Agent推进矛盾，净退化 22 turns |

## 反复出现的退化模式
| 模式 | 出现轮次 | 防范措施 |
|------|---------|---------|
| router 截留导致子Agent推进失效 | round_1, round_2 | 交互效应自检必须覆盖路由×推进组合 |
```

**更新规则**：
- 每轮 Planner 读取上轮 optimization_report 后，将新发现追加到对应表格
- 已有条目不删除，只追加或标注"已解决"
- Planner 在方案制定（Step 2）时将此清单作为约束输入——有效策略可延续，无效策略禁止重复

### Step 1 调整

- 读取历史产物（见上方"回流输入"表和"多轮经验回溯策略"）
- 更新或创建 `lessons_learned.md`
- 在设计新 FIX 时，检查是否与上轮已验证有效的改动冲突
- **禁止重复无效策略**：`lessons_learned.md` 中"已证明无效"的策略不可原样重复，必须换方向

### Step 2 调整

- **保留有效修复**：上轮 COMMIT 的 Iteration 对应的 FIX 不再重复，其改动视为已生效的基线
- **重制失败项**：上轮 ROLLBACK 的 Iteration 需要重新制定方案：
  - 分析 ROLLBACK 原因（非预期退化 / target 无改善）
  - 可选策略：降级改动范围、拆分为更小的 Iteration、转为人工工单
- **新增约束**：从上轮退化归因中提取教训，添加到本轮全局规则的增量约束中
- **Iteration 编号延续**：如上轮最后一个 Iteration 是 iter_5，本轮从 iter_6 开始

---

## 质量自检

fix_plan.md (draft) 产出后、Reviewer 调用前，执行以下自检：

1. **覆盖完整性**：每个非 reject 的 adopted case 是否至少被 1 个 FIX 覆盖（通过 source_root_causes）？
2. **expected_tradeoffs 非空**：每个 FIX 的 `expected_tradeoffs` 是否有具体内容（非空泛描述）？
3. **分类合规**：每个 FIX 的 `fix_strategy` 和 `target_layer` 是否来自 `attribution-framework.md` v6 的枚举值？
4. **源码真实性**：实现层的 `before` 字段是否来自 Agent 真实源码（非编造）？
5. **全局规则完整**：全局规则段是否包含 repair-principles 基线的 7 条硬约束？
6. **revision 优先**：`verdict: "revise"` 的 case 是否以 `revision` 字段为准，而非原始报告？
7. **Iteration 排序**：基础 Iteration 是否排在核心 Iteration 之前？
8. **依赖无环**：`requires` 依赖链是否无环？
9. **Anti-Few-shot 合规**：所有 FIX 的 `after` 字段中是否不含：(a) 枚举式示例（`如X、Y、Z等`）；(b) 引号包裹的具体话术示例（`"我先给您出个参考方案"` 等直接对话文本）。如需表达行为原则，应使用抽象逻辑描述而非具体话术
10. **人工工单覆盖**：所有无法自动优化的 FIX 是否已输出为 `fix_tickets/` 工单？
11. **体积控制**：fix_plan.md 总长度是否 < 500 行？`before` 字段是否使用定位描述（非全文粘贴）？若超出，精简 before 至"文件路径 + 段落标题 + 关键行"。
12. **v2.1 独立推导合规**：每个 FIX 是否填写了 `derivation_note`？推导链是否从 root_causes 的 (component, rule_violation) 与 description / evidence 语义出发，而非引用 skill 02 的 `fix_step1_*` 或 `repair_path.steps[]`？是否完全没有引用已废弃的 stage / mode 字段？
13. **v2.0 归因字段完整**：是否所有 case 都只从 summary JSON 读取了 (scope, root_causes, causal_edges) 字段？是否有 FIX 的推理依赖了 skill 02 的修复建议？
14. **v2.0 external 分流**：scope=external 的 case 是否已转为评测集/评估器工单（不进入 FIX 生成）？
15. **schema 2.2 兼容**：feedback.json 是否通过 `schema_version === "2.2"` 校验？是否对所有 `verdict='reject'` 的 case 一律跳过修复流程（不再细分 scorer_misjudge）？是否完全没有读 `scorer_feedback` 字段？同 group_id 的 case 是否在 §1.5 §"合并 group"中以最高优先级聚类？

---

## 话术风格

与 auto-single-case-analyzer 一致：

- **术语中文化**：英文术语首次出现给中文对照，后续用中文
- **避免自造概念**：用平实因果链描述根因聚合和修复逻辑
- **before/after 原文**：fix_plan 中的 `before` / `after` 片段保持 Agent 源码原文，不做语言转换
- **Iteration 描述具体化**：每个 Iteration 的 description 须包含"改什么"+"改的方向"，不可只写"优化 router"

---

## 环节结束提醒

当 HITL 审批完成、`fix_plan.md (approved)` 已写入后，**必须**向用户展示以下后续操作指引：

```
✅ 修复方案已生成并通过审批！

📂 产出物：
- fix_plan.md (approved) — N 个 FIX，编排为 M 个 Iteration
- reviewer_findings.json — Reviewer 审查结果
- fix_tickets/ — K 条人工工单

📋 后续操作：
1. 输入 /compact 压缩当前上下文（推荐）
2. 启动 auto-fix-executor 执行修复方案
3. 或将 fix_tickets/ 中的工单分配给团队成员处理
```
