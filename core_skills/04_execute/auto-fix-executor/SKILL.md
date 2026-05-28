---
name: auto-fix-executor-v1.0
description: >
  修复执行 skill——读取 approved fix_plan.md，在 Agent 源码上渐进式执行修复，
  通过 eval 工具链逐 Iteration 验证效果，做 D1/D2 双决策，
  产出新版 Agent 文件和 9 维度优化报告。

  核心能力：Agent 源码理解与修改、git branch 快照管理、
  小样本 eval 流水线（extract → run_eval → score → compare --json）、
  D1/D2 双决策状态机、progressive_log.json 持久化与 compact 恢复。

  当用户提到以下任何场景时务必触发此 skill：
  执行修复方案、应用 fix plan、跑修复、执行 iteration、开始自动优化、
  apply fixes、run executor。

  与 auto-fix-planner 的边界：Planner 产出 fix_plan.md (approved)，
  本 skill 消费 fix_plan 执行修复。可细化实现层但不可修改意图层。
  本 skill 不维护自己的 eval 脚本，通过 scripts/ 下的 CLI 工具完成验证。
---

# Fix Executor

读取 approved fix_plan.md 和 Agent 源码，逐 Iteration 应用修复、运行小样本 eval、根据结构化 compare 输出做 COMMIT/ROLLBACK 决策，最终产出新版 Agent 文件和优化效果总结报告。

## 输入

| 物料 | 必选 | 说明 |
|------|:----:|------|
| `fix_plan.md` (approved) | ✅ | S3 产出，`状态: approved`，至少 1 个 Iteration 含自动优化项 |
| `analysis_manifest.json` | ✅ | S1 产出，读取 `agent_files_path`（Agent 源码路径）和 `eval_source`（eval 输入 CSV 路径） |
| `feedback.json` (schema 2.2) | ✅ | S2 产出，`status: "complete"` 且 `schema_version === "2.2"`。用于：(a) 确定 target cases（`verdict != "reject"` 的全部 case）；(b) 提取 `scorer_feedback_all` —— 所有填了 `scorer_feedback` 的 case（不论 verdict、不论 affects_score），用于汇聚到 scorer_feedback markdown；(c) 提取 `scorer_excluded_turns` —— 其中 `scorer_feedback.affects_score === true` 的 case 的 (case_id, session_id, turn_id) 集合，作为 baseline/candidate pass 率统计的剔除集合（见 §scorer_feedback 处理） |
| **Agent 源码** | ✅ | `agent_files_path` 指向的目录（含 `.space/agents/*.md` prompt 文件 + `app/*.py` 代码） |
| Eval 输入 CSV | ✅ | `eval_source` 指向或默认 `projects/biz_a/evals/input_biz_a.csv` |
| Baseline scored CSV | ✅ | 原始 eval 的评分结果，用作 `compare.py -a` 的基线。人工指定或在 `{analysis_root}` 下查找 |
| Scorer prompt | ✅ | 默认 `scripts/score/biz_a_score.md`，业务专属评分提示词 |

> **路径变量定义**（v3.3 新结构）：
>
> - **`{experiment_root}`**：一个 experiment 的根目录，形如 `projects/<biz>/evoloop/experiments/<exp_id>/`
> - **`{analysis_root}`**：`{experiment_root}/analysis/`——S1/S2 产物（feedback.json、reports/、traces/）所在目录
> - **`{round_dir}`**：`{experiment_root}/rounds/round_N/`（N 从 fix_plan.md 的轮次字段获取）
>
> **定位规则**：feedback.json 所在目录即为 `{analysis_root}`。若 `{analysis_root}` **自身**的目录名为 `analysis`（即 feedback.json 路径形如 `.../experiments/<exp_id>/analysis/feedback.json`），则 `{experiment_root}` = `{analysis_root}` 的父目录（v3.3 新结构）；否则走 legacy 路径，`{round_dir}` = `{analysis_root}/iterations/round_N/`（v3.2 旧结构）。

## 输出 Artifact

```
{experiment_root}/rounds/round_N/
├── execution/
│   ├── diffs/                        # per-Iter 变更 diff（git diff 输出）
│   ├── new_agent_files/              # 最终 stable_snapshot 的 Agent 文件副本
│   ├── eval_results/
│   │   ├── baseline_sample.csv       # baseline 子集（匹配 sample sessions）
│   │   ├── sample.csv                # 冻结的小样本输入（target + guardrail 合并）
│   │   ├── output_iter{N}.csv        # 每 Iter 的 eval 原始输出
│   │   ├── scored_iter{N}.csv        # 每 Iter 的评分结果
│   │   ├── compare_iter{N}.json      # 每 Iter 的 compare --json（D1 输入）
│   │   ├── output_full.csv           # 全样本 eval（EXIT 后）
│   │   ├── scored_full.csv           # 全样本评分
│   │   └── compare_full.json         # 全样本对比
│   ├── sample_manifest.json          # 冻结的小样本构成清单
│   ├── progressive_log.json          # 每 Iter 的状态持久化（核心）
│   └── execution_observations.jsonl  # 执行过程观察记录（试点，见下文 §执行观察记录）
└── optimization_report.md            # 9 维度优化总结（见 references/）
```

---

## 前置条件检查

> skill 启动时按以下顺序执行检查。任一项失败则停止并报告。

1. **定位 fix_plan.md**：在 `{round_dir}` 下找到 approved 的 fix_plan.md（新结构路径：`{experiment_root}/rounds/round_N/`；legacy 路径：`{analysis_root}/iterations/round_N/`）。验证 `状态: approved`。从中确定 `{round_dir}` 和轮次 N。

2. **定位 analysis_manifest.json**：在 `{analysis_root}/` 下读取。提取 `agent_files_path` 和 `eval_source`。

3. **定位 feedback.json**：在 `{analysis_root}/` 下读取。验证 `status: "complete"` 且 `schema_version === "2.2"`（≠ "2.2" 直接报错并要求用最新 viewer 重新生成）。提取：
   - **target case 列表**：所有 `verdict != "reject"` 的 case，用于 §小样本构成
   - **`scorer_feedback_all`**：所有填了 `scorer_feedback` 的 case（不论 verdict、不论 affects_score）。**任何 verdict 都可附加 scorer_feedback**——它是顶层正交字段。该集合用于汇聚到 `projects/<biz>/evoloop/scorer_feedback/<YYYYMMDD>_<exp_id>.md` 离线 markdown，供下一轮人工迭代评分 prompt
   - **`scorer_excluded_turns`**：`scorer_feedback_all` 中 `scorer_feedback.affects_score === true` 的 case 的 (case_id, session_id, turn_id) 集合。session_id / turn_id 通过 analysis_manifest.json 的 cases 数组映射。该集合在 baseline/candidate pass 率统计阶段从分子分母**双侧剔除**；剔除明细单独入 optimization_report §8（见 §scorer_feedback 处理）

4. **验证 Agent 源码**：确认 `agent_files_path` 目录存在且是 git 仓库（或在 git 仓库内）。

5. **验证 eval 工具链**：从 analysis_manifest.json 读取 `eval_runner` 字段——指向 runner 可执行脚本的相对路径，由 framework-version 在 manifest 中声明。验证：
   - `manifest.eval_runner` 字段存在且文件可访问；缺失则 AskUserQuestion 由用户提供
   - 框架无关的下游工具链存在：`scripts/score/score.py`、`scripts/score/compare.py`、`scripts/small_sample/extract_sample.py`

   > **解耦原则**：executor 不识别具体 runner 名，也不假设其 CLI 形态、依赖（Redis / 直接 HTTP / 其他）、是否启停服务。具体 runner 的调用细节由 runner 自身的 guide 文档维护（如 `scripts/run_eval/<framework-version>/*_guide.md`）；executor 仅按 manifest 提供的路径与 §8 声明的服务生命周期标志进行抽象决策。

