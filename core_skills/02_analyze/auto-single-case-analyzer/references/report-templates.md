# 报告模板与 JSON Schema

本文件包含 auto-single-case-analyzer 的完整报告模板和结构化数据 Schema。在生成报告时按需查阅。

> **何时读取此文件**：Phase 5 生成报告时，如需确认完整模板结构可查阅此文件。SKILL.md 中已包含报告结构概述，大多数情况下无需额外读取。

> **v1.9.0 重要变更**：移除 `stage` / `mode` 字段。每条 root_cause 简化为 (component, rule_violation, rule_ref, trace_refs, description, evidence)。失败的认知阶段语义和集合差类型语义下沉到 `description` 自由文本。Schema 不兼容 v1.8.0——下游 viewer 与 planner 的字段读取路径已同步更新。
>
> **v1.8.0 历史变更**：废弃 `component_primary` / `failure_type_primary` 顶层字段，改为 `scope` + `root_causes[]` 数组结构。新增 `causal_edges`。eval 从 component 枚举移出为 scope=external。**不兼容** v1.7.0 历史报告。

---

## 单条归因报告模板

```markdown
# Badcase 归因分析报告

**thread_id** `xxx` · **trace_id** `xxx` · **评分** X · **分析时间** YYYY-MM-DD

---

## 一、基本信息

| 字段 | 值 |
|------|---|
| Session / Turn | S_X / T_X（如适用）|
| 用户输入 | [user_query 原文] |
| 实际输出 | [agent_output 原文] |
| 期望输出 | [reference_output 原文] |
| 评分理由 | [评测器评分理由原文] |
| 问题分类 | [人工标注的问题分类，如有] |

**对话上下文**（触发轮之前的关键轮次，表格形式）：

| 轮次 | 角色 | 内容摘要 |
|------|------|---------|
| T_N-2 | 用户 | ... |
| T_N-1 | AI | ... |
| **T_N（触发轮）** | **用户** | **[user_query]** |

> 基本信息只放原始数据，不含分析或解读。

## 二、链路还原

[Phase 2 的结构化调用表，纯事实，格式如下：]

| 步骤 | 节点名称 | 类型 | 关键输出 | 异常 |
|------|---------|------|---------|------|
| S1 | master LLM #1 | GENERATION | tool_call: handoff_to_agent("子agent") | — |
| S2 | 子agent LLM #1 | GENERATION | tool_call: tool_name({参数}) | — |
| S3 | tool_name | TOOL | 返回: {关键字段} | — |
| S4 | 子agent LLM #2 | GENERATION | 输出: {摘要} | ⚠️ output=6 token (in=9416) |

**执行统计**：总耗时 Xs · LLM调用 N次 · 工具调用 N次 · 模型 xxx

## 三、根因分析

### 强相关节点

#### [节点名称]（步骤S_N）

**组件**：`agent:{name}` （或 `tool:{name}` / `memory`）
**规则违反**：`true/false`（若 true：rule_ref 指向规则条款）

[Trace实录] 观察到的具体行为或输出片段。
[Prompt推断] 对照规范的缺口（有 Harness 时填，无则省略此行）。
description：[错是什么 + 失败语义概括（哪个认知阶段的 missing/wrong/excess），一句话]
evidence：[为何判错，引用 trace 原文]

#### [节点名称2]（步骤S_M）

[同上结构]

### 根因链

**根因链**：rc_1（[节点A问题]）→ rc_2（[节点B问题]）→ 最终错误输出
（并列失败用 + 连接：rc_1 + rc_2 → 最终错误）

**一句话总结**：[最精简的根因描述]

> ⚠️ 三、根因分析不得出现 `target_layer` 字符串——target_layer 在 Phase 4 修复规划阶段独立选择。
> ⚠️ 三、根因分析不得出现 `failure_type` / `F1–F11` / `[主]` / `[次]` 等 v1.7.0 用语。
> ⚠️ 三、根因分析不得出现 `stage:` / `mode:` 等 v1.8.0 字段——这些信息以自然语言写入 description。

---

> 交叉对比模式额外项：
> **Harness diff 相关度**：高 / 中 / 低（判定依据：...）

## 四、修复方案

### 4.1 根因汇总

| ID | 根因 | 组件 | 规则违反 |
|----|------|------|---------|
| RC1 | [根因标题] | [component] | [true/false] |
| RC2 | [根因标题] | [component] | [true/false] |

**根因链**：RC_X → RC_Y → 最终错误输出

### 4.2 渐进式修复路径

| Step | 修复动作 | 覆盖根因 | 优先级 | 触发条件 |
|------|---------|---------|--------|---------|
| 1 | [修复动作描述] | RC1, RC2 | [分数] | 默认执行 |
| 2 | [修复动作描述] | RC1 | [分数] | Step1 后仍有问题 |
| 3 | [修复动作描述] | RC3 | [分数] | 多 case 反复出现 |

> 优先级 = 杠杆率(1-3) × 成本分(1-3) × 确定性分(1-3)

**Step 1 修复内容**：

```
修复方向：[target_layer] · [fix_strategy]
具体手段：[从矩阵选取]
修复位置：[harness标题 或 工程组件]

