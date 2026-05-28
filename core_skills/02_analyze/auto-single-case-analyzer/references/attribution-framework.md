# 归因分类框架 v6

> 本文件是 scope、component、rule_violation、target_layer 和 fix_strategy 的唯一权威定义。
> 修改本文件后,须按「归因框架模块维护指南」中的迭代操作 Checklist 同步下游文件。
>
> **v1.9.0 重要变更**:移除 stage(认知阶段)与 mode(差异模式)两个字段。归因字段简化为 (component, rule_violation) 结构维度 + (description, evidence) 自由文本语义维度。stage / mode 表达的"在哪个认知阶段失败"与"集合差类型"信息下沉到 description / evidence 自由文本,由 LLM 根据 trace 实录直接判断,不再强制走固定枚举。
>
> **v1.8.0 重要变更**(历史):废弃 F1–F11 failure_type 枚举,替换为正交字段体系(stage × mode × rule_violation)。
> `eval` 从 component 枚举中移出,改为 `scope=external`,由 HITL reject 人工回流。
> 归因阶段输出多根因数组 + causal_edges,不再输出主/次归因。

---

## 归因链路总览

```
输入:Trace + Eval 结果
         ↓
Phase 3 · 归因诊断
    ① scope 分流(in_agent / external)
    ② 枚举所有独立失败节点
    ③ 记录因果关系
         ↓
Phase 4 · 修复规划
    ① 读因果图,三维评分选锚点
    ② 渐进式 Iteration
         ↓
输出:修复方案
```

**核心原则**:归因保证完整性,修复选择经济性。两阶段信息单向流动,归因不做主次排序。

---

## 零、scope 分流(Phase 3 第一步)

每条 badcase 进入归因前先分流:

| scope | 含义 | 判断者 | 处理 |
|-------|------|--------|------|
| `in_agent` | agent 自身失败 | agent 自动归因 | 走 component × rule_violation + description/evidence |
| `external` | 评估器 / 评测集 / 环境问题 | **agent 初判 + HITL 终判** | agent 在 Phase 3 第一步基于"评估器理由 vs trace 行为矛盾"标记疑似 external 并填 `external_reason`；HITL 阶段 PE 确认或覆盖；最终 external case 走 HITL reject 反向回流，不进 fix_plan |

**为什么需要 HITL 终判**：agent 没有评分标准的上帝视角——它不知道参考答案是否正确、标注是否滞后、评估器规则是否合理。agent 的初判仅基于"评估器评分理由 vs trace 实际行为"的明显矛盾，权威性不足以独立分流。最终是否归为 external 由 PE 在 HITL 阶段确认；PE 也可以将 agent 标为 in_agent 但实际是评估器问题的 case 通过 reject 反向回流，反之亦然。**agent 的 scope 输出不是终态，HITL feedback 才是。**

> `external` 不是和 agent/tool/memory 并列的 component,而是完全另一条归因路径,放在 scope 这一层而不是 component 枚举里。

---

## 一、component(问题位置,3 种枚举)

**仅 scope=in_agent 时使用**。回答"问题在系统的哪个位置"。

```
component_enum: [agent:{name}, tool:{name}, memory]
```

| 枚举值 | 含义 | 示例 |
|--------|------|------|
| `agent:{name}` | 任意 agent(主控或子 agent,用名字区分角色) | `agent:master`、`agent:search_agent` |
| `tool:{name}` | 具名工具 | `tool:web_search`、`tool:calculator` |
| `memory` | 记忆/状态存储层 | 字段写入失败、状态污染 |

`{name}` 由 auto-trace-prep 的 case setup 声明 component map,归因时直接引用名字(如 `agent:master`)。

### component 边界说明

- **`memory`** = 存储机制本身失败(写入失败、数据损坏、schema 不匹配)。agent 与 memory 的交互失败(未读取、写错 key)归 `agent:{name}`
- **`tool:{name}`** = 工具执行机制本身失败,或工具接口设计有缺陷。agent 选错工具、传错参数归 `agent:{name}`

---

## 二、rule_violation(横切字段)

规则遵循是横切判断,与失败发生在哪个认知阶段无关——任一节点的失效都可能伴随违反明确规则。

| 字段 | 值 | 含义 |
|------|----|------|
| `rule_violation` | `true` | 该节点违反了 system prompt 中明确列出的规则或约束 |
| `rule_violation` | `false` | 未违反明确规则(能力/推理问题) |
| `rule_ref` | string / null | 违反的是哪条规则(system prompt 段落引用 / 业务规则 ID) |

**典型组合**:

| 组合 | 含义 |
|------|------|
| `component=agent:master` + `rule_violation=true` + `rule_ref="输出格式 §3.2"` | agent 输出违反明确的格式规则 |
| `component=agent:master` + `rule_violation=true` + `rule_ref="禁止重复调用"` | agent 重复调工具且违反禁令 |
| `component=agent:master` + `rule_violation=false` | agent 失败但 system prompt 没相关明文约束(能力/推理问题) |

---

## 三、多根因与因果关系

一条 badcase 允许映射到多个根因,两种关系:

| 关系 | 形态 | 表达方式 |
|------|------|---------|
| 因果链 | A → B → C(上游导致下游) | `causal_edges: [{from: rc_1, to: rc_2}]` |
| 并列 | A + B → 同一错误(相互独立) | 两条独立 root_cause,无 causal_edge |

**下游节点是否独立记录的判断准则**:

问:**"如果 agent 在这一步按规则/能力要求做了正确判断,错误能不能被拦截?"**

| 答案 | 结论 |
|------|------|
| 能拦截 | 下游是独立失败,单独记一条 root_cause |
| 不能拦截(信息/能力根本没给) | 下游是上游症状,归因到上游即可 |

LLM agent 的每个节点都有自主推理能力,下游失败通常是独立的,需要单独归因。

---

## 四、归因 schema(完整)

```yaml
case_id: string
scope: in_agent | external

# 仅 scope=in_agent 时填充
root_causes:
  - id: rc_1
    component: agent:master          # 物理位置
    rule_violation: false            # 规则违反横切
    rule_ref: null                   # 违反的规则引用(rule_violation=true 时必填)
    trace_refs:                      # 定位 trace 节点(必填)
      - step_id: S_2
        span: "thinking 第 3 段"     # 可选,精确到 span
    description: "agent 在意图理解阶段误解为历史天气查询(认知偏差)"       # 错误是什么 + 失败语义(短)
    evidence: "thinking 写'查历史',但 query 是'明天'"  # 为何判错(引用 trace 原文)

causal_edges:                        # 因果关系(无因果关系可省略)
  - from: rc_1
    to: rc_2

# 仅 scope=external 时填充
external_reason: string              # 评估器问题 / 评测集标注错 / 环境异常
hitl_ref: string                     # 反馈来源(feedback.json 路径)
```

> **失败语义如何写进 description**:v1.9.0 取消了 stage / mode 枚举字段,但失败的"在哪个认知阶段发生""属于何种集合差(漏做/做错/多做)"等语义信息仍然有价值——这些信息现在以**自然语言**形式直接写入 `description`,例如"agent 在意图理解阶段漏掉时间维度判断(missing)""tool 在结果整合时输出多余字段(excess)""agent 用错检索关键词(wrong)"。Phase 4 修复规划与下游聚类会基于 description 文本做语义判断。

### 三个文字字段的职责

| 字段 | 回答什么问题 | 值类型 |
|------|------------|--------|
| `trace_refs` | 在 trace 的哪个节点 | 结构化(step_id + 可选 span) |
| `description` | 这个错是什么 | 自然语言(短) |
| `evidence` | 为什么判它是错 | 自然语言(引用 trace 原文) |

---

## 五、v1.8.0 → v1.9.0 迁移映射

### 字段变化

| v1.8.0 字段 | v1.9.0 对应 |
|------------|------------|
| `root_causes[].stage` | **移除**;失败发生的认知阶段以自然语言写入 `description` |
| `root_causes[].mode` | **移除**;失败的集合差类型以自然语言写入 `description` |
| `root_causes[].component` | 保留(枚举不变) |
| `root_causes[].rule_violation` / `rule_ref` | 保留 |
| `root_causes[].trace_refs` / `description` / `evidence` | 保留;`description` 写作要求收紧——必须包含失败语义概括 |
| `causal_edges` | 保留 |
| `scope` | 保留 |

### 历史:v1.7.0 → v1.8.0 字段变化(参考)

| v1.7.0 字段 | v1.8.0 对应 |
|------------|------------|
| `component_primary` | `root_causes[i].component` |
| `failure_type` (F1–F10) | `(stage, mode, rule_violation)` 三字段分解(v1.9.0 已再简化) |
| `failure_type` = F11 | `scope = external` |
| `component = eval` | 不存在,改走 `scope = external` |
| `target_layer`(归因阶段) | 不在归因阶段,仅 Phase 4 出现 |
| 主归因/次归因 | 不存在,归因只做因果枚举,Phase 4 选锚点 |

### description 写作要求(v1.9.0 新增)

由于 stage / mode 枚举字段被取消,失败的认知阶段语义和集合差语义必须在 `description` 中以自然语言表达。建议格式:

```
[component 中文名] 在 [认知阶段简述] [失败动作简述,体现 missing/wrong/excess 之一]
```

**示例**:

| description 示例 | 隐含语义 |
|----------------|---------|
| "master agent 在路由判断时漏掉子 agent 选择" | comprehend + missing |
| "search_agent 用错检索关键词" | retrieve + wrong |
| "hotel_agent 在结果整合时输出多余字段" | synthesize + excess |
| "calculator tool schema 缺少必填参数校验" | act + missing(component=tool) |

> 不强制套用模板,但 description 必须明确传达"在哪个认知阶段失败"和"是漏做/做错/多做的哪一种"——以便 Phase 4 修复规划和下游聚类能基于自然语言判断"是否同一类失败"。

### 历史:F1–F11 → v1.8.0 映射(已不再使用)

> 仅供从 v1.7.0 历史报告迁移时参考。v1.9.0 不再产出此映射。

