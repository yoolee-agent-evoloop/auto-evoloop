# Optimization Report Template

> 模板版本: v1.2（适配 feedback.json schema 2.2：scorer_feedback 正交化 + affects_score 控制剔除）
> 使用方式: auto-fix-executor 在 EXIT 后根据此模板生成 `optimization_report.md`
> 每个维度必须有具体数据支撑，不可使用空泛描述

---

## 1. 总览指标 (Overall Metrics)

**数据来源**: `compare_full.json` summary 段；`scorer_excluded_turns` 来自 feedback.json (schema 2.2)

> **schema 2.2 剔除说明**：以下通过率分子分母均已剔除 feedback.json 中 `scorer_feedback.affects_score === true` 的 (session, turn)；剔除明细见 §8。任何 verdict（accept / revise / reject）都可能附 scorer_feedback；此处只剔除 affects_score=true 的子集。

| 指标 | Baseline | Candidate | Delta |
|------|----------|-----------|-------|
| 有效通过率（剔除后） | {baseline_pass}/{baseline_total_eff} ({rate}%) | {candidate_pass}/{candidate_total_eff} ({rate}%) | {delta}% |
| 质量退化 | — | {quality_regressions} | — |
| 空输出退化 | — | {empty_output_regressions} | — |
| 改善 | — | {improvements} | — |
| **affects_score=true 剔除** | {excluded_count} 条 ({excluded_pct}% of full sample) | — | — |
| scorer_feedback 总条数（含未剔除） | {sf_all_count} 条（含理由瑕疵 / 评分结果对的 C 情形 case） | — | — |

> **WARN（条件输出）**：当 `excluded_pct > 20%` 时强制追加："⚠️ 评估器问题占比异常高 ({excluded_pct}%)，建议优先迭代评分 prompt 再进入下一轮 fix。"
> 注意：阈值用的是 affects_score=true 占比，不是 scorer_feedback 总占比——后者高不一定表示评分器整体不可用。

---

## 2. Session 级对比 (Per-Session Comparison)

**数据来源**: `compare_full.json` per_session 段

| Session | Baseline | Candidate | Delta | 标记 |
|---------|----------|-----------|-------|------|
| {sn} | {pass}/{total} ({rate}%) | {pass}/{total} ({rate}%) | {delta}% | {!! if delta < -5%} |

---

## 3. 改善归因分析 (Improvement Attribution)

**数据来源**: `compare_full.json` changes (change == "improvement") + fix_plan FIX 映射

> 本节统计已剔除 feedback.json 中 `scorer_feedback.affects_score === true` 的 (session, turn)；剔除明细见 §8。

对每条改善，追溯到哪个 Iter 的哪个 FIX 导致了改善：

| Session | Turn | 改善原因 (ai_reason_b) | 归因 FIX | 归因 Iter |
|---------|------|----------------------|---------|----------|

总结：N 条改善中，M 条可归因到具体 FIX，K 条为间接效应。

---

## 4. 退化归因分析 (Regression Attribution)

**数据来源**: `compare_full.json` changes (change == "regression") + expected_tradeoffs

> 本节统计已剔除 feedback.json 中 `scorer_feedback.affects_score === true` 的 (session, turn)；剔除明细见 §8。

### 4.1 预期退化 (Expected)

退化原因匹配 fix_plan 中某个 FIX 的 expected_tradeoffs：

| Session | Turn | 退化原因 | 匹配的 expected_tradeoff | FIX |
|---------|------|---------|------------------------|-----|

### 4.2 非预期退化 (Unexpected)

退化原因不匹配任何 expected_tradeoffs：

| Session | Turn | 退化原因 | 可能原因分析 |
|---------|------|---------|------------|

### 4.3 空输出退化

Agent 环境问题导致的空输出，非代码质量问题：

| Session | Turn | 备注 |
|---------|------|------|

---

## 5. 退出判断回顾 (Exit Decision Review)

**数据来源**: `progressive_log.json` iterations

| Iter | Type | D1 | D1 Rationale | D2 | D2 Rationale |
|------|------|----|--------------|----|--------------|

执行摘要：共 {N} 个 Iter，{M} COMMIT，{K} ROLLBACK，{J} SKIPPED。

ROLLBACK 复盘（每个 ROLLBACK 的 Iter）：
- iter_{X}：失败原因 + 改进方向建议

---

## 6. 优化目标对照 (Target Alignment)

**数据来源**: fix_plan target_cases + compare_full.json

| Case ID | fix_plan 预期 | 实际结果 | 状态 |
|---------|-------------|---------|------|

