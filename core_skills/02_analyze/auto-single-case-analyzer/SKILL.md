---
name: auto-single-case-analyzer-v1.9.0
version: 1.9.0
description: >
  核心归因引擎——对单个 case 进行 trace 级深度归因分析，输出归因报告和结构化摘要。
  支持两种分析模式：Mode A 直接归因（单条 trace）和 Mode B 对比归因（同一 case 的两版本 trace 配对）。
  分析完成后自动生成反馈查看器（feedback_viewer.html），供 HITL 2 结构化反馈使用。
  所有输入从 analysis_manifest.json 读取，skill 内部不设 HITL 关卡。

  v1.5.0：渐进式修复路径生成（基于根因链设计最小改动路径）、三维优先级评分、
  工程层修复内容分级、修复策略优先级指导（基于人工反馈校准）。

  v1.6.0：修复内容生成硬约束（anti-few-shot、agent 能力边界、路由优先、知识优先、
  工具优先、Step 1 充分性、新 Skill 门槛），增强评估器审视机制，问题解决完整度加权，
  修复原则策略独立文档（供下游 summary 阶段使用）。

  v1.7.0 重构归因链路：引入 `component`（位置维度）作为归因链路第一环，
  `target_layer` 从归因阶段移出，仅保留在修复规划阶段。

  v1.8.0 归因框架正交化：废弃 F1–F11 failure_type 枚举，替换为 (stage × mode × rule_violation)
  正交字段体系，消除消歧条款。eval 从 component 枚举移出为 scope=external（人工回流）。
  归因阶段输出多根因数组 + causal_edges 因果图，不再区分主/次归因。

  v1.9.0 归因字段简化：移除 stage（认知阶段）与 mode（差异模式）两个枚举字段，
  归因结构维度坍缩为 (component, rule_violation)。失败的认知阶段语义和集合差类型语义
  下沉到 description / evidence 自由文本，由 LLM 根据 trace 实录直接判断，不再强制走
  固定枚举——目的是降低 subagent 的字段判定负担，将判断重心放回到 trace 事实本身。
  下游 planner v2.1 同步更新聚类算法（基于 component 结构共性 + description 语义聚类）。

  当用户提到以下任何场景时务必触发此 skill：
  分析这条 badcase、trace 归因、根因分析、为什么 agent 回答错了、
  执行链路分析、工具调用链路复盘、LLM 决策归因、badcase 根因定位、
  agent 失败案例溯源、深度分析 trace。

  与 auto-trace-prep 的边界：auto-trace-prep 负责物料准备，本 skill 负责归因分析。
  与 auto-case-summary 的边界：本 skill 输出单 case 归因报告，auto-case-summary 负责跨 case 汇总。
---

# Single Case Analyzer

对单个 case 进行 trace 级深度归因分析，输出结构化的 Markdown 报告和 JSON 摘要。

## 输入

| 物料 | 必选 | 说明 |
|------|:----:|------|
| analysis_manifest.json | ✅ | 从 auto-trace-prep 产出 |
| case_id | ✅ | 指定要分析的 case |
| mode | ✅ | `direct`（直接归因）或 `compare`（对比归因） |

Skill 从 manifest 中读取该 case 的 trace 路径、评测行数据、harness 路径。**不需要其他参数**——所有信息已在 manifest 中。

## 输出 Artifact

```
{analysis_root}/
├── _s2_execution_plan.json        # S2 执行模式与授权审计（S2 开始时写入）
├── feedback_viewer.html           # HITL 2 结构化反馈查看器
└── reports/
    ├── case_report_{case_id}.md       # 完整归因报告（人可读）
    └── case_summary_{case_id}.json    # 结构化摘要（机器可读）
```

---

## 两种分析模式

### Mode A: 直接归因（单条 trace）

核心归因流程：Phase 2 → Phase 3 → Phase 4 → Phase 5（见下方详细说明）。

### Mode B: 对比归因（同一 case 的两个版本 trace）

分析单元从"单条 trace"变为"baseline vs modified trace 配对"。核心差异：

1. **双链路对照还原**：并列展示两条链路的时间轴，标注分叉点
2. **分叉点逐层归因**：聚焦在两版本行为不同的节点上——为什么 baseline 做对了但 modified 做错了（或反之）
3. **修复方案**：针对退化原因或提升原因给出方案
4. **报告生成**：输出统一格式的报告

两种模式的报告使用**统一的输出格式**，下游（HITL 反馈 + auto-case-summary）不需要区分来源。

---

## Phase 2：Trace 解析 & 执行链路还原

目标：把 trace 数据转化为**纯事实性**的结构化调用表。本阶段只描述发生了什么，不解释为什么——所有根因推断留到 Phase 3。

> ⚠️ **事实性要求**：Phase 2 中禁止出现"可能的原因是"、"这说明"、"归因为"、"推测"等主观推断语言。如果某个行为看起来异常（如输出 token 极少），只做客观记录（标 ⚠️），不做解释。

**如果拿到的是 analysis 格式**（`_meta` + `context` + `call_graph`），核心解析工作已由脚本完成。直接从 `call_graph` 读取调用树，渲染为调用表。

**如果拿到的是 fetch_and_clean beta 格式**（`id` / `sessionId` / `root.input` / `root.output` / `root.steps`，viewer 中标记为 `langgraph-clean`），从 `root.steps` 递归读取执行节点；从 `root.input.messages` 与 `root.output.messages` 还原上下文；从各节点的 `usageDetails`、`response_metadata.token_usage`、`tool_calls`、`calculatedTotalCost` 等字段提取 token、工具调用和成本摘要。该格式已经过五步清洗，不再包含顶层 `observations` 列表。

**如果拿到的是 raw 格式**（`trace` + `observations`），需要分步解析：

1. 先读取顶层结构，确认 `trace` 和 `observations` 两个主键
2. 从 `trace` 中提取 metadata（agent 版本、session_id、总延迟、input/output）
3. `trace.input` 和 `trace.output` 可能是双重 JSON 编码（字符串里套字符串），用 `json.loads` 逐层解析
4. 遍历 `observations` 列表，按 `startTime` 排序，提取每个节点的 type、name、parentObservationId、latency、toolCalls、toolCallNames、toolDefinitions、model 等字段
5. 重点关注：GENERATION 节点（LLM 调用）和 TOOL 节点（工具调用），它们构成分析的核心素材

注意：TraceBackend 的 observation 中 `input` 和 `output` 字段可能为空（取决于导出配置），这时要从 `toolCalls`（GENERATION 节点的工具调用参数）和 trace 层的 `output`（最终状态）来还原数据流。

**输出格式**——结构化调用表，分一级/次级信息：

**一级信息（必须展示，纯事实）**：

| 步骤 | 节点名称 | 类型 | 关键输出 | 异常 |
|------|---------|------|---------|------|
| S1 | master LLM #1 | GENERATION | tool_call: handoff_to_agent("子agent名") | — |
| S2 | 子agent LLM #1 | GENERATION | tool_call: quotation({参数摘要}) | — |
| S3 | quotation | TOOL | 返回: {关键字段摘要，如价格/ID/链接} | — |
| S4 | 子agent LLM #2 | GENERATION | 输出: {前100字或"近乎空"} | ⚠️ output=6 token |

- **节点名称**：agent 名称 + LLM 轮次编号（如"master LLM #2"）或工具名
- **类型**：GENERATION（LLM调用）/ TOOL（工具调用）/ SKILL（skill调用）
- **关键输出**：工具调用参数摘要、工具返回关键值、LLM输出前100字；若输出空/异常则标注实际情况
- **异常**：用 ⚠️（异常但未失败）/ ❌（明确失败）标记，只写观察到的事实

**次级信息（括号标注，视情况展示）**：耗时、input/output token 数。当 token 数异常时（如 output 远低于 input）应展示以便 Phase 3 参考。

**附：执行统计摘要**（表格末尾）：

```
总耗时: Xs | LLM调用: N次 | 工具调用: N次 | 模型: xxx
```

### Mode B 适配：并排执行链路还原

不再是还原一条执行链路，而是**并排还原多版本链路**，重点标注分叉点。

V1 和 V2 各用一张调用表（格式与 Mode A 相同），然后单独标注分叉点：