Before: [原文/现状描述]
After: [修改后内容]
```

**验证方式**：[如何验证此步骤的修复效果]

**Step 2 修复内容**：
[同上格式，若 Step1 不足时执行]

**TC1（验证用测试case）**

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

报告保存到 `{analysis_root}/reports/case_report_{case_id}.md`

---

## 结构化摘要 JSON Schema（v1.9.0）

每条 case 的分析完成后，**除了完整 Markdown 报告外**，还必须额外输出一个 `case_summary_{case_id}.json`。

```json
{
  "case_id": "case_017",
  "thread_id": "p-20260302-182813-54eb5c",
  "trace_id": "69461ad62de1fd82f5f39a2739af22fa",
  "score": 0,
  "scope": "in_agent",

  "root_causes": [
    {
      "id": "rc_1",
      "component": "agent:master",
      "rule_violation": false,
      "rule_ref": null,
      "trace_refs": [
        { "step_id": "S_2", "span": "thinking 第 3 段" }
      ],
      "description": "master agent 在意图理解阶段漏掉'查询动态上下文'规划步骤（comprehend 阶段 missing）",
      "evidence": "thinking 中无 leadDetail 读取指令，子 Agent 追问已知人数"
    }
  ],

  "causal_edges": [],

  "root_cause_chain": "rc_1（Master 未规划预填充步骤） → 子Agent追问已知人数 → 最终错误输出",
  "one_line_summary": "Master 规划缺失 leadDetail 预填充步骤，导致子 Agent 追问用户已提供的信息",

  "typical_snippet": {
    "user_input": "还有几个人出行？",
    "agent_output": "请问您一共几位出行？",
    "expected": "leadDetail 中已有出行人数=3，应直接引用",
    "problem_summary": "动态上下文未从 leadDetail 预填充"
  },

  "fix_step1_component": "agent:master",
  "fix_step1_target_layer": "P3_orchestration",
  "fix_step1_strategy": "工程型修复",

  "repair_path": {
    "steps": [
      {
        "step": 1,
        "action": "在编排层增加 leadDetail → Dynamic Context 的同步节点",
        "covers": ["rc_1"],
        "priority": {
          "leverage": 2,
          "cost": 2,
          "certainty": 3,
          "score": 12
        },
        "trigger": "默认执行",
        "component": "agent:master",
        "target_layer": "P3_orchestration",
        "fix_strategy": "工程型修复",
        "specific_method": "状态流转规则 + 中间件",
        "location": "动态上下文构建模块",
        "content": {
          "problem": "leadDetail 中已有出行人数，但 Dynamic Context 中 [已收集信息] 为空",
          "expected": "leadDetail.成人人数 + 儿童人数 → [已收集信息].出行人数",
          "mapping_rules": [
            "leadDetail.出发城市 → 出发地",
            "leadDetail.目的地 → 目的地",
            "leadDetail.成人人数 + 儿童人数 → 出行人数"
          ]
        },
        "verification": "检查 Trace 中 Dynamic Context 快照是否包含预填充数据"
      }
    ]
  },

  "stats": {
    "total_latency": 24.5,
    "generation_count": 6,
    "tool_count": 5,
    "model": "gemini-3-flash-preview"
  },
  "tags": ["规划缺失", "信息预填充"],
  "evaluator_confidence": "high",
  "evaluator_notes": null
}
```

**scope=external 时的 JSON**（评估器问题不进修复流程）：

```json
{
  "case_id": "case_031",
  "thread_id": "xxx",
  "trace_id": "xxx",
  "score": 0,
  "scope": "external",
  "external_reason": "参考答案滞后，评测集未同步新业务定义（2026-04）",
  "hitl_ref": "feedback.json#case_031",
  "one_line_summary": "评估器误判：agent 输出符合新业务定义，评测集标注未同步",
  "typical_snippet": {
    "user_input": "...",
    "agent_output": "...",
    "expected": "...",
    "problem_summary": "评估器问题，非 agent 问题"
  }
}
```

**字段说明（v1.9.0 简化）**：

| 字段 | 是否必填 | 说明 |
|------|---------|------|
| `scope` | 必填 | `in_agent` 或 `external`，Phase 3 第一步的分流结果 |
| `root_causes` | scope=in_agent 时必填 | 独立失败节点数组，每项含 component/rule_violation/rule_ref/trace_refs/description/evidence |
| `causal_edges` | 可选 | 因果关系数组，无因果时为空数组 |
| `external_reason` | scope=external 时必填 | 评估器/评测集/环境问题描述 |
| `hitl_ref` | scope=external 时必填 | 对应 feedback.json 的反馈来源 |
| `fix_step1_component` / `fix_step1_target_layer` / `fix_step1_strategy` | scope=in_agent 时必填 | Step 1 修复决策三元组，供汇总阶段快速统计 |

> ⚠️ **v1.9.0 移除的字段**：`root_causes[].stage`、`root_causes[].mode`。失败的认知阶段语义和集合差类型语义改写入 `description` 自由文本，由下游基于 LLM 语义判断。
>
> ⚠️ **v1.8.0 移除的字段（历史）**：`component_primary`、`component_secondary`、`failure_type_primary`、`failure_type_secondary`。

**root_causes 子字段约束**：

```
component_enum: [agent:{name}, tool:{name}, memory]
rule_violation_enum: [true, false]
```

> `description` 写作要求：必须包含失败语义概括（在哪个认知阶段失败 + missing/wrong/excess 的哪一种），用自然语言表达。详见 `attribution-framework.md` v6 第五节"description 写作要求"。

**repair_path / fix_step1 相关字段约束不变**（target_layer / fix_strategy 枚举同 v1.7.0）。

**content 字段格式**：
- **P0_prompt / P1_skill**：`{ "before": "原文", "after": "修改后" }`
- **P2_tool 数据层**：`{ "problem": "缺失描述", "expected": "补充方向" }`
- **P2_tool 架构层**：`{ "before": "原 Schema", "after": "新 Schema" }`
- **P3_orchestration**：`{ "problem": "现象", "expected": "预期行为", "mapping_rules": [...] }`

**其他字段**：
- `tags`：辅助分类标签，用于跨 case 聚合
- `stats`：从 trace 数据中提取的执行统计
- `evaluator_confidence`（v1.6.0 新增）：评估器可信度，枚举值 `high|medium|low|suspect`。当为 `low` 或 `suspect` 时必须填写 `evaluator_notes`
- `evaluator_notes`（v1.6.0 新增）：评估器审视备注（可选），说明评估器评分理由与 trace 实际行为的差异

---

## 配对归因报告模板（Mode B / 交叉对比模式）

```markdown
# 配对归因分析报告