6. **确认 baseline scored CSV**：如用户未指定，在 `{analysis_root}` 或 `scripts/score/` 下查找。如无法确定，AskUserQuestion。验证提取行数 > 0（双重 BOM 可能导致 session 过滤失效返回 0 行）。

7. **验证 <SCORER_KEY_ENV>**：运行 `$PY -c "import os; k=os.environ.get('<SCORER_KEY_ENV>',''); print(f'<SCORER_KEY_ENV>: {\"OK\" if k else \"MISSING\"}')""`。如 MISSING，提示用户在 `<credential_store>` 中配置 `<SCORER_KEY_ENV>`。

8. **确认服务生命周期**：从 manifest 读 `service.lifecycle` 标志——值为 `external` 或 `runner_managed`。

   > **新 manifest 最佳实践（强烈推荐）**：新建 manifest 时**显式声明** `service.lifecycle`，避免依赖运行时推断。Schema 校验阶段就把 `lifecycle` 列为推荐字段，让配置错误在写 manifest 时被发现，而不是 round 执行时才暴露。
   >
   > 下列推断逻辑**仅作为兼容旧 manifest 的 fallback**，不是常规路径——

   **未显式声明时按下列字段存在性自动判定**（从上到下首次命中即生效；任一推断分支命中时**必须**先打印 WARN 日志：`[WARN] manifest 未声明 service.lifecycle，按 {推断结果} 处理（基于规则: {命中规则编号}）；建议在 manifest 中显式声明以避免歧义`）：

   | 编号 | 检查 | 命中行为 |
   |---|---|---|
   | 0 | `service.lifecycle` 显式声明 | 按声明执行（**不打 WARN**，正常路径） |
   | 1 | 未声明 + `service.health_url` 存在 | 走 `external`；eval 前 HEAD/GET 探活；不可达 AskUserQuestion |
   | 2 | 未声明 + `server_start_cmd` 存在 + 无 `health_url` | 走 `runner_managed`（向后兼容旧 manifest） |
   | 3 | 未声明 + 两者皆无 | AskUserQuestion 让用户补 `health_url`（推荐 external）或 `server_start_cmd`（runner_managed），**不要默认猜测** |

   - **`external`（推荐路径）**：服务由外部维护（用户终端 / CI / 常驻进程）。eval 前发 HEAD/GET 探活，不可达时 AskUserQuestion 让用户启动服务后重试。executor 不启停服务，不向 runner 注入 `server_start_cmd`。
     > **为何推荐 external**：N 个 Iter 串行执行时，`runner_managed` 每 Iter 启停一次服务（冷启动 + Redis 连接初始化 + agent 编译，单次 ~5-15s × N Iter），`external` 模式下服务一次启动全 round 复用，节省 N×启动时间；同时避免 Iter 间 Redis 连接池脏状态。
   - **`runner_managed`（fallback）**：runner 自启停服务进程。从 manifest 读 `server_start_cmd` 与 `server_port`，由 executor 透传给 runner（具体如何接收由 runner CLI 约定）。

   > **缺省处理变更说明（v1.2）**：v1.1 曾将缺省 `lifecycle` 默认为 `external`，对未配 `health_url` 的旧 manifest 会陷入"既不能自动启动，又无法健康检查"的死锁。本版本改为**按字段存在性推断 + 触发时强制 WARN**：有 health_url 走 external，有 server_start_cmd 走 runner_managed，都没有就停下问用户。这样旧 manifest（典型只有 server_start_cmd）能自动落到 runner_managed，无回归；同时 WARN 日志让维护者能批量定位需补充 `lifecycle` 字段的 manifest。
   >
   > **未来演进保留**：如果引入新的服务部署模式（如 k8s sidecar / serverless cold start），新增字段时同步更新本表的推断分支，每个新分支也要打 WARN。推断逻辑永远是 fallback，新 manifest 必须走显式声明路径。

   > **service.health_url 形态**：完整可探活的 URL（如根路径 `/` 或 `/health`）。具体路径由 runner / 服务方自定义；executor 只做存活探测，不解析路径语义。manifest 中**不要**把 runner 内部会再次拼接的子路径写入 `health_url` 或同名字段，避免双拼。

9. **Python 路径**：检测 `$PY`。优先 `.venv/Scripts/python.exe`（Windows）或 `.venv/bin/python`。

10. **Compact 恢复检查**：检查 `{round_dir}/execution/progressive_log.json` 是否存在。如存在，进入恢复协议。

### Compact 恢复协议

当 `{round_dir}/execution/progressive_log.json` 存在时：

1. 读取文件，解析 `iterations[]` 数组。
2. 如 `final_status` 已设置（round 已完成）：
   - **默认**：通知用户"本轮已完成，如需新轮次请启动新的 round。" 停止。
   - **用户覆盖**：若用户明确要求重做（如"重跑 round_3"），AskUserQuestion 确认后：重置 progressive_log（清空 iterations[]、final_status=null），从 Step 1 重新开始。
3. 统计已完成 Iter 数量。读取 `stable_snapshot_commit`。
4. 验证 git 状态：
   - 当前分支应为 `evoloop/round_{N}`。如不是：`git checkout evoloop/round_{N}`。
   - 工作树应与 `stable_snapshot_commit` 一致：`git diff --stat {stable_snapshot_commit}` 应为空。如不为空：`git checkout {stable_snapshot_commit} -- .`
5. 读取 `sample_manifest_path` 定位已有的 sample manifest。
6. 确定下一个未完成的 Iteration（对照 fix_plan 的 Iter 列表 vs progressive_log 已记录的 Iter）。
7. **跳过 Step 1 和 Step 2**，直接从 Step 3 的下一个未完成 Iter 开始执行。

> 关键：不要重跑 Step 1（工作区初始化）和 Step 2（样本生成）。progressive_log.json 就是状态。信任它。

---

## 文件操作规范（全流程适用）

1. **Write 前路径验证**：对含非 ASCII 字符的路径（如中文目录名），Write 前先用 `Bash: ls "{parent_dir}"` 确认目录存在且拼写正确。Write 后用 `Bash: ls -la "{file_path}"` 确认文件出现在预期位置。
2. **Write 前 Read 规则**：对已存在的文件（特别是跨 session 场景），Write/Edit 前必须先 Read。若不确定文件是否存在，用 `Bash: test -f "{path}" && echo exists` 检查。
3. **禁止手动 CSV merge**：若 eval 输出不完整（空行、行数不足），使用 `--resume` 重跑补全，禁止用 py -c 脚本拼接 CSV（BOM/fieldnames 处理极易出错，Round 3 曾导致 197→142 行数据腐烂）。
4. **encoding 硬规则**：所有 `open()` 调用（包括 py -c 内联脚本）必须显式指定 `encoding='utf-8'`。Windows Python 默认 GBK，不加 encoding 的 JSON/CSV 读写在遇到中文时必崩。
5. **Baseline 保护**：`{full_baseline_scored_csv}` 路径在 progressive_log.run_metadata 中记录。重置或清理 eval_results/ 目录时，禁止删除 baseline 文件。Baseline 路径一旦记录，禁止后续修改。