**🔴 分叉点**：V1步骤S_X vs V2步骤S_X —— [第一个行为不同的节点]

**分叉点识别策略**：不按时间轴硬对齐，而是按**语义决策点**对齐——找到第一个"输出开始不同"的位置，然后向上追溯各自的决策链路，定位导致分叉的根因节点。

---

## Phase 3：根因分析

这是报告的核心。沿着 Phase 2 还原的执行链路，逐层分析每个决策节点的行为是否合理，并输出结构化归因分类。

### 归因分类框架

> 归因分类框架（scope / component / rule_violation / target_layer / fix_strategy 完整定义）见 `references/attribution-framework.md` v6。
> subagent 分析前**必须**先完整读取该文件，不得使用 prompt 中可能存在的任何简写或枚举列表替代。

本阶段遵循 Badcase 归因分类框架 v6，每条 badcase 按以下结构输出：

```yaml
scope: in_agent | external

# scope=in_agent 时：输出 root_causes 数组
root_causes:
  - id: rc_1
    component: agent:{name} | tool:{name} | memory
    rule_violation: true | false
    rule_ref: null                   # rule_violation=true 时必填
    trace_refs: [{step_id, span?}]   # 必填，定位 trace 节点
    description: string              # 错是什么 + 失败语义概括（哪个认知阶段的 missing/wrong/excess）
    evidence: string                 # 为何判错（引用 trace 原文）

causal_edges: [{from: rc_id, to: rc_id}]  # 有因果关系时填写

# scope=external 时：
external_reason: string
hitl_ref: string
```

> ⚠️ **Phase 3 不输出 `target_layer`，不区分主/次归因**。归因只做因果枚举，修复的锚点选择由 Phase 4 基于 ROI/杠杆率独立决策。
>
> ⚠️ **v1.9.0 简化**：归因不再输出 `stage` / `mode` 枚举字段。失败发生在哪个认知阶段（comprehend/retrieve/act/synthesize）以及属于何种集合差类型（missing/wrong/excess）必须以**自然语言**写入 `description`——下游聚类、Phase 4 修复规划均依赖 description 语义判断。**description 写不到位会让下游聚类降级**。

### 归因判定流程

1. **第一步：scope 分流（agent 初判 + HITL 终判）**
   - 先审视评估器的评分理由：评估器指出的问题是否在 Trace 中可观测？评估器的"期望输出"是否合理？
   - 如果评估器评分理由与 Trace 实际行为存在矛盾，标记 `scope=external`，填写 `external_reason` + `hitl_ref`，**不输出** `root_causes` / `causal_edges` / `fix_step1_*` / `repair_path` 等修复流程字段，不进入后续步骤
   - 否则标记 `scope=in_agent`，继续以下步骤
   - **agent 的 scope 输出是初判**：最终是否归为 external 由 PE 在 HITL 阶段确认或覆盖（PE 也可将 agent 标为 in_agent 但实际是评估器问题的 case 通过 reject 反向回流，反之亦然）。详见 `references/attribution-framework.md` §零

2. **第二步：枚举所有独立失败节点**
   - 沿 Phase 2 执行链路逐节点检查，对每个节点问：**"如果 agent 在这一步做了正确判断，错误能不能被拦截？"**
   - 能拦截 → 该节点是独立失败节点，记一条 root_cause
   - 不能拦截（信息/能力根本没给）→ 该节点是上游症状，归因到上游即可
   - LLM agent 每个节点都有自主推理能力，下游失败通常是独立的
   - 对每个独立失败节点，依次填写：
     - **`component`**：问题在哪个位置（agent:{name} / tool:{name} / memory）
     - **`rule_violation`**：是否违反明确规则（true / false）；若 true 则填 `rule_ref`
     - **`trace_refs`**：定位到具体 trace step（step_id + 可选 span）
     - **`description`**：错是什么 + 失败语义概括——必须用自然语言说明该节点（a）在哪个认知阶段失败：comprehend（任务理解）/ retrieve（信息检索）/ act（工具调用）/ synthesize（结果整合），四选一；（b）属于何种集合差类型：missing（漏做）/ wrong（做错）/ excess（多做），三选一。例如"master agent 在意图理解阶段漏掉时间维度判断（comprehend 阶段 missing）"
     - **`evidence`**：为何判错（引用 trace 原文）

3. **第三步：记录因果关系**
   - 对独立失败节点之间有上下游传导关系的，填写 `causal_edges`
   - 并列失败（互相独立共同导致最终错误）不填 causal_edge，两条独立 root_cause 即可

---

**逐节点归因输出格式**：

```
#### [节点名称]（步骤S_N）

**组件**：`agent:{name}` （或 `tool:{name}` / `memory`）
**规则违反**：`true/false`（若 true：rule_ref）

[Trace实录] 观察到的具体行为或输出片段。
[Prompt推断] 对照规范的缺口（有 Harness 时填，无则省略此行）。
description：[错是什么 + 失败语义概括（认知阶段 + missing/wrong/excess），一句话]
evidence：[为何判错，引用 trace 原文]
```

**信源标注规则**（必须在每条描述后标注）：
- `[Trace实录]` ——可以从 trace 中直接观察，是事实
- `[Prompt推断]` ——基于 Harness 中的 prompt 条款推断，有文本依据
- `[假设]` ——无法从当前物料确认，仅作为可能方向

**禁止**：在归因节中重述 Phase 2 已有的执行细节。归因只写决策判断和失效原因，不重复链路。

**根因总结**：

```
**根因链**：rc_1（[节点A的问题]）→ rc_2（[节点B的问题]）→ 最终错误输出
（并列失败用 + 连接：rc_1 + rc_2 → 最终错误）

**一句话总结**：[用一句话概括核心失效路径]
```

**如果没有 Agent Harness**：归因聚焦在 trace 实录层面，推断性内容标注 `[假设]`。

### Mode B 适配：差异归因

配对模式下，归因的核心问题从"这一步为什么错了"变为"**这一步在两个版本间为什么不同**"。

每一层的分析模板变为：

```
#### 分叉点 N：[节点名称]（V1:S_X vs V2:S_X）—— [一句话差异描述]

**V1 行为**：[V1 在这个节点做了什么] `[Trace实录]`
**V2 行为**：[V2 在这个节点做了什么] `[Trace实录]`

**差异来源**（按可能性从高到低排查）：
1. **Prompt 变更** `[Prompt推断]`：V1 和 V2 的 prompt 在这个节点是否有差异？
2. **上游输入差异** `[Trace实录]`：到达这个节点时，输入是否已经不同？
3. **工具/架构差异** `[Trace实录/假设]`：工具或 agent 拓扑是否不同？
4. **随机性** `[假设]`：概率较低，但需排除

**失效原因**（针对 fail 版本，标置信度）：
- 假设A（置信度：高）：... `[Prompt推断]`
```

**Harness diff 相关度**（必须在配对报告的根因分析末尾标注）：

```
**Harness diff 相关度**：高 / 中 / 低

- 高：此 case 的根因与 diff 直接重合
- 中：diff 是贡献因素之一，但非主因
- 低：此 case 的失效与 diff 无关，是两版本共有问题
```

相关度为**中/低**时，不在本 case 报告中展开 diff 分析——diff 的系统性影响在 auto-case-summary 的汇总报告中统一分析。

---

## Phase 4：修复方案

> **核心理念转变**：根因分析是问题诊断，修复路径是解决方案设计——两者解耦，不需要一对一绑定。
> 修复路径的生成应基于根因链的因果关系，识别杠杆点，设计最小改动路径，而非机械地为每个根因生成独立方案。

### 渐进式修复路径生成

**生成原则**：

1. **分析根因因果关系**：从 Phase 3 的根因链中识别上下游关系
2. **识别杠杆点**：找到改动小、覆盖广的修复点——修复一个根因可能连带消除其下游根因
3. **设计渐进式路径**：从杠杆点开始，设定触发条件（何时需要下一步）
4. **优先低成本修复**：Skill/工具层优先于 Prompt 约束堆砌

### 修复内容生成硬约束（v1.6.0 新增）

以下约束适用于 Phase 4 生成的所有修复内容（Before/After 文本、修复动作描述）。违反任一条即为不合格输出。

#### 约束 1：禁止 Few-shot 表述（最高优先级）

