# fix_plan 模板与 Schema

本文件包含 auto-fix-planner 产出的所有 artifact 的模板和格式规范。

---

## 1. fix_plan.md 模板

```markdown
# 修复方案 — {{analysis_id}}

**生成时间**: {{timestamp}}
**输入**: feedback.json ({{total_cases}} cases, {{adopted_count}} adopted) + Agent 源码 ({{agent_files_path}})
**轮次**: round_{{N}}
**状态**: draft / approved

---

## 全局规则

### 继承约束（from repair-principles-v1.6.0.md）

以下约束对所有 FIX 项和所有 Iteration 生效，Executor 执行每项修改时须检查是否违反：

1. **Anti-Few-shot**：禁止枚举式示例，优先纯逻辑原则
2. **Agent 能力边界**：Master Agent 仅路由/整合，Sub-Agent 在 skill 范围内生成内容
3. **路由/编排优先**：现有架构有对应子 Agent → 先修路由
4. **知识/数据优先**：先补知识 → 再加逻辑
5. **工具优先**：计算/查询/格式问题 → 工具层解决
6. **Step 1 充分性**：Step 1 须独立解决或显著缓解核心问题
7. **新 Skill 创建门槛**：高频 + ROI 合理 + 清晰能力边界

### 本轮增量约束

{{#each incremental_constraints}}
- {{constraint_text}} — 出现在 {{frequency}} 条 feedback 中
{{/each}}

---

## Iteration 编排总览

| Iter | 类型 | 描述 | 包含 FIX | requires | blocked_by_tickets | target cases | 预期效果 |
|------|------|------|---------|----------|-------------------|-------------|---------|
{{#each iterations}}
| {{iter_id}} | {{type}} | {{description}} | {{fixes}} | {{requires}} | {{blocked_by_tickets}} | {{target_cases}} | {{expected_outcome}} |
{{/each}}

---

## Iteration 详情

{{#each iterations}}
### {{iter_id}}: {{description}} `type: {{type}}`{{#if requires}} `requires: [{{requires}}]`{{/if}}{{#if blocked_by_tickets}} `blocked_by_tickets: [{{blocked_by_tickets}}]`{{/if}}

**target cases**: {{target_cases}}
**expected_outcome**: {{expected_outcome}}

{{#each fixes}}
#### {{fix_id}}: {{title}}

**意图层（Executor 不可修改）**

| 字段 | 值 |
|------|---|
| fix_id | {{fix_id}} |
| title | {{title}} |
| root_cause | {{root_cause}} |
| source_root_causes | {{source_root_causes}} |
| source_cases | {{source_cases}} |
| derivation_note | {{derivation_note}} |
| target | {{target}} |
| constraints | {{constraints}} |
| expected_tradeoffs | {{expected_tradeoffs}} |
| regression_scope | {{regression_scope}} |
| fix_strategy | {{fix_strategy}} |
| target_layer | {{target_layer}} |

**实现层（Executor 可细化）**

| 字段 | 值 |
|------|---|
| fix_location | {{fix_location}} |
| before | {{before}} |
| after | {{after}} |
| implementation_notes | {{implementation_notes}} |

{{/each}}
---

{{/each}}

## 人工工单

| Ticket | 类型 | 相关 FIX | 来源 case | 原因 |
|--------|------|---------|----------|------|
{{#each tickets}}
| {{ticket_id}} | {{type}} | {{related_fix}} | {{source_case}} | {{reason}} |
{{/each}}

详见 `fix_tickets/` 目录。

---

## 覆盖验证矩阵

| Case | Verdict | 归因根因 | 覆盖 FIX | Iteration | 状态 |
|------|---------|---------|---------|-----------|------|
{{#each all_cases}}
| {{case_id}} | {{verdict}} | {{root_cause}} | {{covering_fix}} | {{iteration}} | {{status}} |
{{/each}}

---

## 交互效应检查

{{#if interaction_warnings}}
{{#each interaction_warnings}}
⚠️ **{{fix_i}} × {{fix_j}}**: {{description}}
- 建议: {{recommendation}}
{{/each}}
{{else}}
未发现 FIX 间交互矛盾。
{{/if}}

---

## 不动项说明

| 文件 | 不改原因 |
|------|---------|
{{#each unchanged_files}}
| {{file}} | {{reason}} |
{{/each}}

---

## 熔断条件

| 级别 | 条件 |
|------|------|
| 通过 | target cases 改善率 ≥ 50% 且 非预期退化 ≤ 2 turns |
| 警告 | target cases 改善率 < 50% 或 非预期退化 3-5 turns |
| 熔断 | 非预期退化 > 5 turns 或 净通过率下降 |

## 回滚策略

1. 回退最后执行的 Iteration（依赖链逆序）
2. 仅保留 type: 基础 的 Iterations
3. 完全回退到基线

## 验证要点

- target cases 中每个 turn 的预期修复机制
- 需抽样回归验证的已通过 turn（与改动文件相关的 turn）
```