---

## 执行观察记录（全流程适用）

S4 执行过程中会不断产生**关于过程本身**的观察（工具 bug、SKILL.md 歧义、决策边界 case 等）。
这类观察如果不当场记录，会随 context 压缩或 session 结束丢失，维护者也失去改进 SKILL.md / scripts 的原始依据。

**本节要求 Executor 在执行过程中遇到以下情况时，当场向
`{round_dir}/execution/execution_observations.jsonl` 追加一行，然后继续主流程。**

### 记录条件

遇到以下任一情况，立即追加一条观察记录：

| 分类 `cat` | 含义 | 典型场景 |
|-----------|------|---------|
| `tool_failure` | 脚本/工具异常 | run_eval.py 崩、compare.py JSON 乱码、路径编码问题、shell 命令 hang |
| `skill_gap` | SKILL.md 指令缺失或语义模糊 | 当前步骤无法按指令执行、遇到指令未覆盖的情况需自行判断 |
| `resource_anomaly` | 时间 / token / 重试异常 | 单 batch 时间超预期 2x、同一 eval 重试 ≥ 3 次、工具连续失败 |
| `decision_uncertainty` | D1/D2 置信度低 | tolerance 临界值（± 1）、ai_reason 与 expected_tradeoffs 匹配歧义、scorer 明显噪声 |

### 严重度 `sev`

| 等级 | 定义 |
|------|------|
| `blocking` | 导致实际返工（重跑 eval、重做 batch）或无法继续 |
| `degrading` | 有 workaround 可继续，但需要调整 |
| `minor` | 观察到异常但不影响本次执行 |

### 字段格式（单行 JSON）

**必填字段（6 个，所有条目都必须有）**：

```json
{"ts":"2026-04-22T14:30:00+08:00","phase":"iter_5/eval","cat":"tool_failure","sev":"degrading","obs":"compare.py JSON 解析时 GBK 乱码，已加 encoding=utf-8 解决","suggestion":"SKILL.md 应 mandate 所有 py -c 脚本 encoding=utf-8"}
```

- `ts`：ISO 8601 + 时区（**必须带 `+08:00`**），不写 UTC 以贴合团队实际
- `phase`：发生位置，格式 `{step或iter}/{sub}`（如 `step_1/init`、`iter_3/apply`、`iter_5/eval`、`step_4/full_eval`、`step_4/report`）
- `cat`：四分类之一（枚举见上）
- `sev`：三级严重度之一
- `obs`：**一句话**描述现象 + 当场采取的 workaround（合并写，别换行）——**内容中禁止包含原始单引号**，若需引用代码请用等号形式（`encoding=utf-8` 而非 `encoding='utf-8'`），避免 shell 写入时引号破坏
- `suggestion`：对 SKILL.md 或 scripts 的改进建议（一句话）。暂无建议时填 `null`

**可选扩展字段**（按需追加，不破坏必填结构）：

- `evidence_missing: true`：context 压缩后细节丢失时标注，用于统计过滤（仅参与计数，不进入规则提炼）
- 未来如需新增字段，向后兼容追加即可。消费端以必填 6 字段为准，额外键不视为格式错误

### 写入操作

**首次**：若文件不存在，Write 创建，写入一行 JSON + 末尾换行。
**后续追加**（按推荐度从高到低）：

1. **Read → Write 拼接**（首选）：Read 现有文件 → 在末尾追加一行 JSON → Write 覆盖回去。不受任何 shell 转义影响，跨平台一致
2. **py -c 追加**：
   ```bash
   $PY -c "import json; open(r'{path}', 'a', encoding='utf-8').write(json.dumps({'ts':'...','phase':'...','cat':'...','sev':'...','obs':'...','suggestion':None}, ensure_ascii=False) + '\n')"
   ```
3. **禁止**使用 `echo '{...}' >> {path}`：`obs`/`suggestion` 内容中很容易出现单引号（代码片段、中文引号、示例文本等），单引号会在 shell 中提前闭合字符串，导致命令失败或写入畸形 JSON。Windows `echo` 对特殊字符处理尤其不可靠

文件不做任何排序/合并。

> 低阻抗原则：**一行 JSON append，不超过 60 秒**。不要中断主流程去写长文。

### Blocking 事件停/继续规则

| cat + sev | 行为 |
|-----------|------|
| `tool_failure` + `blocking` | **暂停当前 batch**，修复工具或回退到 stable_snapshot 后再继续。**禁止**把失败日志化后当作正常路径继续 |
| `resource_anomaly` + `blocking`（如 token 超预算、eval 连续 3 次失败） | **暂停整个 round**，AskUserQuestion 汇报 |
| `skill_gap` + `blocking` | 记录后按最佳判断继续；EXIT 前在 optimization_report 中单列"SKILL.md 待补充"章节 |
| `decision_uncertainty` + `blocking` | 降级为人工决策：AskUserQuestion 请用户判定 D1/D2 |
| 任何 `degrading` / `minor` | 记录后继续 |

### 上下文压缩失真情况

若 Executor 因 context 压缩无法回忆观察细节，**仍应写入**，但用 `"obs": "细节因 compact 丢失"`，`"evidence_missing": true` 追加到 JSON 中。这类条目仅用于计数统计，不进入 SKILL.md 规则提炼。

### 数据消费（维护者视角）

维护者在 round 结束后读取 `execution_observations.jsonl`：

1. 按 `cat` 分类：`tool_failure` / `resource_anomaly` → scripts issue；`skill_gap` / `decision_uncertainty` → SKILL.md issue
2. 按 `sev` 过滤：优先处理 `blocking` 级
3. 处理完在对应 issue/commit 中回链原始观察条目
4. 跨 experiment 复用的结论手工提炼到 `projects/<biz>/evoloop/knowledge/lessons_learned.md`

> 本机制为试点。若下一个 experiment 的前 3 个 round 观察记录数持续 < 3 条/round 或明显干扰主流程，回退到 round 末一次性追加回忆模式。

---

## Step 1: 执行工作区初始化

### 1.1 读取并理解 Agent 源码

读取 `agent_files_path` 下的所有文件。重点理解：
- `.space/agents/*.md`：哪些是 agent prompt 文件，各自职责
- `app/` 下的 Python 代码：核心逻辑结构
- fix_plan 中 FIX 引用的具体文件和位置

向用户简要陈述理解："Agent 包含 N 个 sub-agent prompt 文件和 M 个核心代码文件。fix_plan 涉及 K 个文件的修改。"

### 1.2 创建 git branch

```bash
cd {agent_files_path}
git checkout -b evoloop/round_{N}
```

如分支已存在（上次中断但无 progressive_log），AskUserQuestion："分支 evoloop/round_{N} 已存在，是否复用？"

### 1.3 记录 stable_snapshot_commit

```bash
git rev-parse HEAD
```

记录为 `stable_snapshot_commit`。这是所有 ROLLBACK 的恢复基准。

### 1.4 创建 round 目录

```bash
mkdir -p {round_dir}/execution/diffs
mkdir -p {round_dir}/execution/eval_results
```

### 1.5 解析 fix_plan + 汇总 manifest 健康检查

从 fix_plan.md 提取 Iteration 列表。对每个 Iter 记录：`iter_id`, `type`（基础/核心）, `requires`, `blocked_by_tickets`, `fixes` 列表。