| 旧 F | 名称 | v1.8.0 stage | v1.8.0 mode | v1.8.0 rule_violation | scope |
|------|------|-------|------|----------------|-------|
| F1 | 意图理解 | comprehend | wrong | false | in_agent |
| F2 | 任务拆解 | comprehend | missing / wrong | false | in_agent |
| F3 | 上下文获取 | retrieve | missing / wrong | false | in_agent |
| F4 | 结果处理错误 | retrieve / synthesize | wrong | — | in_agent |
| F5 | 行动选择错误 | act | wrong / missing | — | in_agent |
| F6 | 行动调用错误 | act | wrong | — | in_agent |
| F7 | 输出规范错误 | synthesize | wrong | — | in_agent |
| F8 | 规则遵循错误 | 任意 stage | 任意 mode | **true** | in_agent |
| F9 | 执行机制错误(tool/memory) | act | wrong / missing | — | in_agent |
| F10 | 接口设计缺陷 | act | wrong | — | in_agent |
| F11 | 评估器失效 | — | — | — | **external** |

---

## 六、target_layer 与 fix_strategy(仅 Phase 4 使用,定义不变)

> Phase 3 归因阶段**不输出** target_layer。

| 枚举值 | 适合处理的问题 |
|--------|--------------|
| `P0_prompt` | 任务定义、成功标准、边界说明、输出格式约束 |
| `P1_skill` | 描述说明、少样本示例、步骤模板、领域策略、知识补充 |
| `P2_tool` | 工具 schema、参数约束、错误提示、工具集精简 |
| `P3_orchestration` | 路由、状态机、中间件、停止条件、任务拆解策略 |
| `PX_eval` | 评估器规则、参考答案、标注定义(仅人工处理,不进入自动调优)|

### fix_strategy(4 种)

| 策略类型 | 核心思路 |
|---------|---------|
| **约束型修复** | 增加规则、边界、负向示例来限制错误行为 |
| **能力型修复** | 示例、知识补充、步骤模板来增强正确行为 |
| **工程型修复** | 架构调整、工具改造、流程重组 |
| **保障型修复** | 兜底机制、异常处理、监控告警 |

### 修复链路字段填写规范

**格式**:`{component} → {target_layer} · {fix_strategy}`

**示例**:
- `agent:search_agent → P1_skill · 能力型修复`
- `tool:calculator → P2_tool · 工程型修复`

### 层级 × 策略:具体修复手段矩阵(不变)

| target_layer | 约束型修复 | 能力型修复 | 工程型修复 | 保障型修复 |
|--------------|-----------|-----------|-----------|-----------|
| **P0_prompt** | 负向约束·补丁、输出格式约束、边界条件声明 | 正向约束、思维链、任务拆解指引、角色设定 | 指令结构重组 | 自我纠错与反思、输出校验提示 |
| **P1_skill** | 能力边界声明、禁用场景说明 | 少样本示例、领域知识注入、步骤模板、背景信息补充 | Skill 拆分/合并、接口重设计 | 降级策略、兜底输出 |
| **P2_tool** | 参数约束收紧、工具集精简 | 参数示例、错误码说明、返回值解读指引 | 工具重构、Schema 重设计、新工具开发 | 重试策略、异常捕获、超时处理 |
| **P3_orchestration** | 停止条件收紧、路由白/黑名单 | 状态流转示例、拆解策略示例 | 路由逻辑重构、状态机重设计、中间件调整 | 状态回滚、死循环检测、最大轮次限制 |

---

## 枚举值速查

```
scope_enum: [in_agent, external]

component_enum: [agent:{name}, tool:{name}, memory]
# 注:eval 不再是 component,改为 scope=external

rule_violation_enum: [true, false]

target_layer_enum: [P0_prompt, P1_skill, P2_tool, P3_orchestration, PX_eval]

fix_strategy_enum: [约束型修复, 能力型修复, 工程型修复, 保障型修复]
```

---

## 变更日志

| 版本 | 日期 | 类型 | 变更内容 |
|------|------|------|---------|
| v1 | 2026-03-26 | 初始 | 10 种 failure_type + 5 层 target_layer |
| v2 | 2026-03-31 | 重构 | 新增 fix_strategy 4 种策略类型 + 层级×策略修复手段矩阵 |
| v3 | 2026-04-01 | 增强 | 新增渐进式修复路径生成原则 + 三维评分公式 + 修复策略优先级 |
| v3.1 | 2026-04-07 | 增强 | 新增修复内容生成硬约束 7 条(对应 skill v1.6.0) |
| v4 | 2026-04-16 | 重构 | 新增 component 位置维度 + failure_type 重构为 F1–F11 + 合法映射矩阵(对应 skill v1.7.0) |
| v5 | 2026-04-17 | 重构 | failure_type 废弃,替换为 (stage, mode, rule_violation) 正交字段;eval 从 component 移出为 scope=external;归因输出改为 root_causes[] + causal_edges(对应 skill v1.8.0) |
| v6 | 2026-04-29 | 简化 | 移除 stage / mode 字段;归因结构维度坍缩为 (component, rule_violation),失败语义下沉到 description / evidence 自由文本(对应 skill v1.9.0、planner v2.1) |
