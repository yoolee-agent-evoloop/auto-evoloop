---
biz: <biz_a | biz_b | biz_c>
exp_id: <experiment id from fix_plan.md>
round: <round number>
generated_at: <ISO 8601 timestamp>
schema_version: "2.2"
source_count:
  s2_scorer_feedback: <integer>      # S2 HITL 中所有填了 scorer_feedback 的 case 数
  s4_baseline_diff: <integer>        # S4 自动审查发现的可疑 case 数
affects_score_count: <integer>       # s2_scorer_feedback 中 affects_score=true 的子集数（=剔除统计的数量）
total_full_turns: <integer>
excluded_pct: <float, 0-100>         # = affects_score_count / total_full_turns × 100
---

# Scorer Feedback · {biz} · {exp_id} · round {N}

> 由 auto-fix-executor 在 §4.3 optimization_report 生成时同步产出。**本文档仅供下一轮人工迭代评分 prompt 离线消费**——不是 skill 自动闭环输入。如果维护者根据本文档改了 `scripts/score/<biz>_score.md`，下一轮 eval 用新 prompt 重跑即可。

## 1. 汇总

- **本轮 scorer_feedback 总数**（含理由瑕疵 / 评分结果对的 C 情形）：N 条
- **本轮剔除**：M 条（其中 affects_score=true 的子集，从 baseline/candidate pass 率统计中剔除）
- **剔除占比**：X% / 全样本 turns（仅 affects_score=true 计入）
- **WARN 触发**：是 / 否（剔除占比 > 20% 时是）

> 本文档汇聚 schema 2.2 的所有 scorer_feedback（不论是否剔除统计）。三种典型情形：
> - **A 情形**：reject + scorer_feedback{misjudge_pattern=score_wrong} → affects_score=true — 原 scorer_misjudge
> - **B 情形**：revise + revision + scorer_feedback — agent 真错 + 评分理由也错（schema 2.1+ 核心修正点）
> - **C 情形**：accept + scorer_feedback{misjudge_pattern=reason_wrong_only} → affects_score=false — 理由瑕疵但结果对

## 2. 详细列表

| # | source | session | turn | S2 case_id | S2 verdict | affects_score | 原 baseline_score | 原 candidate_score | rubric_ref | misjudge_pattern | 人工建议改写 | trace_excerpt |
|---|--------|---------|------|------------|------------|---------------|-------------------|--------------------|------------|-------------------|---------------|---------------|
| 1 | S2_scorer_feedback | 13 | 5 | case_017 | reject | true | 0 | 0 | biz_a_score.md §3.1 | score_wrong | 评分理由说 agent 重复了 user_query，但 trace 显示 agent 给出了新增地址 ABC——Rubric 应识别该改写不属于重复 | （前 200 字 actual_output 摘录） |
| 2 | S2_scorer_feedback | 14 | 12 | case_023 | revise | false | 0 | 1 | biz_a_score.md §3.2 | reason_wrong_only | 评分说 agent 没推进销售，但 trace 显示 agent 已 handoff 给销售 | （摘录） |

> `source` 列：
> - `S2_scorer_feedback`：S2 HITL 标注（任何 verdict 都可附），`affects_score` 字段决定是否剔除统计；`S2 case_id` / `S2 verdict` / `rubric_ref` / `misjudge_pattern` / `人工建议改写` 必填
> - `S4_baseline_diff`：S4 自动审查发现的可疑 case，`S2 *` / `affects_score` / `rubric_ref` / `人工建议改写` 可空，仅 `misjudge_pattern` 由自动审查给出推断

## 3. 建议的评分 prompt 修改点

> 维护者根据上表归纳建议改写，落到 `scripts/score/<biz>_score.md` 的具体 §章节。本节由人类填写，Executor **不**自动生成具体 prompt 修改文本。

- **§3.1（零重复）**：…
- **§3.2（正面解决）**：…
- **§（其他章节）**：…

## 4. 跟进

- [ ] 维护者：根据 §3 修改 `scripts/score/<biz>_score.md`
- [ ] 维护者：用新 prompt 跑一遍上一轮的全样本 eval（仅评分，不重跑 agent），验证 §2 列出的 case 是否得到正确分
- [ ] 维护者：把改后版本的 evaluator 报告链接 / commit 记录在本文件末尾
- [ ] 下一轮 round_{N+1} 走 fix 流程时，使用新评分 prompt（affects_score=true 的占比应显著降低）
