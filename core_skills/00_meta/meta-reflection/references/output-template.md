# Output Template (v1)

每次 meta-reflection 输出严格按此格式。文件名按 stage 层级——S1/S2 → `{analysis_root}/meta_reflection/{stage}.md`（experiment 级），S3/S4 → `{round_dir}/meta_reflection/{stage}.md`（round 级）。

## 模板

````markdown
# Round {N} / Stage {stage_id} 元反思

本轮 {stage_id} 在哪些地方走了弯路、丢了信号。{X} 条按"是否值得做"分组，
每条扫读 ≤ 20 秒。

> Snapshot：baseline=... / threshold=... / tolerance=... / sample={N}target+{M}guardrail / scorer_variance=...
>（数字一致性维度的输入；找不到就标 unknown，本身可能是一条洞察）

## 🔴 P0 必修（{count} 条）

**1. {≤ 30 字结论}**
- 证据：{具体 artifact 字段 / 行号 / 数字对比}
- 原因：{≤ 20 字诊断}
- 建议：{具体到能开 PR 的动作}
- [ ] 做  [ ] 加 backlog  [ ] 不做

**2. ...**（同上四段）

## 🟡 P1 建议（{count} 条）

**3. ...**（同上四段）

## 🟢 P2 小修（{count} 条）

**6. ...**（同上四段）

---

## skill 反馈（可选——本轮 skill 自身有问题时写，没有就省略此节）

不是 pipeline 问题——是**本 skill 自身的问题**。详见 SKILL.md Step 6 的 4 类标签。

- **[input_mismatch | P1]** stages/S4.md L18 写 `eval_results/scored_run{1,2,3}.csv`，本项目实际是 `scored_run_1.csv` / `scored_run_2.csv` / `scored_run_3.csv`（下划线分隔）
  - 建议：路径改用 glob `scored_run_*.csv`
- **[taxonomy_gap | P2]** D 类需要 conversation log，但 batch 跑 skill 时 context 不一定有
  - 建议：D 类原理段加一句"如果 conversation 不可访问，fall back 到跨轮 progressive_log delta"

---

```yaml
# 机器消费区（人类可折叠）
fingerprints:
  - obs-1-kebab-id
  - obs-2-kebab-id
  - obs-3-kebab-id
total_observations: 7
must_fix_count: 3
suggested_count: 3
nice_to_have_count: 1
upstream_carryover_count: 0  # 与上轮重复 P0 的条数
stage_id: S4
round_id: round_6

# 可选：仅当 §skill 反馈段非空时填
skill_feedback:
  - type: input_mismatch
    severity: P1
    location: stages/S4.md L18
    issue: scored_run{1,2,3}.csv 路径与项目实际不符
  - type: taxonomy_gap
    severity: P2
    location: SKILL.md Step 2 D 类
    issue: D 类需要 conversation log 但 context 可用性不稳定
```
````

## 写作约束

| 项 | 约束 |
|---|---|
| 全文长度 | ≤ 1500 字 |
| 单条 obs 主体 | ≤ 80 字（不含 checkbox） |
| P0 数量 | ≥ 1（或显式声明"本轮无 P0"） |
| 总 obs 数 | 5-8 条最佳 |
| 证据 | 必须含具体 artifact 字段 / 行号 / 数字 |
| 主语 | 元过程组件，不是 agent 业务 |

## fingerprint 命名约定

每条 obs 一个 kebab-case 稳定 ID，用于跨 round dedup。规则：

- 全部小写 + 连字符
- 长度 ≤ 60 字符
- **核心是 stable**：同一类问题在不同 round 应该 hash 到相同 fingerprint
- 推荐结构：`<axis>-<component>-<problem>` 例如：
  - `signal-d1-baseline-not-stable-snapshot`
  - `policy-fix-plan-rollback-not-machine-readable`
  - `signal-baseline-unit-inconsistent`

不要用日期 / round 号 / iter 号 — 那不稳定。

## 例子（节选自 已验证轮次 / S4 实测）

```markdown
**1. D1 看不到 iter 之间的退化**
- 证据：iter_22 实际丢了 5 条已修好的 turn（S4T3 / S10T10 / S10T11 /
  S11T3 / S12T21），但 D1 报告 regressions=0 → COMMIT
- 原因：D1 比的是 baseline（target turn 全 0，永远不可能 1→0），不是
  上次 COMMIT 后的状态
- 建议：D1 加第二份比较——candidate vs 上次 stable snapshot，退化超
  tolerance 即 ROLLBACK
- [ ] 做  [ ] 加 backlog  [ ] 不做
```

对应 fingerprint：`signal-d1-baseline-not-stable-snapshot`