---

## 2. reviewer_findings.json Schema

```json
{
  "analysis_id": "badcase_analysis_XXXXXX",
  "round": 1,
  "reviewer_model": "codex-cli | claude-code | manual | skipped",
  "reviewed_at": "2026-04-10T15:30:00Z",
  "plan_hash": "<sha256 of fix_plan.md draft>",
  "findings": [
    {
      "id": "RF_001",
      "severity": "high | medium | low | info",
      "target_fix": "FIX_003 | global",
      "target_iteration": "iter_2 | null",
      "category": "逻辑冲突 | 约束违反 | 覆盖遗漏 | 副作用风险 | 编排问题",
      "finding": "问题描述",
      "recommendation": "建议的修改方式",
      "adopted": "true | false | null (未审阅)"
    }
  ],
  "summary": {
    "total": 5,
    "by_severity": {
      "high": 1,
      "medium": 2,
      "low": 1,
      "info": 1
    }
  }
}
```

### severity 级别说明

| 级别 | 含义 | HITL 处理 |
|------|------|---------|
| high | 可能导致修复失败或引入严重退化 | 必须在 HITL 中处理 |
| medium | 潜在风险，建议调整 | 建议处理 |
| low | 优化建议，不影响主流程 | 可选处理 |
| info | 信息性说明 | 仅供参考 |

### category 枚举说明

| 类别 | 含义 |
|------|------|
| 逻辑冲突 | FIX 项之间存在矛盾或互相破坏 |
| 约束违反 | FIX 内容违反全局规则段的约束 |
| 覆盖遗漏 | 有 adopted case 未被任何 FIX 覆盖 |
| 副作用风险 | expected_tradeoffs 不完整或存在未声明的风险 |
| 编排问题 | Iteration 排序/依赖/分组不合理 |

---

## 3. fix_tickets/ticket_NNN.md 模板

```markdown
# Ticket NNN: {{title}}

**类型**: {{PX_eval / P2_tool / P3_orchestration / 其他}}
**来源 case**: {{case_id}}
**原因**: {{why_not_auto}}

## 问题描述

{{detailed_description}}

## 建议处理方式

{{recommended_action}}

## 相关信息

- 相关 FIX: {{fix_id (if any)}}
- 归因报告: case_report_{{case_id}}.md
- feedback 原文: "{{feedback_text}}"
```

---

## 4. 改动日志段模板

追加在 fix_plan.md 末尾，记录 Reviewer 和 HITL 阶段的所有改动：

```markdown
## 改动日志

| 来源 | 改动 | 原值 | 新值 |
|------|------|------|------|
{{#each changes}}
| {{source}} | {{description}} | {{old_value}} | {{new_value}} |
{{/each}}
```

---

## 5. 历史教训清单模板

文件位置：`{analysis_root}/iterations/lessons_learned.md`

Round 2+ 时由 Planner 在 Step 1 回流阅读完成后创建或追加更新。跨轮次累积，不删除已有条目。

```markdown
# 历史教训清单
> 最后更新: round_{{N}}, {{YYYY-MM-DD}}

## 已验证有效的策略
| 策略 | 验证轮次 | 证据 |
|------|---------|------|
{{#each effective_strategies}}
| {{strategy}} | {{round}} | {{evidence}} |
{{/each}}

## 已证明无效的策略（禁止重复）
| 策略 | 失败轮次 | 失败原因 |
|------|---------|---------|
{{#each failed_strategies}}
| {{strategy}} | {{round}} | {{reason}} |
{{/each}}

## 反复出现的退化模式
| 模式 | 出现轮次 | 防范措施 |
|------|---------|---------|
{{#each degradation_patterns}}
| {{pattern}} | {{rounds}} | {{prevention}} |
{{/each}}
```