修复内容中 **严禁** 包含以下模式的文本：
- `（如"X"、"Y"、"Z"等）` 形式的举例枚举
- `禁止使用"X"..."Y"...等表达` 形式的具体话术列举
- `示例：用户说"X" → 回复"Y"` 形式的输入输出示例对

**为什么禁止**：Few-shot 示例让 agent 过拟合到具体表述，丧失泛化能力。COT 逻辑引导 agent 理解"为什么"，few-shot 只教 agent 记住"是什么"。

**替代策略层级**（严格按顺序尝试，只有上层确认不可行时才降级到下层）：
1. **纯逻辑原则**：用抽象的因果推理描述行为规则。如：将 `禁止使用"要不给您看看"等请示式表达` 改为 `当用户已表达明确意向时，直接推进执行流程，不以疑问句征求许可`
2. **COT 推理引导**：用思维链引导 agent 自行推导正确行为。如：`判断标准：用户最近一轮是否包含明确的行动诉求或确认 → 若是，则当前任务为执行而非确认`
3. **最后手段——受控 Few-shot**：仅当以上两层均无法表达时，允许使用 few-shot，但必须在修复内容中标注 `[Few-shot 兜底]` 并说明为何逻辑原则不足以概括

**自检方法**：生成 After 文本后，检查是否存在 `（如"` 或 `"、"` 或 `示例：...→` 模式。若命中，必须重写。

#### 约束 2：Agent 能力边界感知

生成修复方案前，必须先确认目标 agent 节点的架构角色：
- **Master Agent**：仅具备路由（routing）和整合（aggregation）能力，**不具备**直接回复/内容生成能力
- **子 Agent（Skill Agent）**：具备其 skill 范围内的内容生成能力
- **工具**：执行特定功能，无决策能力

修复方案不得要求某 agent 执行其架构角色之外的功能。如果修复方案建议 Master 直接生成回复内容，该方案不合格。

#### 约束 3：路由/编排优先原则

生成修复路径前，执行以下预检：
1. 对于当前 case 的失效场景，现有 agent 架构中是否已有可胜任的子 Agent？
2. 如果有 → Step 1 必须是编排层/路由修复（确保正确路由到该子 Agent），而非在 prompt 层添加新能力
3. 仅当确认没有合适的现有子 Agent 时，才考虑 Skill 内容修复或新建 Skill

#### 约束 4：知识/数据优先于逻辑约束

修复路径必须遵循以下顺序：
1. **数据/知识完整性**：先检查知识库或工具返回数据是否缺失。如果缺失，Step 1 应为补充数据
2. **逻辑/原则约束**：仅当数据完整但 agent 仍未正确使用时，才添加推理逻辑或原则约束
3. **具体描述/few-shot**：仅当逻辑约束不生效时（需有证据），才考虑更具体的描述

#### 约束 5：工具优先于 Prompt 方案

对于以下类型的问题，修复方案必须首先考虑工具侧解决：
- 计算类问题 → 计算器工具，不依赖模型计算
- 数据查询类 → 数据库/API 工具，不依赖模型记忆
- 格式转换类 → 格式化工具，不依赖 prompt 约束

仅当工具方案不可行（如开发成本过高、无对应工具基础设施）时，才降级到 prompt 层面修复。

#### 约束 6：Step 1 充分性原则

Step 1 必须被设计为 **独立充分的解决方案**——仅执行 Step 1 即应能解决或显著缓解该 case 的核心问题。Step 2 和 Step 3 是备选/加固方案，不是 Step 1 的必要补充。

评判标准：如果仅执行 Step 1 无法解决问题的核心根因，则说明 Step 1 的优先级评估有误，需要重新排序。

#### 约束 7：新 Skill 创建门槛

仅当同时满足以下条件时，才建议"新建 Skill"：
1. 高频/高普适性：该场景在多个 case 中反复出现
2. ROI 合理：新 Skill 的开发和维护成本低于在现有 Skill 中增强能力
3. 能力边界清晰：新 Skill 与现有 Skill 无重叠

否则，优先建议"增强现有 Skill 能力"。如果无法从当前单 case 判断是否高频，应在修复方案中标注 `[建议下游汇总时评估频次]`，将判断权移交给 auto-case-summary 阶段。

### 修复策略优先级（基于人工反馈校准，v1.6.0 更新）

| 优先级 | 策略 | 说明 |
|--------|------|------|
| **高** | 工具/架构修复 | 计算、查询、格式等问题优先从工具视角解决 |
| **高** | 补充知识库/数据 | 先确保数据完整，再考虑逻辑约束 |
| **高** | 编排层/路由修复 | 已有能力但未利用 → 修复路由，不修复内容 |
| **高** | 优化 Skill / Skill description | 增强现有 Skill 能力或改善触发条件 |
| **中** | 纯逻辑原则声明 | 用抽象因果逻辑概括行为，禁止 few-shot 枚举 |
| **中** | 架构层调整 | 结构化 memory、状态管理优化 |
| **低** | Prompt 约束堆砌 | 在 prompt 层面增加约束/强调 |
| **禁止** | Few-shot 示例 | 默认禁止；仅当纯逻辑原则确认不可行且标注 `[Few-shot 兜底]` 时例外 |
| **禁止** | 强调/加粗/重复声明 | 不符合最佳实践 |

### 三维优先级评分

每个修复步骤按以下三维度评估，计算优先级分数：

```
Priority Score = 杠杆率 × 成本分 × 确定性分
```

| 维度 | 定义 | 评分标准 |
|------|------|---------|
| **杠杆率** | 单次修复可能覆盖的根因数量 | 高(3)：覆盖≥2个根因；中(2)：覆盖1个；低(1)：仅缓解 |
| **成本分** | 修复的实施成本 | 低(3)：Skill/工具优化；中(2)：Prompt 原则声明；高(1)：架构改动 |
| **确定性分** | 修复效果的可验证程度 | 高(3)：可即时测试；中(2)：需部署后验证；低(1)：难以验证 |

#### 补充维度：问题解决完整度加权（v1.6.0 新增）

在计算 Priority Score 后，追加以下校验：
- 如果该 Step 覆盖的根因全部是次要根因（非根因链的起始节点），则 Priority Score 乘以 0.5 的衰减系数
- 如果该 Step 仅能解决问题的部分症状（即单独执行无法让 case 通过评测），且其覆盖的不是根因链头部节点，则不应排在 Step 1

**评判方法**：对每个 Step，问"如果只做这一步，问题能解决吗？"
- 能 → 候选 Step 1
- 不能，但处理的是根因链头部 → 候选 Step 1（因为后续根因可能连锁消解）
- 不能，且处理的是根因链尾部 → 降级到 Step 2 或 Step 3

### 工程层修复内容分级

| 层级 | 输出级别 | 内容要求 |
|------|---------|---------|
| P3_orchestration（架构层） | **L2 具体方案** | 状态流转规则、路由逻辑、映射关系、验证条件 |
| P2_tool 架构层（Schema 重设计） | **L2 具体方案** | Schema 结构变更、参数调整 |
| P2_tool 数据层（知识库等） | **L3 需求描述** | 缺失内容描述、补充方向（真实数据需业务方提供） |

**L2 具体方案输出格式**（架构层）：

```markdown
### 问题定位
- 组件：[状态管理模块 / 路由引擎 / 工具执行器 / ...]
- 现象：[动态上下文 [已收集信息] 为空]
- 期望：[应从 context.metadata 同步到 Dynamic Context]

### 修复规格
- 输入：context.metadata.leadDetail
- 输出：Dynamic Context.[已收集信息]
- 映射规则：
  - leadDetail.出发城市 → 出发地
  - leadDetail.目的地 → 目的地
  - leadDetail.成人人数 + 儿童人数 → 出行人数

### 验证条件
- 当 leadDetail 非空时，[已收集信息] 应预填充
- 可通过 Trace 中 Dynamic Context 快照验证
```

**L3 需求描述输出格式**（数据层）：

```markdown
### 问题定位
- 组件：[知识库 / 工具返回数据]
- 缺失内容：[XX 场景下的处理话术 / XX 产品的价格数据]

### 补充方向
- 需要业务方提供：[具体数据类型描述]
- 预期效果：[补充后 Agent 应能正确响应 XX 场景]
```

### 报告输出结构