**case_id** `xxx` · **轨迹模式** 退化/修复/顽疾/波动
**V1** `版本名` · thread `xxx` · 评分 X（pass/fail）
**V2** `版本名` · thread `xxx` · 评分 X（pass/fail）

---

## 一、基本信息

| 字段 | V1 | V2 |
|------|----|----|
| 版本名 | [版本名] | [版本名] |
| thread_id | `xxx` | `xxx` |
| 评分 | X (pass/fail) | X (pass/fail) |
| 评分理由 | [评测器原文] | [评测器原文] |

**用户输入**（两版本相同）：[user_query 原文]

**期望输出**：[reference_output 原文]

**各版本实际输出**：

| | V1 实际输出 | V2 实际输出 |
|---|---|---|
| 输出内容 | [原文] | [原文] |

**对话上下文**（两版本共享）：

| 轮次 | 角色 | 内容摘要 |
|------|------|---------|
| T_N-2 | 用户 | ... |
| **T_N（触发轮）** | **用户** | **[user_query]** |

## 二、链路还原

### V1 调用表

| 步骤 | 节点名称 | 类型 | 关键输出 | 异常 |
|------|---------|------|---------|------|
| S1 | master LLM #1 | GENERATION | tool_call: ... | — |

**执行统计**：总耗时 Xs · LLM调用 N次 · 工具调用 N次

