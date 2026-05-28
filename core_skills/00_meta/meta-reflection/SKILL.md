---
name: meta-reflection-v1
description: >
  在 evoloop 任一 stage（S1 / S2 / S3 / S4）出口做元过程反思——产出
  人类可决策的洞察清单，按 P0 必修 / P1 建议 / P2 小修 三档分组，
  每条 ≤ 80 字 + review checkbox（[ ] 做 / 加 backlog / 不做）。

  ALWAYS use 当用户提到：反思 / 复盘 / 元反思 / "这一轮哪里有问题" /
  各 stage 出口的 meta_reflection / 跨层信号未被消费 / 设计层漏洞。

  输入：当前 stage 的 round artifact（progressive_log / fix_plan /
  feedback / attribution，按 stage 不同）。
  输出：单文件 markdown，路径 `{round_dir}/meta_reflection/{stage}.md`。

  Scope：只反思元过程（fix_plan / D1 / sample / scorer 的设计与流转），
  不反思 agent business domain 内容（"agent 应该回答 XXX" / "prompt 加 YYY"
  这类内容立刻停下）。
---

# Meta-Reflection (v1)

每跑完一个 stage 做一次元反思——找的不是"agent 哪条 case 答错了"（那是
single-case-analyzer 的活），是"我们用来跑 stage 的方法论本身有没有结构性漏洞"。

v1 设计原则：MVP + 人类可读 + 可决策。每条 obs 扫读 20 秒决定做不做；累积 ≥ 5 轮后做一次 meta 升级。

## 路径变量

- `{analysis_root}` = `badcase_analysis_{MMDDHH}/`（auto-trace-prep 创建，S1/S2 工作目录）
- `{experiment_root}` = `projects/<biz>/evoloop/experiments/<exp_id>/`
- `{round_dir}` = `{experiment_root}/rounds/round_N/`（S3 开始才存在，承载 S3/S4 产物）
- legacy 路径（`projects/<biz>/.../iterations/round_N/`）兼容，自动检测

**stage 与产物层级对应**：
- **S1 / S2**：experiment 级，无 round_N → 输出到 `{analysis_root}/meta_reflection/{stage}.md`
- **S3 / S4**：round 级 → 输出到 `{round_dir}/meta_reflection/{stage}.md`

> **encoding 硬规则**：所有 `open()` / py 内联脚本必须显式 `encoding='utf-8'`。
> Windows Python 默认 GBK，写中文 prose 不加 encoding 必崩。

## Step 1：判断 stage 并加载对应模块

| stage_id | 对应 stage skill | 何时跑 | 加载模块 |
|---|---|---|---|
| S1 | auto-trace-prep | analysis_manifest.json (confirmed) 写完后 | `stages/S1.md` |
| S2 | auto-single-case-analyzer | feedback.json / attribution 写完后 | `stages/S2.md` |
| S3 | auto-fix-planner | fix_plan.md (approved) 写完后 | `stages/S3.md` |
| S4 | auto-fix-executor | progressive_log + optimization_report 写完后 | `stages/S4.md` |

> S1/S2/S3 模块是 **draft（未实测）**——v1 只在 S4 做过 已验证轮次 实测。其他 stage
> 跑出来的洞察 review 时记得标 calibration 不足。

读对应模块文件，把里面的"特有失效模式"和"输入 artifacts"作为 Step 2 brainstorm 的输入。

## Step 2：扫 4 类决策机制失效根因（内部思考，不输出）

元反思的 core question 不是"找 N 类问题"，是"**我们用的决策机制还能继续用吗**"。

下面 4 类是 input / process / output / time 的 MECE 切分——任何 agentic
pipeline 的 stage 都可以套这 4 类找根因。先想清楚每类的**原理**（为什么这类
会发生），再问"本 stage 上有什么具体表现"。**不要被表面相似的现象骗——
表面相同的问题往往是不同根因，不同根因要不同 fix**。

### A · 测量信号不可信
**原理**：决策的输入永远夹杂噪声——抽样代表性差 / 测量工具自身变异 / 工具链
稳定性 / 数据完整性 / 跨 run 一致性，都是噪声源。任何 gate 的判定阈值必须
放在噪声层**之上**才是真 gate；否则 gate 通过等于掷骰子。
→ 本 stage 接收哪些输入？每个输入的 noise 量级度量过吗？哪些"通过"实际
可能在噪声里？