**4.1 根因汇总**

| ID | 根因 | 组件 | 规则违反 |
|----|------|------|---------|
| RC1 | [根因标题] | [component] | [true/false] |
| RC2 | [根因标题] | [component] | [true/false] |

**根因链**：RC_X → RC_Y → 最终错误输出

**4.2 渐进式修复路径**

| Step | 修复动作 | 覆盖根因 | 优先级 | 触发条件 |
|------|---------|---------|--------|---------|
| 1 | [修复动作描述] | RC1, RC2 | [分数] | 默认执行 |
| 2 | [修复动作描述] | RC1 | [分数] | Step1 后仍有问题 |
| 3 | [修复动作描述] | RC3 | [分数] | 多 case 反复出现 |

> 优先级 = 杠杆率(1-3) × 成本分(1-3) × 确定性分(1-3)

**Step N 修复内容**（每个 Step 单独展开）：

```
修复方向：[target_layer] · [fix_strategy]
具体手段：[从矩阵选取]
修复位置：[harness标题 或 工程组件]

Before: [原文/现状描述]
After: [修改后内容]
```

**验证方式**：[如何验证此步骤的修复效果]

### 验证用测试case 格式

表格后逐条提供：

```
**TC1（验证 Step N）**

metadata：
```json
{
  "businessId": "可为空",
  "leadDetail": {
    "字段名": "字段值"
  }
}
```

user_query：[本轮用户输入内容]

dialog_history：
```json
[
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "..."}
]
```
```

### 修复方案撰写检查清单

生成修复方案时，按以下清单自检：

- [ ] **反补丁**：是否避免了在 prompt 层面堆砌约束/强调？
- [ ] **层级选择**：是否优先考虑了 Skill/工具层面的修复？
- [ ] **根本原因**：是否处理了根本原因而非表面症状？
- [ ] **杠杆点**：是否识别了能连带解决其他问题的修复点？
- [ ] **业务对齐**：是否需要业务确认？是否可能存在业务误解？
- [ ] **简洁性**：是否用简洁原则代替了冗余示例？
- [ ] **评估器审视**：归因是否可能受评估器误导？
- [ ] **Anti-Few-shot**：After 文本中是否存在 `（如"X"、"Y"等）` 或 `示例：...→` 模式？若有，必须改为纯逻辑原则
- [ ] **Agent 能力边界**：修复方案是否要求某 agent 执行其架构角色之外的功能？Master 是否被要求直接回复？
- [ ] **路由优先**：当现有架构中已有可胜任的子 Agent 时，是否优先修复路由而非内容？
- [ ] **知识优先**：是否先检查了数据/知识库完整性？是否在数据缺失的情况下直接添加逻辑约束？
- [ ] **工具优先**：计算/查询/格式问题是否优先考虑了工具方案？
- [ ] **Step 1 充分性**：仅执行 Step 1 能否独立解决或显著缓解核心问题？
- [ ] **新 Skill 门槛**：如果建议新建 Skill，是否满足高频+ROI+边界清晰三重条件？
- [ ] **组件名准确性**：修复位置中的 Skill/Agent/工具名称是否与 Harness 中的实际名称一致？

### Mode B 适配

配对模式下，修复方案有四种导向：
- **退化 case**：修复方向是"恢复 V1 的正确行为"，Step 1 应聚焦 diff 导致的退化点
- **修复 case**：验证方向是"V2 的改进是否真正解决了问题"
- **顽疾 case**：修复方向同普通模式——找系统性根因
- **波动 case**：修复方向侧重"稳定性"——确定性增强方案

---

## 报告话术风格（全局规范）

报告的读者是需要快速决策"改哪里、怎么改"的工程师和产品经理。

**术语中文化**：
- 英文术语在**首次出现时**给出中文对照（如"Dynamic Context（动态上下文）"），后续全部使用中文
- 仅在需要**精确定位代码/配置位置**时保留英文原文

**避免自造概念**：
- 不要使用"三级联锁失效模型""熵增失稳源"等自造术语。用平实的因果链描述替代
- 避免不必要的学术化包装

**失效描述具象化**：
- 每个归因结论都要有**具体的锚点**——用该 case 实际的 input/output 片段来举例
- 先展示"Agent 实际返回了什么"和"正确的应该是什么"，再给出抽象归因

---

## Phase 5：报告生成

输出一份完整的 Markdown 分析报告，统一采用**4节结构**：

```
一、基本信息    ← 纯事实（ID、评分、原始评估器输出、对话上下文）
二、链路还原    ← 纯事实（Phase 2 的结构化调用表 + 执行统计摘要）
三、根因分析    ← 混合（Phase 3 的节点归因 + 根因链 + 一句话总结；每条明确标注信源）
四、修复方案    ← 4.1 根因汇总 + 4.2 渐进式修复路径 + 验证用测试case
```

**各节内容约束**：
- **一、基本信息**：只放原始事实数据——thread_id、trace_id、评分、评分理由原文、对话上下文原文、期望输出原文、实际输出原文。不含任何解读。
- **二、链路还原**：直接粘贴 Phase 2 的结构化调用表。不含推断性语言。
- **三、根因分析**：Phase 3 的归因内容。**禁止重复链路还原的执行细节**——用"步骤S_N"指向链路还原表。
- **四、修复方案**：4.1 根因汇总表 + 4.2 渐进式修复路径（含触发条件和优先级评分）+ 各 Step 修复内容展开 + 验证用测试case。

**各节之间不允许信息重复**。

> 完整报告模板见 `references/report-templates.md`。

### 两个 artifact 的职责分工

- `case_report_{case_id}.md` — **人读 + viewer 展示**。feedback_viewer 直接从 Markdown 提取"三、根因分析"和"四、修复方案"章节渲染，因此章节结构必须严格遵循模板。
- `case_summary_{case_id}.json` — **机器聚合**。auto-case-summary 读取此 JSON 做跨 case 统计和归并，因此字段名必须与 canonical schema 一致。viewer 仅在 Markdown 提取失败时 fallback 到 JSON。

报告保存到 `{analysis_root}/reports/`，文件名格式：
- Mode A：`case_report_{case_id}.md`
- Mode B：`case_report_{case_id}.md`（统一格式，内容含配对信息）

### 结构化摘要 JSON

每条 case 的分析完成后，**必须额外输出**一个 `case_summary_{case_id}.json`。该 JSON 用于 auto-case-summary 的轻量化聚合。

> Summary JSON 的完整 Schema 见 `references/report-templates.md`。

---

## 并行执行策略

### S2 执行授权与审计

**原则**：S2 的 `case_report_{case_id}.md` / `case_summary_{case_id}.json` 必须由 subagent 逐 case 生成。主 agent 只负责读取 `analysis_manifest.json`、生成 subagent prompt、调度 / 校验 / 汇总 subagent 产物、生成 `feedback_viewer.html`。除非用户明确选择 `manual_serial_fallback`，主 agent 禁止直接批量生成归因报告。

**触发门禁**：在 支持 subagent 的宿主环境中，如果宿主策略要求“只有用户显式要求 subagent / delegation / parallel agent work 才能启动子代理”，主 agent 必须先向用户确认：

> 本阶段按 skill 设计需要为每个 selected case 启动独立子代理并行分析。是否授权使用子代理执行 S2？

未获得明确授权前，禁止启动 subagent，禁止自动降级为主 agent 批量生成报告，必须停止并等待用户确认。

**fallback 三选一**：如果 subagent 不可用或未授权，必须询问用户选择：(a) 授权 subagent 后重试；(b) 主 agent 串行分析，并标记 `manual_serial_fallback`；(c) 暂停 S2，并标记 `paused`。

**落盘要求**：S2 开始时必须写入 `{analysis_root}/_s2_execution_plan.json`，让执行路径可审计。写入失败时停止 S2，不继续生成报告。生成 `feedback_viewer.html` 时，脚本会读取并嵌入该执行计划；viewer 必须展示执行模式提示，尤其让 `manual_serial_fallback` / `paused` 可被人工审查者直接识别。

```json
{
  "stage": "S2",
  "execution_mode": "subagent",
  "subagent_authorized": true,
  "fallback_reason": null,
  "selected_case_count": 24
}
```