### V2 调用表

| 步骤 | 节点名称 | 类型 | 关键输出 | 异常 |
|------|---------|------|---------|------|
| S1 | master LLM #1 | GENERATION | tool_call: ... | — |

**执行统计**：总耗时 Xs · LLM调用 N次 · 工具调用 N次

**分叉点**：🔴 V1步骤S_X vs V2步骤S_X —— [第一个行为不同的节点]

## 三、根因分析

### 强相关节点（差异归因）

#### [节点名称]（分叉点 V1:S_X / V2:S_X）

[Trace实录] V1：[V1 在此节点的行为摘要]。
[Trace实录] V2：[V2 在此节点的行为摘要]。
差异来源：prompt变更 / 上游输入差异 / 工具差异 / 随机性 `[Prompt推断]`

**[主]** `failure_type` · `target_layer`（针对失败版本）

[Prompt推断] 对照规范/diff 的缺口分析。
根因：为什么此版本在此处失效。

### 根因链

**根因链**：[版本间变更A] → [分叉点B] → 最终结果差异

**一句话总结**：[...]

**Harness diff 相关度**：高 / 中 / 低（判定依据：...）

## 四、修复方案

### 4.1 根因汇总

| ID | 根因 | 失效机理 | 目标层 | 差异来源 |
|----|------|---------|-------|---------|
| RC1 | [根因标题] | [failure_type] | [target_layer] | [diff_source] |

**根因链**：[版本间变更] → [分叉点] → 最终结果差异

### 4.2 渐进式修复路径

| Step | 修复动作 | 覆盖根因 | 优先级 | 触发条件 |
|------|---------|---------|--------|---------|
| 1 | [修复动作描述] | RC1 | [分数] | 默认执行 |

**Step 1 修复内容**：

```
修复方向：[target_layer] · [fix_strategy]
具体手段：[从矩阵选取]
修复位置：[harness标题 或 工程组件]

Before: [V2 现有内容]
After: [修改后内容]
```

**验证方式**：同一 case 重跑 V2，确认行为与 V1 一致

**TC1（验证用测试case）**