**manifest 健康清单**（升格自前置检查 Step 1.8）：本 round 收集到的所有"按字段存在性推断 lifecycle"的 WARN 必须**汇总**到用户确认环节展示，不能仅停在日志层。这样配置缺失能在整个 round 启动前被人看到，而不是埋在执行日志里被忽略。

向用户确认时输出格式（无 WARN 时省去"manifest 健康"段）：

```
Fix plan 包含 N 个 Iteration：
  - iter_1 (基础)
  - iter_2 (核心)
  ...

⚠️ manifest 健康（{count} 项需关注）：
  - service.lifecycle 未声明，按规则 {规则编号} 推断为 {external | runner_managed}
    建议：在 manifest 中显式补 service.lifecycle: "{推断值}"

是否开始执行？(也可先暂停修补 manifest 后重跑)
```

---

## scorer_feedback 处理（schema 2.2）

> **何时执行**：前置检查 §3 已从 feedback.json 提取两个集合（`scorer_feedback_all` 用于离线汇聚 + `scorer_excluded_turns` 用于剔除统计）后，本节描述如何使用它们。**不**改 score.py / compare.py 的内部逻辑——剔除发生在统计层（§3.5 D1 决策、§4.2 全样本 eval、§4.3 报告渲染），不改评分链路。

### schema 2.2 关键变化

`scorer_feedback` 在 schema 2.2 升为**顶层正交字段**——不再绑定 reject_subtype。任何 verdict 都可附加 scorer_feedback：

| 典型情形 | verdict + scorer_feedback 组合 | affects_score |
|---|---|---|
| **A**：agent 行为对、评分理由错（原 scorer_misjudge） | reject + not_badcase + scorer_feedback | true（评分结果不可信） |
| **B**：agent 真错（要修）+ 评分理由错（要给评分器反馈） | revise + revision + scorer_feedback | 视情况——结果对 → false；结果错 → true |
| **C**：评分理由轻量瑕疵但结果对 | accept + scorer_feedback | false |

### 处理策略：分两层处理（汇聚 vs 剔除）

S2 HITL 中带 `scorer_feedback` 的 case 意味着评分器对这条 (session, turn) 的判定有问题（理由 / 结果维度之一）。两个独立动作：

1. **汇聚 scorer_feedback_all → 离线 markdown**：所有带 scorer_feedback 的 case（不论 affects_score）合并写入 `projects/<biz>/evoloop/scorer_feedback/<YYYYMMDD>_<exp_id>.md`，供下一轮人工迭代评分 prompt 离线消费。SoT 模板：`references/scorer_feedback_template.md`（运行时按需 mkdir + 复制 + 填充）

2. **剔除 scorer_excluded_turns → 当前轮统计**：仅 `affects_score === true` 的 (session, turn) 从所有 baseline_pass / candidate_pass 率统计、§3 改善归因、§4 退化归因 **双侧剔除**（分子分母都减）。保持比率有意义

3. **不 override**：Executor 不依赖 `scorer_feedback.suggested_revision` 自动覆写 score.csv（避免自由文本解析 + 评分链路被自动改动）

4. **D1 / D2 决策**：tolerance 判定基于剔除后的 pass 率；剔除明细不参与 D1/D2

### 实现位点

| 位点 | 改动 |
|---|---|
| §3.5 D1 决策 / pass 率计算 | 应用 `scorer_excluded_turns` 过滤后再计算 pass / fail 计数 |
| §4.2 全样本 eval 后处理 | baseline_full / candidate_full 的 pass 率同样剔除 |
| §4.3 optimization_report 渲染 | §1 总览标注剔除条数 + 比例；§3 / §4 章节开头注明已剔除；§8 表新增列承载 scorer_feedback 明细；新增 §8.1 聚合段输出到 `projects/<biz>/evoloop/scorer_feedback/<date>_<exp>.md`（聚合 scorer_feedback_all 全量） |

### 高占比 WARN

当 `len(scorer_excluded_turns) / total_full_turns > 0.20`（**affects_score=true 占比** > 20%）时，optimization_report §1 总览**强制输出 WARN**："评估器问题占比异常高 ({pct}%)，建议优先迭代评分 prompt 再进入下一轮 fix"。该 WARN 不阻塞执行，但作为下一轮决策的强信号。

> 注意：WARN 阈值用的是 `affects_score=true` 占比（评分结果不可信），不是 `scorer_feedback_all` 占比（含理由瑕疵的 C 情形）。后者占比高不一定意味着评分器整体不可用——理由表达可优化但结果对的情形不污染统计。

---

## Step 2: 小样本构成 (Sample Manifest)

### 2.1 确定 target turns

从 feedback.json 提取 `verdict != "reject"` 的 case_id 列表。通过 analysis_manifest.json 的 cases 数组将 case_id 映射到 `(session_number, turn_number)` 对。构造 `session_turn_pairs`：

```python
target_turns = []
target_session_set = set()
for case in feedback["feedback"]:
    if case["verdict"] != "reject":
        # 在 analysis_manifest.cases 中找到对应 case
        manifest_entry = next(c for c in manifest["cases"] if c["case_id"] == case["case_id"])
        eval_row = manifest_entry["eval_row"]
        target_turns.append(f'{eval_row["session_number"]}:{eval_row["turn_number"]}')
        target_session_set.add(str(eval_row["session_number"]))
session_turn_pairs = ",".join(target_turns)       # 如 "13:1,15:15,14:26"
target_sessions = ",".join(sorted(target_session_set))  # 如 "13,14,15"
```

> **关键变化**：使用 `--session-turns` 只提取 target turns（而非整个 session 的所有 turns），大幅减少 eval 量。

### 2.2 确定 guardrail 抽样

从 eval 输入 CSV 中获取所有 session_number 集合，减去 target sessions。按以下决策表确定抽样参数：

| 剩余 sessions | session 数 | --sample-strategy |
|---------------|-----------|-------------------|
| ≤ 5 | 1 session | `full`（默认，不加参数） |
| 6-10 | 2 sessions | 若平均 >15 turns/session → `uniform:3`；否则 `full` |
| > 10 | 2-3 sessions | 若平均 >15 turns/session → `uniform:3`；否则 `full` |

seed = round 编号 N。

> 判断"平均 turns/session"方法：在 `--preview` 模式下先执行一次 `--random` 抽样，观察提取行数和 session 数，计算平均值。

### 2.3 两步提取 + 合并

`extract_sample.py` 的 `--session-turns` 和 `--random` 互斥，需两次调用。每次使用 `--manifest` 生成工具层的规范 manifest：

> **并发执行约束**：§2.3 的两条 `extract_sample.py`（target / guardrail）+ §2.5 的 baseline target 提取**共 3 条命令彼此无依赖**，**必须在单 message 内一次性触发 3 个并行 Bash 调用**，禁止串行执行。§2.5 的 baseline guardrail 因依赖 `manifest_guardrail.sessions`，必须等 §2.3 完成后再执行（属 Phase B）。违反此原则单轮多花 ~30s 进程冷启动。
>
> **运行时降级**：本约束依赖 Agent 框架支持单 message 多 tool call 并行（支持 subagent 的宿主环境 原生支持）。若运行环境不支持（Agent 框架仅允许串行 tool call），降级为顺序执行——语义不变，仅性能损失，不要因此中断流程。
>
> **资源占用提示**：3 路并行 `extract_sample.py` 主要是 IO（CSV 读 + 正则匹配），单 case 内存占用 ~200MB，3 路约 600MB；如本地内存紧张（<2GB 可用）可降为串行。