`execution_mode` 允许值：
- `subagent`：已授权并使用 subagent 逐 case 分析；并发度由宿主能力和下方并行策略决定
- `manual_serial_fallback`：用户明确选择由主 agent 串行分析
- `paused`：未授权或 subagent 不可用，用户选择暂停 S2

如果进入 `manual_serial_fallback`，必须在 `_s2_execution_plan.json` 中记录 `fallback_reason`，并在最终汇报中明确说明该批报告不是 subagent 产物。

### 宿主执行策略

- **支持 subagent 的宿主环境**：支持 subagent 并行，对每个 case 启动独立子代理
- **宿主 Agent**：使用可用的 worker subagent；如果宿主策略要求显式授权，必须先完成上方门禁
- **不支持 subagent 的宿主环境**：不得自动降级，必须按 fallback 三选一等待用户决定

### Subagent 权限预检（probe-and-worker 合并模式）

> **设计变更（probe-worker 合并）**：旧版本要求**先**起一个不做实际工作的"测试 subagent"探权限，成功后**再**起正式批次。这导致冷启动多花一倍单 case 时长。新版本将探针与首个真实 worker 合并：

1. **启动 1 个 foreground subagent，让它分析批次中的第 1 个真实 case**（不是 dummy 任务）
   - prompt 完全按 §Subagent Prompt 生成 流程产出
   - 该 subagent 既是权限探针，也是首个生产 worker
2. **首个 subagent 完成成功** → 立即按 §并行策略 一次性启动剩余 N-1 个 case 的并发批次（不再补探针）
3. **首个 subagent 失败**：按下列**信号优先级**判定失败类别（按从硬到软的可观测信号顺序，命中最高一项即归类，不再向下匹配）：

   | 优先级 | 信号 | 类别 | 处理 |
   |:---:|---|---|---|
   | 1 | Agent tool 调用同步抛错（subagent 未启动） | **权限被拒** | 停下询问用户：(a) 授权 subagent 后重试 (b) 主 agent 串行分析并标记 `manual_serial_fallback` (c) 暂停 S2。**禁止**自动降级为脚本方案。等待明确选择 |
   | 2 | Agent tool 错误消息含关键字 `permission`/`denied`/`unauthorized`/`tool not allowed`（不区分大小写） | **权限被拒** | 同上 |
   | 3 | Agent tool 正常返回，但 `case_report_{case_id}.md` 不存在 / 头 5 行无 `## 一、基本信息` / `case_summary_{case_id}.json` 缺 `scope` 字段 | **case 分析失败** | 记 `format_warning`，继续启动剩余批次（避免单 case 异常阻塞整轮） |
   | 4 | subagent 完成但 case_summary 字段不齐（如 in_agent 缺 `root_causes`） | **case 分析失败** | 同上 |
   | 5 | 以上信号均不命中（如启动后立即崩溃且错误信息为空） | **歧义** | **保守按权限被拒处理**——停下询问用户，附错误原文供判断 |

> **为何 probe-worker 合并**：实测旧版本在权限正常环境下，探针阶段约耗 1× 单 case 时长（典型 2-4 min）但产出只是一个 dummy 报告，纯浪费。合并后探针的产出就是首个 case 报告，零浪费。在权限异常环境下，失败检测时机不变（首个 subagent 启动失败立即可见）。
>
> **重试上下文**：用户调整权限后选择 (a) 重试时，主 agent 重新启动同一 case_id 的首个 subagent；prompt / manifest / case 范围保持不变，不重置已分析结果（如有）。

### 并行策略

采用**动态滑动窗口**模式——维持一个最大并发数的 subagent 池。

**并发上限**（一律使用 **foreground subagent**）：
- **≤10 条**：一次性全部并行启动
- **>10 条**：动态窗口，最大并发数 = 10

**进度汇报**：每完成 5 个 subagent，向用户简要汇报进度。

### Subagent Prompt 生成

> Prompt 模板已外置为 `references/subagent-prompt-template.md`。
> 主 agent 为每个 case 生成 prompt 时，必须严格遵循以下流程。

**Step 1 — 读取模板**：

读取 `<skill_path>/references/subagent-prompt-template.md`，获取完整的 prompt 模板文本。

**Step 2 — 替换占位符**：

对模板中出现的 `{{placeholder}}` 做纯文本替换。trace 路径有"推荐"和"legacy"两种占位符；其它占位符都是必填：

| 占位符 | 值来源 | 状态 |
|--------|--------|--------|
| `{{case_id}}` | 当前 case 的 case_id | 必填 |
| `{{eval_row_json}}` | 当前 case 对应的评测记录行 JSON | 必填 |
| `{{analysis_root}}` | 本次分析的 `$ANALYSIS_ROOT` 路径——subagent 把 `case_report_*.md` 和 `case_summary_*.json` 写到 `{{analysis_root}}/reports/`，所以必须替换为有效绝对目录路径 | **必填** |
| `{{skill_path}}` | 当前 skill 的安装路径 | 必填 |
| `{{harness_path}}` | Agent Harness 路径，无则填 `"无"` | 必填 |
| `{{trace_abs_path}}` | 当前 case 的 trace 文件**绝对路径**（推荐）；详见下方"trace 路径归一化要求" | **推荐**（trace 路径） |
| `{{trace_json_filename}}` | 当前 case 的 trace 文件名 | legacy（trace 路径，仅当 trace 实际位于 `{analysis_root}/traces/` 下时配合 `{{analysis_root}}` 拼接使用） |

**替换策略**：

- **trace 路径优先用 `{{trace_abs_path}}`**：直接从 manifest 取绝对路径，避免拼接歧义——manifest 的 `trace_path` 可能不在 `{analysis_root}/traces/` 下（如 `traces_clean/`、自定义目录），legacy 双占位符的拼接 `{{analysis_root}}/traces/{{trace_json_filename}}` 在这些情形下会失效。
- **trace 路径归一化要求**（P2 修复）：替换 `{{trace_abs_path}}` 前，main agent 必须把 `manifest.cases[i].trace_path` 归一化为**绝对路径**——
  - `Path(trace_path).is_absolute()` → 直接使用
  - 相对路径 → 用 `(Path(manifest_path).parent / trace_path).resolve()` 解析为绝对路径
  - 这一步**不能依赖 subagent 的 CWD**（subagent 可能在不同 worker 进程里跑，CWD 不可控）
- legacy `{{trace_json_filename}}`（配合 `{{analysis_root}}`）仍替换，但仅供兼容旧分支或外部 fork 模板；新模板应只用 `{{trace_abs_path}}`。
- 替换前 grep 模板看 trace 路径占位符是哪种；其它必填占位符（`{{case_id}}`、`{{eval_row_json}}`、`{{analysis_root}}`、`{{skill_path}}`、`{{harness_path}}`）任何模板都必须替换。

**Step 3 — 完整性自检**（见下方"Subagent Prompt 完整性自检"节）

**Step 4 — 发送**：

将替换后的完整文本作为 Agent tool 的 prompt 参数发送，**调用时必须显式传 `model: "<worker-model>"`**——不要让子 agent 继承父 session 的模型。

```
Agent({
  description: "...",
  subagent_type: "general-purpose",
  model: "<worker-model>",          // 强制 worker 模型，不省略
  prompt: <替换后的完整模板>
})
```

理由：
- **成本**：单 case 分析是结构化抽取 + 链路还原任务，worker 模型 4.6 完全够用；父 agent 若是 Opus，N 个并发 subagent 全跑 Opus 会让本次分析的 token 成本上升一个量级。
- **并发上限**：worker 模型 的请求/分钟和 token/分钟配额比 Opus 高，10 并发跑 worker 模型 不容易触限；跑 Opus 时常被限速回退到串行，反而拉长端到端时长。
- **一致性**：所有 case 的子 agent 跑同一模型，下游聚合（auto-fix-planner / 人工 review）才有可比基线；继承父模型会让 "Opus 跑出来的 case_001" 与 "worker 模型 跑出来的 case_002" 在严谨度/啰嗦度上有微差。

**模型选择按宿主能力映射**：
- **支持 subagent 的宿主环境**：显式使用 `model: "<worker-model>"`，不要让子 agent 继承父 session 的模型
- **宿主 Agent**：使用下方 S2 默认预设
- **其他宿主**：使用该宿主中等价的低成本 worker/subagent 模型