**证据源类型**（泛化，stages/*.md 映射到本 stage 实际 artifact）：测量
工具输出 / 多次运行结果（用于算 variance）/ 工具链脚本（measurement
pipeline 的实现代码）/ 抽样 manifest

### B · 决策规则与现实脱节
**原理**：规则诞生时基于某些假设，假设可能已被违反；或规则在错粒度的输入上
决策；或规则边界有 hole（边界 case / cross-scenario 冲突）。规则定下来后
容易被当成"理所当然"，但产生它的约束条件可能早就变了。
→ 本 stage 的算法 / threshold / tolerance / 截止条件，当初为什么设这个值？
对应的现实约束今天还成立吗？

**证据源类型**：决策算法代码（rule / policy / SKILL.md）/ 规则参数
（threshold / tolerance）/ 规则诞生依据（commit message / DESIGN /
历史 plan / 假设字段）

### C · 跨层信号丢失
**原理**：pipeline 一头写的字段，另一头不读 = prose 装饰 = 设计缺陷。生产端
的承诺（"若 X 则 Y"）必须有消费端的可执行实现；否则承诺是空头支票。决策
依据本身是机器可消费的，还是 prose-only 等人工 parse？
→ 本 stage 的输入字段哪些来自上游？是不是所有上游写的都被读了？反过来
本 stage 写出去的字段下游会读吗？

**证据源类型**：上游 stage 的 artifact schema / 本 stage 对上游字段的
消费代码 / 本 stage 输出 artifact 的 schema / 下游对本 stage 输出的
消费证据

### D · 成本 / 收益曲线
**原理**：单点成本看不出问题，曲线斜率才暴露 pipeline 是否在退化——人工
补救次数 / 同一类问题修了几遍 / 同字段被多个组件重写 / 本轮 vs 上轮的
delta。时间维度的退化是 pipeline 慢性病，不会在某一轮"爆"，会一直闷烧。
→ 本轮 vs 上轮 / 上几轮，哪些指标在单调向坏？

**证据源类型**：跨轮 / 跨 stage 的同类 artifact / 当前会话内 HITL 介入
痕迹（人工补救 / ad-hoc 临时脚本 / 手动同步状态字段）/ 跨 commit 同字段
修改频次

> **每条候选必须挂一个具体证据**（artifact 字段名 / log 行号 / 数字对比）。
> 没证据的不要写——"觉得可能"不算洞察。

## Step 3：按"是否值得做"三档分组

- **🔴 P0 必修**：不修下一轮还会再撞；问题是结构性的；建议动作清晰可开 PR
- **🟡 P1 建议**：方向对但成本 / 收益还需要确认；先讨论
- **🟢 P2 小修**：单点 hygiene，攒一起做就行

每档 1-3 条；总条数 5-8 条最佳，**别凑数**。如本轮真没 P0 → 写一句"本轮无 P0，
连续无 P0ge3 轮请回看本 skill brainstorm 是否漏看了"。

## Step 4：写输出

单文件，路径按 stage 层级：
- S1 / S2 → `{analysis_root}/meta_reflection/{stage}.md`（experiment 级，无 round_N）
- S3 / S4 → `{round_dir}/meta_reflection/{stage}.md`（round 级）

目录不存在则建。

格式严格按 `references/output-template.md` —— 每条 obs 四段：
- 一句话结论（≤ 30 字）
- 证据（具体 artifact / 字段 / 数字）
- 建议动作（具体到能开 PR）
- review checkbox：`[ ] 做  [ ] 加 backlog  [ ] 不做`

文末追加 yaml fingerprint 块（人类折叠不读，机器后续 dedup 用）。

## Step 5：自检 + 人工 review 提示

输出后 LLM 自检：

- [ ] 总长 ≤ 1500 字
- [ ] 每条 obs 主体 ≤ 80 字（不含证据/建议/checkbox）
- [ ] 至少 1 条 P0（或显式声明"本轮无 P0"）
- [ ] 每条 obs 有具体证据（artifact 路径 / 字段 / 数字）
- [ ] 主语是元过程不是 agent 业务

末尾给用户一句话提示：

> 请打开本次写出的 `meta_reflection/{stage}.md`（完整路径见上文 Step 4：S1/S2 在 `{analysis_root}/` 下，S3/S4 在 `{round_dir}/` 下），逐条勾 [做 / 加 backlog / 不做]。
> 累积 ≥ 5 轮后做一次 meta 升级（详见 `references/human-review-checklist.md`）。

## Step 6：skill 自反馈（可选——本轮跑顺了就跳过）

如果你（AI）跑这个 skill 时遇到 **skill 自身的问题**（不是 pipeline 问题），
写到输出文末 §skill 反馈段。常见 4 类标签：

- `input_mismatch`：stages/{stage}.md 列的 artifact 路径在本项目不存在 / 名字不同 / 已迁移
- `prompt_clarity`：SKILL.md 某段读起来歧义，或 4 类原理某条不知道怎么落到本 stage
- `taxonomy_gap`：4 类失效在本 stage 不全适用；或本轮发现一类全新失效（A/B/C/D 都套不上）
- `output_format`：三档分组 / ≤80 字 / fingerprint 结构在本 stage 不顺手

**每条挂具体证据**（"SKILL.md L62 写 X，但实际 Y"）。**没有就跳过这步**——
不要凑无价值反馈。

格式见 `references/output-template.md` 的 §skill 反馈（可选）段。

## Scope 边界

| ✅ 反思元过程 | ❌ 不反思业务 |
|---|---|
| fix_plan schema 是否合理 | agent prompt 该不该加 X |
| D1 是否消费 fix_plan 字段 | agent 某 case 答错原因 |
| sample 是否代表 full | feedback verdict 对错 |
| scorer 是否有偏置 / noise | scorer 单 case 打分高低 |

发现自己在写"agent 应该回答 XXX"或"prompt 加 YYY"——立刻停，这是 business domain。