```bash
# Target turns（--session-turns 只提取特定 turn，--manifest 自动标记 source="target"）
$PY scripts/small_sample/extract_sample.py \
  -i {eval_input_csv} \
  -o {round_dir}/execution/eval_results/sample_target.csv \
  --session-turns {session_turn_pairs} \
  --manifest {round_dir}/execution/manifest_target.json

# Guardrail cases（--exclude-sessions 排除 target，避免重叠）
# 若决策表结果为 uniform:3，加上 --sample-strategy uniform:3
$PY scripts/small_sample/extract_sample.py \
  -i {eval_input_csv} \
  -o {round_dir}/execution/eval_results/sample_guardrail.csv \
  --random {guardrail_count} \
  --seed {N} \
  --exclude-sessions {target_sessions} \
  [--sample-strategy uniform:3] \
  --manifest {round_dir}/execution/manifest_guardrail.json

# 合并 CSV（target 在前，guardrail 追加）
cp {round_dir}/execution/eval_results/sample_target.csv \
   {round_dir}/execution/eval_results/sample.csv
tail -n +2 {round_dir}/execution/eval_results/sample_guardrail.csv \
   >> {round_dir}/execution/eval_results/sample.csv
```

### 2.4 合并 sample_manifest.json

从两个工具产出的 manifest 合并为一个完整的 sample_manifest.json：

```python
import json
with open('{round_dir}/execution/manifest_target.json') as f:
    m_target = json.load(f)
with open('{round_dir}/execution/manifest_guardrail.json') as f:
    m_guard = json.load(f)

manifest = {
    "seed": m_guard.get("seed"),
    "sessions": sorted(set(m_target["sessions"] + m_guard["sessions"])),
    "turns": m_target["turns"] + m_guard["turns"],
    "created_at": m_target["created_at"]
}
with open('{round_dir}/execution/sample_manifest.json', 'w') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
```

> **不要手写 manifest schema**——始终从 `extract_sample.py --manifest` 的工具产出合并，避免 schema 漂移。

### 2.5 提取 baseline 子集

从全量 baseline scored CSV 中，提取与 sample 完全相同的 (session, turn) 子集，供 compare.py 使用。

由于 sample 来自两步提取（target turns + guardrail turns），baseline 也需两步提取后合并：

> **并发分组**（见 §2.3 顶部约束）：
> - **Phase A（与 §2.3 同批 3 路并发）**：baseline target 只依赖 `session_turn_pairs`（§2.1 已算出），与 §2.3 两条提取**同 message 触发**
> - **Phase B（§2.3 完成后单条）**：baseline guardrail 依赖 `manifest_guardrail.sessions`，必须等 Phase A 完成后再执行

```bash
# [Phase A] Baseline target（与 sample target 相同的 session:turn 对）
$PY scripts/small_sample/extract_sample.py \
  -i {full_baseline_scored_csv} \
  -o {round_dir}/execution/eval_results/baseline_target.csv \
  --session-turns {session_turn_pairs}

# [Phase B] Baseline guardrail（与 sample guardrail 相同的 sessions + 相同 strategy）
$PY scripts/small_sample/extract_sample.py \
  -i {full_baseline_scored_csv} \
  -o {round_dir}/execution/eval_results/baseline_guardrail.csv \
  -s {guardrail_sessions} \
  [--sample-strategy uniform:3]

# [Phase C] 合并（待 Phase B 完成后）
cp {round_dir}/execution/eval_results/baseline_target.csv \
   {round_dir}/execution/eval_results/baseline_sample.csv
tail -n +2 {round_dir}/execution/eval_results/baseline_guardrail.csv \
   >> {round_dir}/execution/eval_results/baseline_sample.csv
```

> `{guardrail_sessions}` 从 manifest_guardrail.json 的 `sessions` 字段读取。

> **冻结规则**：sample_manifest.json 和 baseline_sample.csv 在整个 round 内不变。每个 Iteration 使用同一份 sample。

---

## Step 3: 渐进式执行循环

对 fix_plan 中的每个 Iteration（按排列顺序），执行以下子步骤。

> **Progressive Log 纪律（违反即停止）**：
> 1. 每个 Iter 的 D1/D2 决策完成后，**必须立即** Edit progressive_log.json 追加本 Iter entry。
> 2. **禁止**在未更新 log 的情况下开始下一个 Iter。
> 3. 若因 context 压缩导致 log 内容不确定，先 Read progressive_log.json 确认当前状态。**原因**：压缩可能丢失 D1 结论，导致同一 Iter 被重复执行或判断矛盾。
> 4. 验证方法：每次追加后，确认 `iterations[]` 数组长度 = 已完成 Iter 数。
> 5. 若 Edit 失败（old_string 匹配不到），改用 Read 全文 → Write 全文方式更新。

### 3.1 依赖检查

对当前 Iter：
- 检查 `requires`：如任一 required Iter 在 progressive_log 中状态为 `ROLLBACK`，**SKIP** 本 Iter。
- 检查 `blocked_by_tickets`：如非空，AskUserQuestion 确认这些 ticket 是否已解决。用户确认未解决 → **SKIP**；已解决 → 继续执行。
- SKIP 时记录 `status: "SKIPPED"`，设 `d2_decision: "CONTINUE"`，跳至 3.7 写 log。
- 如果 SKIP 后剩余所有 Iter 也都会被 SKIP（全部 requires 已 ROLLBACK 的 Iter），则设 `d2_decision: "EXIT"`，直接进入 Step 4。

### 3.2 应用改动

对当前 Iter 的 `fixes` 列表中每个 FIX：

1. 读取 fix_plan 中 FIX 的实现层：`fix_location`、`before`、`after`、`implementation_notes`。
2. **读取文件实际内容**（不要盲信 fix_plan 的 `before` —— 前序 Iter 可能已改动同一文件）。
3. 理解意图层的 `root_cause` 和 `target`，结合实际代码状态，细化实现层（可调整 `after` 文本，但不可改变意图）。
4. 使用 Edit 工具应用改动。如需创建新内容，使用 Write 工具。
5. 遵守 repair-principles 7 条硬约束（特别是 Anti-Few-shot：after 中不可含枚举式示例或引号包裹的具体话术）。

> **多 FIX 并发约束**：本 Iter 的 fixes 列表按修改的 `fix_location.file` 分组：
> - **同文件多 FIX 串行**（Edit 工具的 old_string 唯一性语义要求）
> - **不同文件的 FIX 必须在单 message 内并发触发 Read + Edit/Write**——例如 Iter 含 3 个 FIX 分布在 `agents/router.md` / `agents/chat.md` / `app/router.py`，应一次性 3 个并发 Edit
> - 步骤 1-3（读 fix_plan + 读实际文件 + 推理细化）的 Read 调用同样可批量并发
>
> **运行时降级**：依赖 Agent 框架支持单 message 多 tool call 并行（支持 subagent 的宿主环境 原生支持）。若运行环境不支持，降级为顺序执行——语义不变，仅性能损失，不要因此中断流程。
>
> **部分失败处理**：若并发 Edit 中部分成功部分失败（如 `agents/router.md` Edit 通过、`agents/chat.md` Edit 因 old_string 不唯一失败），不要立即 git commit；先把失败项重试或重新读文件做更具体的 old_string 匹配；全部 FIX 落地后再统一 commit 该 Iter。这样 stable_snapshot 始终是"全 FIX 成功"或"未提交"的二态，不会有"半成功"的中间态。

全部 FIX 应用后：