不允许因模型名不匹配而跳过 subagent；必须按宿主能力做等价映射，或停下说明原因。

**宿主 Agent S2 默认预设**：

```json
{
  "agent_type": "worker",
  "model": "gpt-5.4-mini",
  "reasoning_effort": "xhigh"
}
```

```
Agent({
  description: "...",
  subagent_type: "general-purpose",
  model: "<worker-model>",          // 支持 subagent 的宿主环境 场景显式指定；其他宿主按等价 worker 模型映射
  prompt: <替换后的完整模板>
})
```

理由：
- **成本**：单 case 分析是结构化抽取 + 链路还原任务，中等成本 worker 模型通常足够；不应让所有 subagent 默认继承高成本父模型。
- **并发上限**：worker/subagent 模型通常更适合多 case 并发；继承高成本父模型时容易触限，反而拉长端到端时长。
- **一致性**：所有 case 的子 agent 应跑同一等价模型，下游聚合（auto-fix-planner / 人工 review）才有可比基线；混用模型会让不同 case 的严谨度/啰嗦度出现微差。

## ⚠️ Prompt 生成强制约束

1. **公共部分必须逐字保留**——模板中除 `{{placeholder}}` 外的所有文本，主 agent 不得做任何摘要、精简、改写或重新组织
2. **每个 subagent 拿到的 prompt 公共部分必须完全一致**——唯一的差异是 6 个占位符的值
3. **禁止在替换过程中"优化"或"调整"模板内容**——即使主 agent 认为某段表述可以更好
4. **如果 context 不足以容纳完整模板**：降低并发数（从 10 降到 5），而不是精简模板

违反以上约束会导致不同 case 的分析标准不一致，使下游聚合结果不可比较。

### Subagent Prompt 完整性自检

主 agent 完成占位符替换后、发送 prompt 前，对生成的 prompt 文本做以下 5 个锚点检测：

| # | 锚点字符串 | 检测目的 |
|---|-----------|---------|
| 1 | `scope` | JSON Schema v1.8.0 顶层字段存在 |
| 2 | `[Trace实录]/[Prompt推断]/[假设]` | 信源标注要求存在 |
| 3 | `references/attribution-framework.md` | 归因框架外置读取指令存在 |
| 4 | `❌ 使用阿拉伯数字` | 格式负面示例存在 |
| 5 | `Phase 2 链路还原` | 分析流程完整性 |

**执行规则**：
- 5 个锚点全部命中 → 通过，发送 prompt
- 任一锚点缺失 → 说明公共部分被意外精简或截断，**必须重新从模板文件读取并重新替换**，不得手动补丁
- 自检失败超过 2 次 → 停止批量执行，通知用户检查模板文件完整性

### Subagent 输出格式校验

每个 subagent 完成后，主 agent 做格式检查（三层校验，从粗到细）：

1. **Markdown 报告**：读取 `case_report_{case_id}.md` 前 5 行，确认包含 `## 一、基本信息`（非阿拉伯数字）
2. **JSON 合法性**：对 `case_summary_{case_id}.json` 跑 `json.loads(file_content)`：
   - **抛 `JSONDecodeError`** → 标记 `json_broken`，附 line/col 信息，触发 retry（最多 1 次重生成 subagent prompt 让其修正引号/反斜杠转义）
   - 文件末尾如出现单行注释 `// JSON_BROKEN: ...`（subagent 自验失败兜底产物）→ 直接判为 `json_broken`，不再尝试 retry
3. **JSON Schema 字段**（仅当步骤 2 通过）：
   - 存在 `scope` 字段（`in_agent` / `external`）
   - `scope=in_agent` 时 `root_causes` 数组非空
4. 任一检查不通过 → 标记 `format_warning` 或 `json_broken`，在进度汇报中提示用户；不阻塞其它 case 分析。下游 viewer 对 `json_broken` 的容错处理见 §HITL 2 "JSON 损坏容错"。

### 上下文窗口管理

- **Harness 文件**：主 agent 只记录路径，subagent 按需读取
- **Trace JSON 文件**：同上，主 agent 不读取 trace 内容
- **评测记录**：仅读取必要的列和目标行
- 每个 subagent 完成后，主 agent 只记录：`{case_id, status, output_path, core_failure_oneliner}`

### Session 断裂保护

如果主 agent 感知到上下文即将紧张（已消耗超过 70%）：
1. 将当前进度持久化到 `$ANALYSIS_ROOT/_progress.json`
2. 告知用户当前进度和未完成的 case
3. 新 session 读取 `_progress.json` 即可恢复上下文

---

## HITL 2：结构化反馈（查看器）

所有被选中的 case 分析完成后，skill 自动调用 `scripts/generate_feedback_viewer.py` 生成查看器：

```bash
$PYTHON_CMD <skill_dir>/scripts/generate_feedback_viewer.py \
  {analysis_root}/reports/ \
  --manifest {analysis_root}/analysis_manifest.json \
  --static {analysis_root}/feedback_viewer.html
```

> **`$PYTHON_CMD`**：使用环境检测阶段确定的 Python 可执行路径。
>
> **最简用法**（自动推断路径）：`$PYTHON_CMD <skill_dir>/scripts/generate_feedback_viewer.py {analysis_root}`
>
> **脚本工作流程**：
> 1. 读取 `analysis_manifest.json`，过滤 `selected: true` 的 case
> 2. 收集对应的 `case_report_*.md` 和 `case_summary_*.json`
> 3. 读取 trace 文件按 `thread_id` 精确匹配，兼容两种命名：`traces/trace-*-thread-*.json`（analysis-compact 历史命名）与 `traces/thread-<thread_id>.json`（当前 traces_fetch 默认命名）；匹配不到时回退 manifest 的 `trace_path`（若 `trace_path` 是其他机器的绝对路径，再按文件名落到本地 `traces/`）
> 4. 读取 `viewer/feedback_viewer.html` 模板
> 5. 将数据 JSON 嵌入模板的 `<script id="embedded-data">` 标签，生成自包含 HTML
>
> 脚本会额外携带可选的 `_s2_execution_plan.json`，用于 viewer 展示 S2 执行模式。
>
> **字段别名兜底**：查看器会对已知字段别名（如 `score` / `ai_score`）做兼容，并动态渲染 `case_summary` JSON 中的未知字段。canonical summary schema 仍以 `references/report-templates.md` 为准。
>
> **Trace 展示兼容性**：viewer 模板内置 trace normalizer，同时支持默认 `analysis-compact` 和 fetch_and_clean beta `langgraph-clean`。两种格式都会展示格式、trace/thread id、消息上下文、调用节点、token/cost 摘要；若遇到未知结构，则展示 raw JSON fallback，避免"数据已嵌入但原始 Trace 面板为空"。
>
> **JSON 损坏容错**：脚本对每份 `case_summary_*.json` 用 try/except 包裹 `json.load()`。若解析失败：
> - 该 case 加入 `data.broken_summaries`（含 `case_id` / 错误位置 / 原文前 4KB 摘录）
> - viewer 顶部插红条警告 `⚠️ N 份 case_summary JSON 损坏`，列出损坏 case_id
> - 该 case 仍可在查看器中查阅 Markdown 报告（`case_report_*.md`），仅缺结构化根因卡片
> - **不阻塞**其它 case 渲染，也不让脚本退出非 0

### Call Graph Schema 约束（trace 渲染契约）

trace JSON 的 `call_graph` 由上游 `auto-trace-prep` 的 `_build_call_tree` 生成，本 skill 的 viewer 按以下契约渲染：

| 字段 | 必填 | 说明 |
|------|:----:|------|
| `nodeType` | ✅ | `GENERATION` / `TOOL` / `CHAIN`（CHAIN 通常被 auto-trace-prep 过滤，但 viewer 兼容） |
| `name` | ✅ | 节点名（如 LLM 节点名、tool 名） |
| `step` | ✅ | 全局步骤号 |
| `input` / `output` | 推荐 | TOOL 节点必含完整 input（arguments）/ output（result）；GENERATION 节点的 input 是 messages 数组、output 是 assistant 消息 |
| `children` | 视情况 | 子节点数组（TOOL 通常挂在 GENERATION 之下）；非空时 viewer 递归渲染，缩进展示 |
| `toolCallNames` | 视情况 | GENERATION 节点的工具调用名清单；当 `children` 缺失时作为 fallback 让 viewer 回到"sibling 提取"模式 |
| `model` / `latency` / `tokenUsage` / `cost` | 可选 | meta 信息，节点头条显示 |