[同单条模式格式]
```

报告保存到 `{analysis_root}/reports/case_report_{case_id}.md`

---

## 配对摘要 JSON Schema（Mode B / 交叉对比模式）

每个配对分析完成后，输出 `case_summary_{case_id}.json`（与单条模式共用文件名格式）。

```json
{
  "case_id": "case_012",
  "mode": "compare",
  "trajectory_pattern": "regression",
  "versions": [
    {
      "version": "V1",
      "thread_id": "p-20260302-182813-54eb5c",
      "trace_id": "69461ad62de1fd82f5f39a2739af22fa",
      "score": 1,
      "score_label": "pass"
    },
    {
      "version": "V2",
      "thread_id": "p-20260310-093021-8b2c4f",
      "trace_id": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
      "score": 0,
      "score_label": "fail"
    }
  ],
  "scope": "in_agent",
  "divergence_points": [
    {
      "id": "DP1",
      "node": "hotel_agent LLM #2",
      "v1_behavior": "基于用户偏好筛选 top 3 并推荐",
      "v2_behavior": "直接输出原始搜索结果列表",
      "diff_source": "prompt_change",
      "description": "V2 的 hotel_agent prompt 删除了'基于用户偏好筛选并推荐 top 3'段落，导致 hotel_agent 在意图理解阶段漏掉筛选规划（comprehend 阶段 missing）",
      "rule_violation": false
    }
  ],
  "typical_snippet": {
    "user_input": "帮我查三亚的酒店，预算2000左右",
    "v1_output": "推荐三亚海棠湾万丽酒店（1880元/晚）...",
    "v2_output": "以下是搜索到的5家酒店：1. xxx 2. xxx ...",
    "expected": "基于预算筛选后推荐 1-3 家匹配的酒店",
    "problem_summary": "V2 prompt 变更导致 hotel_agent 跳过了结果筛选步骤"
  },
  "root_causes": [
    {
      "id": "RC1",
      "title": "hotel_agent prompt 中筛选指令被误删",
      "diff_source": "prompt_change",
      "component": "agent:hotel_agent",
      "rule_violation": false,
      "rule_ref": null,
      "trace_refs": [{"version": "v2", "step_id": "S_3"}],
      "description": "V2 迭代中重写了 hotel_agent prompt，遗漏了'基于用户偏好筛选'的关键段落，导致在意图理解阶段漏规划筛选步骤（comprehend 阶段 missing）",
      "evidence": "v2 trace step S_3：hotel_agent 直接输出搜索结果列表，无筛选逻辑；v1 trace step S_3：调用 preference_filter 后再生成"
    }
  ],
  "repair_path": {
    "steps": [
      {
        "step": 1,
        "action": "恢复 hotel_agent 的结果筛选指令",
        "covers": ["RC1"],
        "priority": {
          "leverage": 2,
          "cost": 3,
          "certainty": 3,
          "score": 18
        },
        "trigger": "默认执行",
        "target_layer": "P0_prompt",
        "fix_strategy": "能力型修复",
        "specific_method": "正向约束",
        "location": "hotel_agent prompt 第3段",
        "content": {
          "before": "（V2 中缺失）",
          "after": "基于用户偏好筛选并推荐 top 3"
        },
        "verification": "同一 case 重跑 V2，确认输出为筛选后的 top 3"
      }
    ]
  },
  "stats_comparison": {
    "v1": { "total_latency": 18.2, "generation_count": 4, "tool_count": 3, "model": "gemini-3-flash" },
    "v2": { "total_latency": 24.5, "generation_count": 6, "tool_count": 5, "model": "gemini-3-flash" }
  }
}
```

**字段填充要求**：

**基础字段**：
- `mode`：`"compare"` 表示配对归因
- `trajectory_pattern`：从 `["regression", "fixed", "all_fail", "unstable"]` 中选取
- `divergence_points`：每个分叉点包含 id、节点名称、两版行为描述、差异来源
- `diff_source` 枚举值：`prompt_change` / `upstream_input` / `tool_change` / `architecture_change` / `model_change` / `randomness`
- `typical_snippet`：包含 `v1_output` 和 `v2_output`

**root_causes（根因列表）**：
- 每个根因包含 id/title/component/rule_violation/rule_ref/trace_refs/diff_source/description/evidence（与单条模式 schema 对齐，v1.9.0 移除 stage/mode）
- `rule_ref`：rule_violation=true 时必填，否则 null
- `trace_refs`：必填，对照模式下每条 ref 含 `version`（v1/v2）+ `step_id`（+ 可选 `span`）
- `description` 必须包含失败语义概括（哪个认知阶段失败 + missing/wrong/excess 类型）
- `evidence`：必填，引用 trace 原文（对照模式下应同时引用 v1 与 v2 的对应 step 以支撑差异判定）

**repair_path（渐进式修复路径）**：
- 结构与单条模式相同
- `content` 字段中 `before` 应为 V2 现有内容，`after` 为修复后内容
- `verification` 应说明如何验证 V2 修复后与 V1 行为一致

**其他字段**：
- `stats_comparison`：各版本的执行统计对比

---

## 变更日志

| 版本 | 日期 | 类型 | 变更内容 |
|------|------|------|---------|
| v1.8.0 | 2026-04-17 | 重构 | 废弃 component_primary/failure_type_primary；新增 scope + root_causes[] 数组结构；每条 root_cause 包含 (stage, mode, rule_violation, trace_refs, description, evidence)；新增 causal_edges；eval scope=external 单独处理；**不兼容 v1.7.0** |
| v1.9.0 | 2026-04-29 | 简化 | 移除 root_causes[].stage / mode 字段（单条 + 配对 schema 同步）；description 写作要求收紧需包含失败语义概括；4.1 根因汇总表从 6 列减为 4 列；**不兼容 v1.8.0** |