```bash
cd {agent_files_path}
git add -A
git commit -m "iter_{N}: {iter_description}"
git diff HEAD~1 > {round_dir}/execution/diffs/diff_iter{N}.patch
```

当 `service.lifecycle=runner_managed` 时，runner 在每次 eval 调用时自启动 server（加载最新文件）并完成后清理，无需手动判断"是否改了 .md"。当 `service.lifecycle=external` 时，源码改动后服务是否重启由外部进程负责；executor 在 eval 前仅做 health check，不触发重启。

若 eval 报错"端口已被占用"：运行 `lsof -ti :{server_port} | xargs kill -9`（Mac/Linux）或通过 `netstat -ano | findstr ":{server_port}"` 找到 PID 后 `taskkill /F /PID {pid}`（Windows），等待 3 秒后重试。

### 3.3 小样本 Eval

> **禁止管道操作**：eval CLI 命令后不得附加 `| tail`、`| grep` 等管道。runner 普遍采用**增量落盘**设计（turn 完成后立即写入 CSV，并发场景下用 file lock 协调写入）；任务运行中输出文件已包含部分结果，**不能据此判断任务是否完成**。管道还会导致 stdout buffering 假象（标准输出延迟刷新 → 误判任务卡死 → 重复运行覆盖已有结果）。如需观察进度，使用 Monitor 工具监听 task stdout，并以 **task 退出码 + 输出文件最终行数**作为完成判据。

使用绝对路径调用 eval 工具链：

实际命令形态由 `manifest.eval_runner` 指向的 runner 决定，executor 按抽象槽位组装调用，**不假设具体 CLI 形态**（bash wrapper / ps1 wrapper / 直接 python 调用 / 其他可执行）：