**渲染规则**：

- viewer 优先用 `node.children` 嵌套结构展示 TOOL 子节点（含完整 input/output）
- 若节点无 `children` 字段（老 trace），降级回退到 `toolCallNames` + "下一兄弟 GENERATION 节点的 `input` 中 role=tool 消息" 的提取链路
- 节点深度从 0 起，每层视觉缩进；DOM 标 `data-node-type` / `data-depth` 供回归测试断言
- 自检：脚本运行时若 `_meta.stats.toolCount > 0` 但 call_graph 递归遍历 TOOL 节点数 = 0，输出 stderr warning + viewer 内插黄条提示

### 查看器 UI 要素（每个 case 一个页面）

| 区域 | 内容 |
|------|------|
| Case 概览 | case_id、thread_id、评测行摘要（user_query → expected vs actual） |
| 归因报告 | 渲染 case_report.md（链路全景 + 逐层归因 + 修复方案） |
| 根因摘要 | 从 case_summary.json 提取的结构化根因卡片 |
| **反馈表单** | 3 态 verdict + 正交 group_id + 顶层正交 scorer_feedback（弹窗交互，schema 2.2） |

### 反馈表单字段（schema 2.2）

```
反馈（verdict）:○ 采纳 (accept) ── 零文本字段
                ○ 修改后采纳 (revise) → 展开 revision 文本框（归因覆盖文本）
                ○ 拒绝 (reject) → 自动弹出"评分器反馈"弹窗（默认必填，可显式跳过）

priority:       ○ P0  ○ P1  ○ P2  ○ 不纳入本轮修复  (verdict=reject 时整行隐藏)

group_id:       [可选；所有 verdict 通用 — "加入归并"按钮弹窗多选已审 case]

revision:       [verdict=revise 时必填 — 归因覆盖文本，Planner 必读]

scorer_feedback:[可选 · 顶层正交字段 · 所有 verdict 通用 · 弹窗交互]
                "+ 评分器反馈" 按钮触发 → 弹窗内填字段：
                评分规则引用 (rubric_ref):  [自由文本，可空，如 "biz_a_score.md §3.1（零重复）"]
                误判模式 (misjudge_pattern):
                    ○ 评分错误 (score_wrong)         → 派生 affects_score=true (剔除统计)
                    ○ 评分正确但理由错误 (reason_wrong_only) → 派生 affects_score=false (不剔除)
                建议改写 (suggested_revision): [自由文本（必填）]
```

> schema 2.2 关键变更（vs 2.1）：
> - **删除 `reject_subtype` 字段**：reject 含义统一为"不作为 badcase 进入修复流程"
> - **misjudge_pattern 收窄为两值**：值含义即决定 `affects_score`，不再有独立 checkbox
> - **scorer_feedback 改为弹窗**：避免折叠造成的页面跳顶问题；reject 时自动弹出
> - **UI 中文化**："Verdict" → "反馈"；"Rubric 引用" → "评分规则引用"

#### verdict / group_id / scorer_feedback / repair_priority 四正交关系

| 维度 | 表达什么 | 取值 | 消费方 | 举例 |
|---|---|---|---|---|
| `verdict` | 对 agent 的反馈方向（归因有效性） | accept / revise / reject | Planner（reject 跳过；accept/revise 进 fix_plan） | revise = 归因要改、改完后修 |
| `group_id` | 同根因聚类信号 | group_NNN 或 null | Planner（最高优先级聚类约束） | group_001 含 case_A/B → 共用一个 FIX |
| `scorer_feedback` | 对评分器的反馈（独立维度） | object 或 null | Executor（离线汇聚 + 可选剔除统计） | revise + scorer_feedback = B 情形：agent 真错 + 评分理由也错 |
| `repair_priority` | 本轮修复时间预算 | P0/P1/P2/skip | Planner（fix_plan 内排序） | accept + skip = 归因对、本轮不修；reject 时强制 N/A |
| `revision`（从属） | revise 路径下的归因覆盖文本 | string | Planner（仅 verdict='revise' 时存在） | revise + revision="实际是 tool X 调参问题" |

> **设计原则**：用户对一条 case 的反馈本来就是多维的——"对 agent 的反馈方向" + "对评分器的反馈" + "聚类" 三者独立，不应强行塞进一个互斥的 verdict 选项。

`skip` vs `reject` 不重叠：reject = 这条不应是 badcase；skip = 是 badcase、归因也对，但本轮容量/业务策略不修。

#### 归并的增量与时机

归并不创造新归因信息，是给 Planner 的**同根因聚类信号**——最高优先级聚类约束（覆盖 §1.5 四档聚类的语义判定）。与 verdict 正交（accept + group / revise + group / reject + group 都合法）。归并后同组 case 共享一个 FIX，避免重复修复。

**何时该归并**：
- 多条 case 经分析后根因相同（如都是同一工具参数错误、同一 prompt 盲区）
- 仅打算用一个 FIX 修复整组而非每条单独修

**何时不该归并**：
- case 之间根因不同但症状相似（应独立 verdict）
- 想表达"这条 case 重要"——那是 priority 的语义

**归并交互**：在当前 case 点"+ 加入归并"按钮 → 弹窗列出**已审过**的 case（多选 checkbox）→ 确认后自动建 group_NNN（可重命名）。组成员等价，每条 case 各自填 revision（不强制承袭）。`group_id` 与 verdict 正交：accept + group / revise + group / reject + group 都合法。归并后的 case 在 sidebar 显示 `[group_001]` 标签，可快速跳过。

#### reject 含义（schema 2.2）

reject 不再细分子类型。统一含义：**"这条不作为 badcase 进入修复流程"**。可能因为：
- 评估集标注本身有问题（脏数据/重复 case）
- 网络/超时/上游服务异常等环境问题
- 评分器问题（trace 行为对、评分错）—— 此情况下应同时填 scorer_feedback (misjudge_pattern=score_wrong)

reject 时 viewer **自动弹出**评分器反馈弹窗（默认必填，因为多数 reject 与评分器有关）；用户可点"取消"显式跳过（罕见情形：纯标注问题或纯环境问题）。

#### 何时填 scorer_feedback（顶层正交字段）

scorer_feedback 与 verdict 正交——任何 verdict 都可附加。判定参考：

| 用户判断 | verdict | scorer_feedback | misjudge_pattern → affects_score |
|---|---|---|---|
| **A 情形**：agent 行为对、评分错（原 scorer_misjudge） | reject | 必填（弹窗自动弹出） | `score_wrong` → true（剔除统计） |
| **B 情形**：agent 真错（要修）+ 评分理由错（要给评分器反馈） | revise + revision | 填 | 评分结果错 → `score_wrong`；理由错但评分结果对 → `reason_wrong_only` |
| **C 情形**：agent 行为对、评分结果对、仅评分理由表达上有些瑕疵 | accept | 填（轻量备注） | `reason_wrong_only` → false（不剔除） |
| **D 情形**：agent 真错、评分理由也对 | accept / revise | 不填 | — |

**B 情形是 schema 2.1+ 的核心修正点**：旧 schema 把"对 agent 的反馈"和"对评分器的反馈"绑在互斥 verdict 上，B 情形下三条路都不通——accept 让 Planner 按错归因修；revise 修对 agent 但评分器问题被吃掉；reject + scorer_misjudge 让真 badcase 被剔除、agent 漏修。schema 2.1 把 scorer_feedback 升为顶层正交字段，schema 2.2 进一步把 misjudge_pattern 简化为两值（直接派生 affects_score）。

> **scorer_feedback 弹窗内的"误判模式 + 建议改写"必填**。弹窗内置校验，未填时点确认会被拦截。用户可点"取消"放弃填（不写入 feedback.json）。

### 输出

用户审查完所有 case 后，点击 "Submit All Feedback"，查看器将反馈数据写入 `feedback.json`。

如果用户选择暂不反馈，产出 `feedback.json` 标记 `status: "incomplete"`，流程暂停但不阻塞。

**`feedback.json` 示例（schema 2.2）**：