状态分类：
- ✅ 完全改善：所有关联 turn pass
- ⚠️ 部分改善：部分 turn pass
- ❌ 未改善：与 baseline 相同
- 🔻 退化：比 baseline 更差

达成率：{M}/{N} target cases 完全改善

---

## 7. 性能开销 (Performance Overhead)

**数据来源**: eval_results CSV 中的 latency 和 total_tokens 列

| 指标 | Baseline 均值 | Candidate 均值 | Delta | 标记 |
|------|-------------|---------------|-------|------|
| 响应延迟 (s) | | | | {⚠️ if delta > 20%} |
| Token 消耗 | | | | {⚠️ if delta > 20%} |

---

## 8. 疑似评估器问题 (Suspected Scorer Issues)

**双通道数据来源**（schema 2.2）：
- (a) **S2 通道**：feedback.json 中所有填了 `scorer_feedback` 的 case（`scorer_feedback_all`）。任何 verdict 都可能命中（accept/revise/reject 均可附 scorer_feedback）
- (b) **S4 通道**：本轮 baseline / candidate scored CSV 中 ai_analysis 和 ai_reason 自动审查发现的可疑 case

| Session | Turn | source | S2 case_id | S2 verdict | affects_score | 原 baseline_score | 原 candidate_score | ai_reason 摘要 | 人工建议改写（≤100 字截断） | 可疑原因 |
|---------|------|--------|------------|------------|---------------|-------------------|--------------------|----------------|--------------------------------|---------|

> `source` 取值：
> - `S2_scorer_feedback`：S2 HITL 标注，`S2 case_id` + `S2 verdict` + `affects_score` + `人工建议改写`（来自 scorer_feedback.suggested_revision）必填
> - `S4_baseline_diff`：S4 自动审查发现，`S2 *` / `affects_score` / `人工建议` 可空

**S4 自动审查标准**（仅 S4 通道命中）：
- 评分理由与 actual_output 内容不符
- 相同或极相似的输出在不同 turn 得到不同评分
- 评分理由提到了 actual_output 中不存在的内容

> **重要**：
> - 本表中所有 source=S2_scorer_feedback **且 `affects_score=true`** 的 (session, turn) 已经从 §1 / §3 / §4 的统计中剔除（不计入分子分母）
> - source=S2_scorer_feedback **但 `affects_score=false`** 的 case 不剔除（评分理由瑕疵但结果对，不污染统计），仅作为下一轮 prompt 迭代的候选
> - S4 自动发现的 case **不**自动剔除（避免双重排除人工未确认的 case），仅作为下一轮 prompt 迭代的候选

### 8.1 反馈聚合到 scorer_feedback markdown

Executor 把本表完整内容 + 所有 S2_scorer_feedback case 的 scorer_feedback 详情（含未剔除的 C 情形）写入：

```
projects/<biz>/evoloop/scorer_feedback/<YYYYMMDD>_<exp_id>.md
```

**生成规则**：
- `<biz>` 取自 `agent_files_path` 的业务标识（如 biz_a / biz_b / biz_c）
- `<YYYYMMDD>` 是 round 启动日期
- `<exp_id>` 取自 fix_plan.md 的 experiment 字段
- 文件结构遵循 `core_skills/04_execute/auto-fix-executor/references/scorer_feedback_template.md`（SoT 模板）；运行时第一次写入时 mkdir `projects/<biz>/evoloop/scorer_feedback/` 即可，无需预先创建空目录

**关键约束**：S4 不自动 override 评分（评分链路保持只读）；该 markdown 仅供下一轮人工迭代评分 prompt 离线消费。如果维护者根据 markdown 改了 biz_a_score.md 等评分 prompt，下一轮 eval 用新 prompt 重跑即可。

---

## 9. 下一步建议 (Next Steps)

**数据来源**: 综合以上 8 个维度

基于分析，建议：

**(A) 如 improvements > 0 且 unexpected quality regressions == 0：**
→ 建议 merge `evoloop/round_{N}`，新版 Agent 生效。
→ 可用新版 Eval 结果开启新一轮 auto-trace-prep。

**(B) 如 improvements > 0 但 unexpected quality regressions > 0：**
→ 建议回流 auto-fix-planner（路径 B）。
→ 重点关注：{列出非预期退化的 case 和可能原因}
→ `progressive_log.json` 的 summary 段已准备好供 S3 消费。

**(C) 如 improvements == 0：**
→ 建议三选一：
  1. 回流 S1/S2 重新分析（可能原始归因有误）
  2. 回流 S3 调整方案（方案方向可能有误）
  3. 人工介入（超出自动化能力范围）