```text
# 抽象形态（按 §8 service.lifecycle 分支）
{eval_runner}  \
  -i {round_dir}/execution/eval_results/sample.csv  \
  -o {round_dir}/execution/eval_results/output_iter{N}.csv  \
  -c {concurrency}  \
  --overwrite                                                 # 槽位：覆写已存在文件
  [--session-turns {session_turn_pairs} 当执行单 badcase 快速复测]  # 可选过滤槽位
  [+ {service.start_args}  当 lifecycle=runner_managed]       # 透传 server_start_cmd / server_port
  [+ {service.url_args}    当 lifecycle=external]             # 仅传 service URL（已探活）

# 具体参数名（如 --url / --agent-dir / --start-cmd / --tenant-id 等）由 runner CLI 决定，
# 见对应 runner guide：`scripts/run_eval/<framework-version>/*_guide.md` 或同级目录下的 README。
```

> **executor 的契约**：根据 `manifest.eval_runner` + `manifest.service.lifecycle`，组装命令并执行；不解析 runner 输出、不假设 runner 是否支持特定 flag。runner 必须满足下列最小契约：
> - 接受 `-i <input_csv>` / `-o <output_csv>` / `-c <concurrency>` / `--overwrite`
> - 增量落盘（写入 `output_csv`），并以非零退出码报告失败
> - 当 `service.lifecycle=runner_managed`，接受透传的 `server_start_cmd` 与 `server_port`，并自启停服务
> - 当 `service.lifecycle=external`，从 service URL 直接发请求，**不**自启停服务

```bash
# 3.3b: Score
$PY scripts/score/score.py \
  -i {round_dir}/execution/eval_results/output_iter{N}.csv \
  -o {round_dir}/execution/eval_results/scored_iter{N}.csv \
  -p {scorer_prompt} -c 10 \
  [--session-turns {session_turn_pairs} 当 output_iter{N}.csv 为全量输入且仅需重评目标 key]

# 3.3c: Compare (JSON to file, then Read) —— --only-changes 过滤 unchanged 行，减少 token 消耗
$PY scripts/score/compare.py \
  -a {round_dir}/execution/eval_results/baseline_sample.csv \
  -b {round_dir}/execution/eval_results/scored_iter{N}.csv \
  --json --only-changes > {round_dir}/execution/eval_results/compare_iter{N}.json
```

运行 compare 后，Read `compare_iter{N}.json` 解析结果。若文件超过 Read 单次上限（>500 行），改用 py -c 提取 summary + changes（必须加 `encoding='utf-8'`）。

### 3.3a 异常检测 (post-eval 必检)

Read `output_iter{N}.csv`，逐行检查以下三项。任一触发则**暂停**并 AskUserQuestion 报告异常：

1. **Call 1 memory 异常**：若某 turn 的 `user_state` 为空，但其 `dialog_history` 含 5+ message pairs（即 `json.loads(dialog_history)` 长度 ≥ 10），报警："Turn S{X}T{Y} 的 dialog_history 有 {N} 条消息但 user_state 为空，疑似 Call 1 memory 构造异常"
2. **响应截断**：若任何 target turn 的 `actual_output` 长度 < 50 字符（非空但过短），报警："Turn S{X}T{Y} 响应仅 {N} 字符，疑似截断或异常"
3. **延迟异常**：若 target turns 的平均 latency > 2x 全部 turns 平均 latency，报警："Target turns 平均延迟 {X}s，是整体平均的 {ratio}x，可能影响响应质量"

> 以上检查仅当使用 `--session-turns` 模式（target turns 独立提取）时执行。传统全 session 模式可跳过。

### 3.4 微调窗口 (Optional)

查看 eval 结果后，**可选**对实现层做微调。硬约束：

1. **只能修改当前 Iter 改动过的文件**。跨 Iter 文件修改 = 新 FIX，需回到 Planner。
2. **不可修改意图层**（root_cause, target, constraints, expected_tradeoffs）。
3. **不可增删 FIX 项或改变 Iteration 顺序**。
4. 微调后**不重新 eval**（效果在下一个 Iter 的 eval 中自然体现）。

如执行微调：`git add + git commit -m "iter_{N}_tweak: {brief}"`。在 progressive_log 的 `tweaks` 数组中记录改了什么文件和改动原因。

> **审计说明**：D1 决策基于 pre-tweak 的 compare 数据（eval 反映的是 tweak 前的代码效果）。tweak 包含在 COMMIT 后的 stable_snapshot 中，其效果在下一个 Iter 的 eval 中自然验证。d1_rationale 中应注明"本 Iter 有 tweak，eval 数据为 pre-tweak"。

### 3.5 D1 决策: COMMIT / ROLLBACK

D1 决策算法（严格按步骤执行）：

**准备数据**：
```
compare_json = 读取 compare_iter{N}.json
quality_regressions = compare_json.summary.quality_regressions
iter_type = 当前 Iter 的 type（基础 / 核心）
sample_size = sample_manifest.json 的 turns 数量

tolerance 计算：
  基础 Iter: tolerance = 3
  核心 Iter: tolerance = max(3, round(sample_size * 0.05))
```

**Step D1-1: 排除空输出退化**
```
empty_count = compare_json.summary.empty_output_regressions
→ 这些是 agent 环境问题，不计入 D1 判断。
→ 在 d1_rationale 中记录但不作为 ROLLBACK 依据。
```

**Step D1-2: 筛选非预期质量退化**
```
quality_items = compare_json.changes[]
  where change == "regression" AND subtype == "quality"

对每条 quality_item：
  读取 ai_reason_b（候选版本的退化原因）
  与当前 Iter 所有 FIX 的 expected_tradeoffs 逐条对照：
  - 如 ai_reason_b 描述的退化场景与某个 expected_tradeoffs 语义匹配
    → 标记为"预期退化"
  - 如不匹配任何 expected_tradeoffs
    → 标记为"非预期退化"
  (这是语义判断。当不确定时，分类为非预期——保守策略。)

unexpected_count = 非预期退化的数量
```

**Step D1-3: 计算 target 改善**
```
target_turns = sample_manifest.json 中 source == "target" 的 (session, turn) 集合
improved = compare_json.changes[] 中 change == "improvement" 且 (session, turn) ∈ target_turns 的数量
target_improved = improved
```

**Step D1-4: 判定**
```
IF unexpected_count > tolerance:
  → ROLLBACK
  → rationale: "非预期质量退化 {unexpected_count} 条，超过容忍度 {tolerance}"

IF iter_type == "核心" AND target_improved == 0:
  → ROLLBACK
  → rationale: "核心 Iter 但 target 无改善 (0/{target_count})"

ELSE:
  → COMMIT
  → rationale: "target 改善 {target_improved}/{target_count}，非预期退化 {unexpected_count} ≤ tolerance {tolerance}"
```

**ROLLBACK 执行**：
```bash
git checkout {stable_snapshot_commit} -- {changed_files}
git commit -m "rollback iter_{N}: {rationale 简写}"
```

**COMMIT 执行**：
```bash
stable_snapshot_commit = $(git rev-parse HEAD)
```

### 3.5a D1 决策 Walk-through 示例

**场景**：iter_2 修改了 chat.md（FIX_005: 延后信号实质推进），小样本 100 turns。

**Step 1: 读取 compare 数据**
```
summary.quality_regressions = 13, summary.empty_output_regressions = 0
```

**Step 2: 排除空输出** → quality_regressions = 13

**Step 3: 逐条匹配 expected_tradeoffs**

FIX_005 expected_tradeoffs：
> "延后信号内嵌于业务推进场景，若边界判断不精确，可能引入'保留价值理由'话术 → 被动回复/无效请示模式"

| Turn | ai_reason_b 摘要 | 匹配? | 判定 |
|------|-----------------|-------|------|
| S2T6 | "无效请示，未直接提供方案" | ✅ "被动回复/无效请示" | 预期 |
| S2T8 | "未针对房型主动提供替代" | ✅ "被动回复" | 预期 |
| S3T1 | "缺乏引导提问" | ✅ "被动回复模式" | 预期 |
| ...（共 11 条类似模式） | | ✅ | 预期 |
| S13T2 | "重复确认已知信息" | ❌ 与延后信号无关 | 非预期 |
| S15T12 | "重复确认月份" | ❌ 与延后信号无关 | 非预期 |

**Step 4: 计算** → 非预期 = 2, tolerance(基础) = 3, 2 ≤ 3 → **COMMIT**

**判断要点**：
- "匹配"是语义匹配——退化模式是否落在 expected_tradeoffs 描述的风险类别内，不要求逐字匹配
- 若 ai_reason_b 因编码问题不可读，**必须**通过 Read scored CSV 获取原文后再判断，禁止基于 session/turn 号推测

### 3.6 D2 决策: CONTINUE / EXIT

| D1 结果 | 条件 | D2 决策 |
|---------|------|---------|
| COMMIT | 有更多 Iter 且 target 未全部修好 | CONTINUE |
| COMMIT | 无更多 Iter 或 target 全部修好 | EXIT |
| ROLLBACK | 存在后续 Iter 且不 requires 当前 Iter | CONTINUE |
| ROLLBACK | 无可继续的后续 Iter | EXIT |

- "target 全部修好" = 所有 target-source turns 在 compare 中 score_b == "1"
- "不 requires 当前 Iter" = 后续 Iter 的 requires 数组不包含当前 iter_id

### 3.7 写入 progressive_log.json

每个 Iter 完成后**立即**写入。首个 Iter 创建文件，后续 Iter 追加到 `iterations[]`。

**文件 schema**（必须内联，compact 后是唯一参考）：

```json
{
  "round": "round_{N}",
  "fix_plan_path": "rounds/round_{N}/fix_plan.md",   // v3.3；legacy 场景下为 "iterations/round_{N}/fix_plan.md"。写入时按本轮实际 {round_dir} 的相对路径填写，保持与 Planner 前置条件识别的 round 目录一致
  "agent_files_path": "{agent_files_path}",
  "stable_snapshot_commit": "{当前的 stable_snapshot_commit}",
  "run_metadata": {
    "source_commit": "{初始 commit hash}",
    "eval_input_csv": "{eval_input_csv 路径}",
    "scorer_prompt": "{scorer_prompt 路径}",
    "scorer_model": "gemini-3-flash-preview",
    "sample_seed": {N},
    "decision_policy": "s4-d1-v1"
  },
  "sample_manifest_path": "execution/sample_manifest.json",
  "iterations": [
    {
      "iter_id": "iter_{N}",
      "type": "基础 | 核心",
      "status": "COMMIT | ROLLBACK | SKIPPED",
      "started_at": "ISO 8601",
      "completed_at": "ISO 8601",
      "changes_applied": ["agents/router.md", "agents/chat.md"],
      "commit_hash": "完整 40 字符 git commit hash（使用 git rev-parse HEAD 获取，禁止手动截断）",
      "eval_result": {
        "scored_csv": "eval_results/scored_iter{N}.csv",
        "compare_json": "eval_results/compare_iter{N}.json",
        "target_improved": 7,
        "target_unchanged": 2,
        "target_regressed": 1,
        "regression_pass": 14,
        "regression_fail": 1,
        "empty_output_regressions": 0,
        "quality_regressions_unexpected": 0
      },
      "d1_decision": "COMMIT | ROLLBACK",
      "d1_rationale": "具体数据支撑的决策理由",
      "d2_decision": "CONTINUE | EXIT",
      "d2_rationale": "具体数据支撑的决策理由",
      "snapshot_commit_after": "D1 后的 stable_snapshot_commit",
      "tweaks": []
    }
  ],
  "final_status": null,
  "final_snapshot_commit": null,
  "summary": null
}
```

当 D2 == EXIT 时，设置 `final_status: "EXIT"`，`final_snapshot_commit`，并填充 `summary`：

```json
"summary": {
  "accepted_iterations": ["iter_1", "iter_2"],
  "rolled_back_iterations": ["iter_3"],
  "skipped_iterations": ["iter_4"],
  "unresolved_targets": ["case_04", "case_09"],
  "recommended_action": "merge | local_adjustment | replan"
}
```

`recommended_action` 规则：
- `"merge"`：所有 target cases 改善，无非预期退化
- `"local_adjustment"`：部分 target 改善，有 ROLLBACK 的 Iter 存在
- `"replan"`：无 target 改善，或 ROLLBACK 多于 COMMIT

### 3.8 循环继续

- D2 == CONTINUE → 回到 3.1，处理下一个 Iter。
- D2 == EXIT → 进入 Step 4。

向用户输出进度摘要：
```
[Progress] Iter {current}/{total} {D1_decision}, 已用时 {elapsed}
  target: {improved}/{total_target} 改善
  非预期退化: {unexpected} (tolerance: {tolerance})
```

---

## Step 4: EXIT 后处理

### 4.1 复制 new_agent_files

将 `stable_snapshot_commit` 对应的 Agent 文件复制到 `{round_dir}/execution/new_agent_files/`。

> **注意**：`agent_files_path` 通常是 monorepo 子目录（如 `projects/<biz>/framework-version/<framework-id>/`）。`git archive` 会导出整个仓库，不是子目录。必须用 `--prefix` + 路径过滤，或直接复制文件。

```bash
mkdir -p {round_dir}/execution/new_agent_files

# 方法：从 agent_files_path 子目录导出（仅 Agent 文件）
cd {repo_root}
git archive {stable_snapshot_commit} -- {agent_files_path_relative} | tar -x -C {round_dir}/execution/new_agent_files/ --strip-components={depth}

# 如 tar 在 Windows 上不可用，替代方案：
# git checkout {stable_snapshot_commit} -- {agent_files_path_relative}
# cp -r {agent_files_path}/* {round_dir}/execution/new_agent_files/
# git checkout evoloop/round_{N} -- {agent_files_path_relative}
```

### 4.2 验证 Eval：fast_verify / release_verify

S4 支持两档验证：

- **fast_verify**：只跑 target turns + `regression_scope` + guardrail 子集，产出 `output_fast.csv` / `scored_fast.csv`，必要时用 `scripts/csv_patch/merge_by_session_turn.py` merge 到候选 scored 快照。该结果只用于迭代内快速判断，不能替代最终全量验证。
- **release_verify**：继续跑全量 eval + score，产出 `output_full.csv` / `scored_full.csv` / `compare_full.json`，用于 round 结束和合并前最终确认。

默认 EXIT 时执行 `release_verify`。用户明确要求快速复测单个 badcase 时，可先执行 `fast_verify`；进入最终报告前仍必须执行一次 `release_verify`。

`progressive_log.json` 中每次验证必须记录：

```json
{
  "eval_scope": "fast_verify | release_verify",
  "session_turns": "13:4,15:2 或 null",
  "merged_from": "eval_results/scored_fast.csv 或 null",
  "stale_turns_count": 0
}
```

`stale_turns_count` 表示候选 scored 快照中未在本次局部验证里重新 eval/score 的行数；只要大于 0，报告中必须标注该验证不是全量结论。

`release_verify` 调用形态与 §3.3a 一致——执行 `manifest.eval_runner`，按 `service.lifecycle` 分支决定服务管理；输入用全量 `{eval_input_csv}`，输出落到 `{round_dir}/execution/eval_results/output_full.csv`，并发可提升至 20。具体参数由对应 runner CLI 决定：

```text
{eval_runner}  \
  -i {eval_input_csv}  \
  -o {round_dir}/execution/eval_results/output_full.csv  \
  -c 20  --overwrite
  [+ {service.start_args}  当 lifecycle=runner_managed]
  [+ {service.url_args}    当 lifecycle=external（eval 前已完成 health check）]
```

```bash
# Score
$PY scripts/score/score.py \
  -i {round_dir}/execution/eval_results/output_full.csv \
  -o {round_dir}/execution/eval_results/scored_full.csv \
  -p {scorer_prompt} -c 10

# Compare (full baseline) —— --only-changes 减少输出体积
$PY scripts/score/compare.py \
  -a {full_baseline_scored_csv} \
  -b {round_dir}/execution/eval_results/scored_full.csv \
  --json --only-changes > {round_dir}/execution/eval_results/compare_full.json
```

### 4.3 生成 optimization_report.md

按 `references/optimization-report-template.md` 的 9 维度模板，基于 `compare_full.json` + `progressive_log.json` 生成报告。每个维度必须有具体数据支撑。

### 4.4 附加 执行观察摘要（本轮试点产出）

在 optimization_report.md 末尾追加一节 `## 执行观察摘要`，从
`{round_dir}/execution/execution_observations.jsonl` 聚合统计。**不复述每条观察的详情**，只做分类计数：

```markdown
## 执行观察摘要

> 原始数据：`execution/execution_observations.jsonl`（共 N 条）

| 分类 (cat)            | blocking | degrading | minor | 合计 |
|----------------------|:--------:|:---------:|:-----:|:----:|
| tool_failure         |    -     |     -     |   -   |   -  |
| skill_gap            |    -     |     -     |   -   |   -  |
| resource_anomaly     |    -     |     -     |   -   |   -  |
| decision_uncertainty |    -     |     -     |   -   |   -  |

**需要维护者处理的条目**：列出所有 `sev = blocking` 的 `phase` + `cat`，每条 ≤ 1 行。
```

若 `execution_observations.jsonl` 不存在或为空，本节写一句 "本轮未产生执行观察记录"。
这一节的目的是**让维护者一眼判断是否需要改进 SKILL.md / scripts**，不影响 9 维度主报告。

### 4.5 更新 progressive_log.json

设置 `final_snapshot_commit` 为当前 `stable_snapshot_commit`。确保 `summary` 段完整。

---

## 质量自检

optimization_report.md 产出后，执行以下检查：

1. **progressive_log 完整性**：每个 Iter 的 entry 所有字段非空
2. **Git 状态一致**：当前分支 `evoloop/round_{N}`，HEAD 与 `stable_snapshot_commit` 一致
3. **样本一致**：所有 Iter 使用同一份 sample（sample_manifest.json 未被修改）
4. **D1 审计**：每个 ROLLBACK 的 rationale 引用了具体 compare_json 数据
5. **意图层未改**：验证未修改任何 FIX 的 root_cause、target、constraints
6. **文件范围**：未修改 fix_plan 中未列出的文件
7. **report 完整**：optimization_report.md 的 9 个维度均有内容

---

## 话术风格

与 auto-single-case-analyzer 和 auto-fix-planner 一致：

- **术语中文化**：英文术语首次出现给中文对照，后续用中文
- **数据引用**：决策理由必须引用具体数字（如"非预期退化 3 条，tolerance 2，超出 1 条"）
- **代码原文**：涉及 Agent 源码的引用保持原文，不做语言转换
- **Iteration 描述**：进度摘要须含"改了什么"+"效果如何"，不可只写"完成 iter_2"

---

## 环节结束提醒

当 optimization_report.md 写入完成后，向用户展示：

```
[Executor Complete]

产出物：
- optimization_report.md — 9 维度优化效果总结
- new_agent_files/ — 新版 Agent 文件（最后 COMMIT 的稳定快照）
- progressive_log.json — 执行过程记录（含 summary 段供 S3 回流消费）

全样本结果：
- Baseline: {baseline_pass}/{baseline_total} ({rate}%)
- Candidate: {candidate_pass}/{candidate_total} ({rate}%)
- 退化: {regressions} (质量: {quality}, 空输出: {empty})
- 改善: {improvements}

执行摘要：
- Iterations: {committed} COMMIT / {rolled_back} ROLLBACK / {skipped} SKIPPED
- Target 达成: {resolved}/{total_target}

后续决策（请阅读 optimization_report.md）：
(A) 提升+无副作用 → 创建 PR 将 evoloop/round_{N} 合入（遵循 PR-only 工作流）
(B) 提升+有退化 → 回流 auto-fix-planner 调整方案
(C) 未提升 → 回流 S1/S2 重新分析 或 人工介入
```

> **元反思推荐判定**（AI 自行评估，判定逻辑不向用户展示）：若本轮执行暴露了方法论的结构性漏洞（自行判断——D1 触发条件处于 scorer noise 层 / 跨 iter 累积 tradeoff 单调向坏 / HITL 反复介入 / fix_plan 字段下游不消费 / 跨轮 baseline 或 tolerance 漂移 / 其他非预期摩擦皆是线索），**在 A/B/C 决策树之前追加一句** "建议先（新建分支/branch）然后输入 /meta-reflection 做元过程反思，再做 A/B/C 决策 — 触发理由：<一句话>"；本轮顺畅则不追加，**不要给"可选"等通用提示**。