```jsonc
{
  "schema_version": "2.2",
  "analysis_id": "badcase_analysis_032514",
  "status": "complete",
  "total_cases": 5,
  "reviewed_at": "2026-03-25T16:30:00Z",
  "groups": [
    {
      "group_id": "group_001",
      "name": "工具参数类问题",
      "member_case_ids": ["case_017", "case_031"]
    }
  ],
  "feedback": [
    // 标准 accept
    { "case_id": "case_017", "verdict": "accept", "repair_priority": "P0", "group_id": "group_001" },

    // 标准 revise
    { "case_id": "case_023", "verdict": "revise", "repair_priority": "P1",
      "revision": "根因不是 prompt 盲区，是工具返回值解析错误" },

    // B 情形：agent 真错 + 评分理由错（schema 2.1+ 核心修正）
    { "case_id": "case_031", "verdict": "revise", "repair_priority": "P1", "group_id": "group_001",
      "revision": "与 case_017 同根因，但本 case 的具体表现是 retry 路径异常",
      "scorer_feedback": {
        "rubric_ref": "biz_a_score.md §3.2（销售推进）",
        "misjudge_pattern": "reason_wrong_only",
        "suggested_revision": "评分说 agent 没推进销售，但 trace 显示 agent 已 handoff 给销售——是销售子 agent 自身的 retry 问题",
        "affects_score": false  // 派生自 reason_wrong_only：评分理由错但结果对，不剔除
      }
    },

    // A 情形：agent 行为对、评分错（原 scorer_misjudge，2.2 = reject 单选项 + scorer_feedback）
    { "case_id": "case_045", "verdict": "reject",   // 注意：2.2 已删 reject_subtype 字段
      "scorer_feedback": {
        "rubric_ref": "biz_a_score.md §3.1（零重复）",
        "misjudge_pattern": "score_wrong",
        "suggested_revision": "评分理由说 agent 重复了 user_query，但 trace 显示 agent 给出了新增地址 ABC——Rubric 应识别该改写不属于重复",
        "affects_score": true   // 派生自 score_wrong：评分结果不可信，剔除当前轮统计
      }
    },

    // C 情形：accept + 评分理由轻量备注
    { "case_id": "case_052", "verdict": "accept", "repair_priority": "P2",
      "scorer_feedback": {
        "rubric_ref": "biz_a_score.md §2.4",
        "misjudge_pattern": "reason_wrong_only",
        "suggested_revision": "评分理由口语化偏多、可改为更正式表述（不影响判分结果）",
        "affects_score": false
      }
    }
  ]
}
```

> **schema 兼容性**：本次干净升级到 2.2，**不兼容旧 2.1 / 2.0 / 1.0**。Planner / Executor 检测到 `schema_version` ≠ "2.2" 时直接报错。仓库内无历史 feedback.json 样本，迁移成本为零。schema 2.1 → 2.2 的核心 breaking change：(a) 删除 `reject_subtype` 字段（reject 含义统一）；(b) `misjudge_pattern` 枚举从 5 值（过严/过松/...）收窄为 2 值（score_wrong / reason_wrong_only），值含义即决定 `affects_score`；(c) `affects_score` 由 `misjudge_pattern` 派生。

### Skill 内部不设 HITL 的理由

当前 skill 中影响归因质量的两个交互点已被前移到 auto-trace-prep：
- actual 列语义 → HITL 1 的 schema 确认中解决，结果写入 schema.json
- Harness 有无 → auto-trace-prep 阶段确定，harness_path 为 null 时 skill 自动降级

---

## 分析质量自检

报告完成后，按以下清单自检：

1. **事实推测分离**：链路还原（二）中是否有推断性语言？根因分析（三）中每条陈述是否都标注了 `[Trace实录]`/`[Prompt推断]`/`[假设]`？
2. **无重复内容**：根因分析（三）中是否有重复链路还原（二）的执行细节？如有，改为"参见步骤S_N"。
3. **归因针对性**：Phase 3 是否只分析了强相关节点？有没有分析了与 badcase 无关的节点？
4. **渐进式修复路径完整**：是否包含 4.1 根因汇总 + 4.2 渐进式修复路径？每个 Step 是否都有覆盖根因、优先级评分、触发条件？
5. **期望输出有据**：基本信息中的"期望输出"是否来自 reference_output 字段？
6. **锚点具象化**：根因分析中每个失效判断是否都有具体的输入/输出片段作为锚点？
7. **话术检查**：是否有未翻译的英文术语、自造概念、或无意义的学术包装？
8. **scope 分流正确**：是否先做了 scope 判断？评估器问题是否正确判定为 scope=external？
9. **component 合规**：每个归因节点是否都以 `**组件**：` 行开头？component 取值是否符合 `agent:{name}` / `tool:{name}` / `memory` 三种枚举之一（注意：eval 不是 component）？
10. **rule_violation 齐全**：每条 root_cause 是否都包含 rule_violation 字段？rule_violation=true 时是否填写了 rule_ref？
11. **trace_refs 存在**：每条 root_cause 是否都有 trace_refs 定位到具体 trace 节点？
12. **description 失败语义齐全**（v1.9.0 新增）：每条 root_cause 的 description 是否包含失败语义概括——明确提及在哪个认知阶段失败（comprehend / retrieve / act / synthesize 之一）以及属于何种集合差类型（missing / wrong / excess 之一）？这两项不再是独立字段但必须在 description 自由文本中清晰表达，否则下游聚类无法判断"是否同一类失败"。
13. **description 和 evidence 分离**：description（是什么错 + 失败语义概括）和 evidence（为何判错）是否分开写？evidence 是否引用了 trace 原文？
14. **Phase 3 不含废弃字段**：根因分析章节是否完全没有出现 `stage:` / `mode:` / `target_layer` 字符串和 F1–F11 字符串？（v1.9.0 移除 stage / mode 枚举字段）
15. **不含主/次归因语言**：Phase 3 中是否没有"主归因"、"次归因"、"[主]"、"[次]"等表述？
16. **修复方向正交**：修复方向是否采用 `{target_layer} · {fix_strategy}` 格式？具体手段是否来自"层级×策略矩阵"？
17. **杠杆点识别**：是否识别了能连带解决其他根因的杠杆点？Step 1 是否优先处理杠杆点？
18. **反补丁检查**：是否避免了在 prompt 层面堆砌约束/强调/加粗？是否优先考虑 Skill/工具层修复？
19. **工程层内容分级**：架构层（P3/P2架构）是否给出 L2 具体方案？数据层是否给出 L3 需求描述？
20. **Anti-Few-shot 最终检查**：修复方案（四）中的所有 Before/After 文本，是否完全不含 `（如"..."、"..."等）` 形式的 few-shot 枚举？
21. **评估器可靠性**：是否审视了评估器的评分理由是否合理？对于怀疑评估器误判的 case，是否正确标记为 scope=external 而非进入 in_agent 流程？
22. **组件名验证**：修复方案中所有 agent/skill/tool 名称是否与 Harness 一致？

### Mode B 额外自检项

1. **分叉点标注**：配对报告是否在链路还原部分明确标注了 🔴 分叉点？
2. **差异归因而非独立归因**：根因分析是否聚焦"版本间为什么不同"，而非两条独立分析？
3. **diff 相关度标注**：配对报告是否在根因分析末尾标注了"Harness diff 相关度"？
4. **diff 分析解耦**：配对报告中是否没有展开 diff 的系统性分析（留到 auto-case-summary）？

### 批量模式额外自检项

1. **人工反馈闭环**：是否向用户展示了查看器并等待反馈？feedback.json 是否正确生成？

---

## 环节结束提醒

当所有 case 分析完成、查看器已生成、`feedback.json` 已写入后，**必须**向用户展示以下后续操作指引：

```
✅ 归因分析完成！共生成 N 份报告，feedback_viewer.html 已就绪。

📋 后续操作：
1. 打开 feedback_viewer.html 审查报告并提交反馈（采纳 / 修改后采纳 / 拒绝 + 可选 group_id 归并）
2. 反馈提交后，输入 /compact 压缩当前上下文（推荐，释放 token 空间给下一环节）
3. 输入 /auto-fix-planner 启动修复方案制定（跳过汇总聚合，直接由 Planner 从 feedback 聚合根因）
```
