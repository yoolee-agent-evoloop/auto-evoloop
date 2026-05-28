# Human Review Checklist (v1)

每次 stage 跑完后 LLM 会写一份 `meta_reflection/{stage}.md`——S1/S2 落在 `{analysis_root}/`（experiment 级），S3/S4 落在 `{round_dir}/`（round 级）。
这个文件是给你（人类）看的——下面是 review 步骤。

## 单轮 review（每次 stage 跑完都做，~5 分钟）

1. 打开当轮 `{stage}.md`
2. 从上往下读，每条 obs 在 checkbox 上勾 1 个：
   - **[x] 做**：本轮 / 下轮就动手——要么直接改代码，要么开 PR / issue
   - **[x] 加 backlog**：记录到外部 backlog 系统，不立即做
   - **[x] 不做**：判断为 false alarm 或不值得；附一句话理由
3. 文末 yaml 块**不读**——那是机器后续 dedup 用的

> review 完成的标志：所有 obs 都恰好勾了 1 个 checkbox。

## 周期性 meta 升级（≥ 5 轮反思后做一次，~30 分钟）

> **触发**：累积 ≥ 5 个 `{stage}.md` 文件 / 或人类觉得"看到的 P0 重复了"

### Step 1 — 收集

```bash
# 列出当前 experiment 下所有 meta_reflection 文件，按 stage 分组
# 同时覆盖 S1/S2（analysis_root 级）和 S3/S4（rounds/ 级）
find projects/<biz>/evoloop -name "S*.md" -path "*/meta_reflection/*" | sort
```

### Step 2 — 按 stage 分组对照

每个 stage 一组，按 round 排序，关注：

- **fingerprint 重复**：同一个 fingerprint 在 ≥ 2 轮 P0 出现 → 该问题是结构性的，必须 upstream 修
- **fingerprint 单点**：只出现一次 → 单点问题，已记入 backlog 即可

可以用简单 grep 提取所有 fingerprints：

```bash
grep -h "^  - " projects/.../meta_reflection/S4.md | sort | uniq -c | sort -rn
```

### Step 3 — 决定 upstream 升级

把"重复 P0"列出来，决定哪些升级到：

| 升级类型 | 修哪里 | 例子 |
|---|---|---|
| 代码修改 | D1 算法 / fix_plan schema / sample 抽样规则 / score.py | "D1 加 stable_snapshot 双基准比较" |
| Prompt 修改 | 本 skill SKILL.md 或 stage 模块 | "S4 模块新增'expected_tradeoffs 未消费'失效模式" |
| 流程修改 | <host_runtime_doc> / DESIGN.md / 团队 wiki | "code review 必须含 'fix_plan 字段被消费' 检查" |

### Step 4 — 沉淀

把决定 upstream 的项目记到 `lessons_learned.md` 或类似归档位置，并：
- 在原 `{stage}.md` 文件里标 `[x] 已 upstream <date> via <PR/commit>`
- 在 backlog 系统标 done

### Step 5 — 累积 skill_feedback 决定 skill 自身演进

除了上面的 pipeline upstream，每个 `{stage}.md` 文末可能有 §skill 反馈段——
那是 AI 跑 skill 时发现的 **skill 自身问题**（不是 pipeline 问题）。

```bash
# 提取所有 stage 文件的 skill_feedback yaml 块
grep -A 20 "^skill_feedback:" projects/.../meta_reflection/*/S*.md
```

按 `type` + `location` 聚合后决定：

- 同一 `location` + `type` 在 ≥ 2 轮出现 → 改 SKILL.md / stages/*.md（**不需要等 5 轮**——skill 自身 bug 是 hygiene 问题，发现即修）
- 单次出现 → 进 skill backlog，下次再现时升级

特别注意：
- `taxonomy_gap` 反复出现 → 4 类原理切分可能有漏，是 skill 演进的高价值信号
- `input_mismatch` 反复出现 → stages 模块没跟项目实际同步，是 skill 维护赤字

## 给本 skill 自己的反思（year-level）

如果发现连续 5+ 轮某个 stage 反思**完全没产出 P0** → 可能是：

- (a) 该 stage 真的稳定了——好事
- (b) brainstorm 4 个面在该 stage 上不灵——需要重写 `stages/{stage}.md` 的"高发失效"
- (c) 该 stage 输入 artifact 太少 / 信号太少——需要补充输入清单

排查 (b)/(c) 才是元反思的元反思。

## 反向：发现 false-positive 也要回流

如果某条 obs 被 review 时**反复勾"不做"**（≥ 3 轮）→ 说明 prompt 在制造无价值噪音：

- 在对应 stage 模块里把那条失效模式标"低价值"或删除
- 在 SKILL.md Step 2 里加一句"避免这类伪洞察"

这两个反向通道（"漏看了一类"和"看了无价值的"）都是 v1 → v1+ 演进的依据。

## 字段补全约定

review 时如果发现 obs 字段不完整（比如证据太空、建议太抽象）：

- 不要靠记忆补全——证据是这一轮 stage 的硬资产，丢了就丢了
- 但可以在 review 文件末尾追加一段"待补"区，下次跑同 stage 时让 LLM 优先补
- 长期看这种"模糊洞察"高频出现 → 在 stage 模块里加"必须挂证据，没证据不要写"硬约束（v1 SKILL.md 已有，但可能在某 stage 上需要再强调）
