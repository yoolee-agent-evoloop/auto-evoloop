---
name: auto-trace-prep-v1.3
description: >
  物料准备 skill——加载评测数据、获取 Agent Harness、抓取并标准化 trace 文件。
  三个子能力（eval-data、harness、trace-fetch）封装在一个 skill 中，
  共享触发时机和 HITL 1 信息澄清节点，输出统一的 analysis_manifest.json 供下游消费。
  支持单版本和多版本（交叉对比）场景。默认获取所有 badcase 的 trace，
  后续增量分析只需修改 selected 标签，无需重跑此 skill。

  v1.3 关键变化：
  - 1a eval-data 新增"按需运行 eval"模式：用户仅给 Agent 版本 + 测评集 CSV 时，
    skill 自行调用 scripts/run_eval/<framework>/ + scripts/score/ 产出 scored CSV，
    不再要求用户手工准备 scored 数据（实现风格参考 auto-fix-executor §3.3）。
  - 1c trace-fetch 移除"用户直接提供 Trace JSON 文件"选项，强制走 thread_id 路径。
  - 1c 新增 beta：可切换到 scripts/traces_fetch/fetch_and_clean.py 的 LangGraph
    五步清洗流水线作为 trace 压缩后端（与默认 analysis-compact 互斥）。

  当用户提到以下任何场景时务必触发此 skill：
  准备 trace 分析、加载评测数据和 trace、拉取 trace、我要分析 badcase（作为流程起点）、
  上传了评测 Excel 要求分析、提供了多个版本的评测数据要求对比、
  没有评测结果但已有 agent 版本+测评集要求先跑 eval。

  与 auto-single-case-analyzer 的边界：本 skill 只负责物料准备和分析范围确认，
  不做任何归因分析——归因由 auto-single-case-analyzer 执行。
---

# Trace Prep

物料准备——加载评测数据、获取 Agent Harness、抓取并标准化 trace 文件，输出统一的 `analysis_manifest.json` 供下游 skill 消费。

## 适用场景

你拿到了评测数据（Excel/CSV），需要准备分析所需的全部物料：解析评测记录的列结构、获取 Agent Harness、拉取 trace 文件。本 skill 是整个 badcase 分析流程的起点。

## 输入物料

| 物料 | 必选 | 说明 |
|------|:----:|------|
| 评测记录 | ✅（二选一） | (1) **已有 scored Excel/CSV**——直接用作 eval-data 输入；或 (2) **Agent 版本（路径/服务 URL）+ 测评集输入 CSV**（如 `projects/<biz>/evals/input_<biz>.csv`）→ 由 1a 自行调用 `scripts/run_eval/<framework>/` + `scripts/score/` 跑出 scored CSV 后再继续 |
| Agent 版本 ID | 可选 | 用于自动获取 Harness（prompt 文件、工具定义、编排代码）；若走"按需跑 eval"路径，本字段同时承担"指向 agent 源码 / 服务"的角色 |
| Harness 文件 | 可选 | 如无版本 ID，可直接提供 Markdown/代码文件 |
| Trace 数据 | 二选一 | (A) thread_id 列表（直接调用拉取脚本）（B) 从评测 Excel/CSV 中提取 thread_id（仍走 A 的拉取流程）。**v1.3 起不再支持"用户直接提供 trace JSON 文件"路径**——下游 viewer / analyzer 已不再保留 raw 命名兼容性，统一走脚本拉取以保证清洗格式一致 |

## 输出 Artifact

```
{analysis_root}/
├── schema.json               # 列类型映射、评分范围、通过阈值
├── Harness.md                # 标准化的 Agent 描述文档
├── traces/                   # 标准化 trace JSON 文件
│   ├── trace-<hash>-thread-<thread_id_1>-analysis-compact.json
│   └── trace-<trace_id>-thread-<thread_id_2>.json   # fetch_and_clean beta
└── analysis_manifest.json    # 统一索引（见下方 schema）
```

### 输出目录命名规则

按以下优先级决定 `$ANALYSIS_ROOT`：

**优先级 1：调用方提供显式 anchor（推荐）**

如果调用方（host repo 的运行时指令、上层 skill、或用户）已给出明确的 analysis_root 路径，**直接使用该路径**作为 `$ANALYSIS_ROOT`，**不再追加** `badcase_analysis_{MMDDHH}/` 前缀。本 skill 对显式 anchor 不做改写。

触发场景：
- host repo 在自己的运行时指令（如 `<host_runtime_doc>`）中规定 stage artifact 的归属位置（典型：把 S1/S2 产物锚到 `evoloop/experiments/<exp>/analysis/`，而非 eval 文件平级）
- 多 skill 串联时上一阶段已创建好实验目录

**用户没有显式给出时**：开始 Phase 1 之前，先确认归属位置——不要按默认规则先建一遍再回头搬。具体确认方式（询问用户 vs 读 host 运行时指令）由调用方自行决定，本 skill 不预设。

**优先级 2：默认规则（无显式 anchor 时）**

所有产物统一放在一个以时间戳命名的文件夹中，该文件夹与用户提供的**评测文件同级目录**平行创建。

- 命名：`badcase_analysis_{MMDDHH}/`（月日时，如 `badcase_analysis_031714/` 表示 3 月 17 日 14 时创建）
- 目录创建：根据评测文件路径确定父目录，创建 `badcase_analysis_{MMDDHH}/traces/`
- 如果用户没有提供评测文件（如直接给了 trace JSON），则在 trace 文件所在目录的同级创建；如果 trace 也是用户上传到临时目录的，则在当前工作目录创建

**路径变量（不论按哪条规则确定）**：
- `$ANALYSIS_ROOT`：本次分析产物根目录
- `$TRACES_DIR`：`$ANALYSIS_ROOT/traces/`

**目录创建责任**：
- `$ANALYSIS_ROOT` 本身的**父目录必须已存在**——优先级 1 时由调用方保证（如 host repo 在 <host_runtime_doc> 里规定的 `projects/<biz>/evoloop/experiments/<exp>/` 已就位），优先级 2 时由评测文件所在路径天然保证。
- skill **始终负责** `mkdir -p $ANALYSIS_ROOT $TRACES_DIR` 以及后续 Phase 中产生的子目录（`reports/` 等由 Stage 2 自行创建）。
- 若 `$ANALYSIS_ROOT` 已存在且非空（典型：复用既有实验目录），skill 直接在其下写入产物，不清理旧文件——清理由调用方决定。

> **host repo 内调用本 skill 时**：通常 host 会通过其 `<host_runtime_doc>` 或类似运行时指令规定 anchor 落点；本 skill 不假设任何 host 布局，但承诺一旦收到显式 anchor 即按其行事。`auto-evoloop-registry` 的 anchor 规则见该仓库 `<host_runtime_doc>` "Skill artifact 锚点" 一节。

---

## 执行流程

```
Phase 1: 物料采集
  ├── 1a. eval-data: 读取评测记录 → schema.json
  ├── 1b. harness: 获取 Agent Harness → Harness.md
  └── 1c. trace-fetch: 拉取所有 badcase 的 trace → traces/*.json
         ↓
  汇总为 analysis_manifest.json (draft)
         ↓
HITL 1: 信息澄清 + 分析范围标注
  确认 schema、列语义、标注 selected/analysis_mode
         ↓
  analysis_manifest.json (confirmed)
```

---

## Phase 1：物料采集

> **环境检测**（首次执行时）：参照 `references/environment-setup.md` 完成 Python 路径检测和路径规范配置，后续全流程复用检测结果。

### 1a. eval-data：评测数据解析

> **首步：判定输入分支**——读取用户提供物料后，按以下规则确定走"直接解析"还是"按需跑 eval"：
>
> | 输入物料 | 分支 |
> |---|---|
> | 已有 scored Excel/CSV（含 `actual_output` + 评分列） | **直接解析**（跳到下文"列类型识别"段） |
> | 仅 Agent 版本/服务 URL + 测评集输入 CSV（含 `user_query` / `dialog_history` / `metadata` 等输入列，但**无 `actual_output` 与评分列**） | **按需跑 eval**（先执行 1a-bis，产出 scored CSV，再回到"列类型识别"段） |
> | 既有 scored CSV 又有"agent 版本"且用户明确要求"用新版本 agent 重跑评测" | **按需跑 eval**（视既有 scored CSV 为对照基线，跑出新一份后两份并存进入多版本场景） |
>
> 推断不确定时（如 CSV 列里 `actual_output` 仅部分为空），AskUserQuestion 让用户确认是"已有评测但部分缺失"（直接解析 + 后续标注空值）还是"未评测"（按需跑 eval）。

读取 Excel/CSV，自动识别列类型，产出 `schema.json`。

**列类型识别**——寻找以下语义字段（字段名可能因项目不同而有别名，灵活匹配）：

```
核心字段：
- user_query / 用户输入        → 用户当轮说了什么
- actual / actual_output / agent_output  → 模型/Agent 实际输出（即 Agent 真实返回给用户的内容）
- reference_output / 参考答案   → 期望 Agent 怎么回答
- dialog_history / 对话历史     → 之前的多轮对话
- metadata / 元数据            → 业务上下文（用户画像、线索信息等）
- 评分                        → score / ai_score（scripts/score/score.py 默认列名）
- 评分理由                    → score_reason / ai_reason / ai_analysis（scripts/score/score.py 默认列名；ai_reason 是简短标签，ai_analysis 是详细推理）
- 问题分类 / 问题分析          → 已有的人工标注（如果有）
- thread_id                    → 用于关联或查询 trace
- session_number / turn_number → 会话与轮次编号（多轮场景必备）
- latency_ms / fail_reason    → run_eval 产物的运行时元数据（可选，分析延迟异常时有用）
```

> **scored CSV 的实际列名**（`scripts/score/score.py` 输出）：`session_number` / `turn_number` / `metadata` / `user_query` / `dialog_history` / `actual_output` / `thread_id` / `latency_ms` / `fail_reason` / `ai_score` / `ai_reason` / `ai_analysis`。1a 列识别**必须**识别这组列名作为 score.py 默认的别名集合——否则走 1a-bis "按需跑 eval"分支时会自相矛盾（自己跑出的 scored CSV 自己识别不了）。

**actual/agent_output 空值处理**：如果 actual / agent_output 字段为空，但 reference_output 存在，需主动询问用户："该条记录的 actual/agent_output 为空，但存在 reference_output。请确认：reference_output 列的内容是否实际上代表 Agent 的真实输出（即该列被命名为 reference_output 但实际含义是 agent 实际回答）？"——因为不同项目的列命名习惯可能不同，reference_output 有时会被用来记录 agent 实际输出而非期望答案。确认后再继续分析。

**reference_output 空值处理**：如果 reference_output / 期望输出字段为空，**停止并询问用户**："该条记录的期望输出（reference_output）为空，无法进行期望 vs 实际对比。请提供期望的 Agent 输出，或说明为何无法提供。" 明确禁止在期望输出为空时进行推断、捏造或用其他字段替代——错误的基准会导致归因方向完全偏离。

识别不到的字段不要猜，问用户。

**`schema.json` 输出格式**：

```json
{
  "columns": {
    "user_query": "B",
    "actual": "C",
    "reference_output": "D",
    "dialog_history": "E",
    "metadata": "F",
    "score": "G",
    "score_reason": "H",
    "problem_category": "I",
    "thread_id": "J"
  },
  "score_range": [0, 5],
  "pass_threshold": 3,
  "total_rows": 50,
  "badcase_count": 15,
  "badcase_rows": [2, 5, 8, 11, 13, 17, 20, 23, 28, 31, 35, 38, 42, 45, 49]
}
```

### 1a-bis. 按需运行 eval（缺少 scored CSV 时）

> **何时执行**：1a 首步分支判定为"按需跑 eval"时启动。本节为 **scored CSV 产出器**——产出物喂回 1a 的"列类型识别"段，下游照常解析。
>
> **设计参照**：本节调用方式与 `core_skills/04_execute/auto-fix-executor/SKILL.md` §3.3（小样本 Eval）保持一致——共用同一组 `scripts/run_eval/<framework-version>/`、`scripts/score/score.py`、`scripts/score/<biz>_score.md` 工具链；本 skill **不复制 runner 实现**，仅作编排。

#### 步骤 1：信息采集（AskUserQuestion 一次性收齐）

向用户确认以下槽位，缺一不可：

| 槽位 | 含义 | 默认/示例 |
|---|---|---|
| `biz` | 业务标识（决定 scorer prompt 与 input CSV 默认路径） | 三选一：`biz_a` / `biz_b` / `biz_c`（来自 `projects/<biz>/`） |
| `framework_version` | 评测框架版本（决定调用哪份 runner） | 默认 `<framework-current>`（推荐）；过渡期 `<framework-legacy>` 需用户显式指定 |
| `eval_input_csv` | 测评集输入 CSV 绝对路径 | 默认 `projects/<biz>/evals/input_<biz>.csv`；如有多份则列出供选 |
| `service_url` | agent-engine 服务 base URL（<framework-name> runner 需要；<framework-name> 不需要） | 默认 `http://localhost:8088`；如服务跑在其他主机则覆盖 |
| `scorer_prompt` | 业务专属评分 prompt | 默认 `scripts/score/<biz>_score.md` |
| `concurrency_eval` / `concurrency_score` | runner / scorer 并发 | 默认 `10` / `10`，本地资源紧张可降到 5 |
| `output_dir` | scored CSV 落盘根目录 | 默认 `$ANALYSIS_ROOT/eval_runs/<framework-version>_<UTC date>/`（与产物一同收纳，便于 manifest 锚定）。**前置**：本节启动前 `$ANALYSIS_ROOT` 必须已通过本 SKILL §"输出目录命名规则" 段（优先级 1 显式 anchor 或优先级 2 默认规则）确定；如尚未确定，先回到 §"输出目录命名规则"完成 anchor 选择再回到本节 |
| `session_turns` | 可选局部评测范围 | 为空表示全量；局部快速验证时传 `"13:4,15:2"`，格式与 `run_eval.py --session-turns` 一致 |
| `base_eval_output_csv` / `base_scored_csv` | 局部模式可选 | 若要覆盖既有全量产物，分别提供原 `eval_output.csv` / `scored.csv`；为空则只产出局部文件，不 merge |

> **agent 版本/源码不在本仓库**：runner 是纯 HTTP 客户端；agent-engine 服务需要用户在 `~/agent-source/agent-<biz>/` 侧自行启动（参考 host repo `<host_runtime_doc>` "Eval Pipeline" 段）。本 skill **不启停服务**——只做存活探测。

#### 步骤 2：服务存活探测（仅 <framework-current> 需要）

```bash
curl -fsS "$SERVICE_URL/healthz" >/dev/null \
  || { echo "[ERR] $SERVICE_URL 不可达，请先在 agent-source 仓库侧启动 agent-engine"; exit 1; }
```

不可达时：AskUserQuestion 报告"服务未启动，请按 host repo <host_runtime_doc> 'Eval Pipeline · Mac/Linux' 段启动后再继续"，等待用户重试。本 skill **不**自动尝试拉起服务（避免对 agent-source 仓库布局做隐式假设）。

#### 步骤 3：跑 eval

```bash
mkdir -p "$OUTPUT_DIR"

# (a) run_eval —— <framework-current> 形态，<framework-legacy> 走对应 wrapper
$PYTHON_CMD scripts/run_eval/$FRAMEWORK_VERSION/run_eval.py \
  --url "$SERVICE_URL" \
  -i "$EVAL_INPUT_CSV" \
  -o "$OUTPUT_DIR/eval_output.csv" \
  -c "$CONCURRENCY_EVAL" \
  --overwrite
```

局部模式（`session_turns` 非空）时，输出文件名固定为 `eval_output.partial.csv`，并向 runner 追加 `--session-turns "$SESSION_TURNS"`：

```bash
$PYTHON_CMD scripts/run_eval/$FRAMEWORK_VERSION/run_eval.py \
  --url "$SERVICE_URL" \
  -i "$EVAL_INPUT_CSV" \
  -o "$OUTPUT_DIR/eval_output.partial.csv" \
  -c "$CONCURRENCY_EVAL" \
  --session-turns "$SESSION_TURNS" \
  --overwrite
```

> **<framework-legacy> 路径**（仅过渡期）：脚本路径 `scripts/run_eval/<framework-legacy>/run_eval.sh`（Mac/Linux）或 `.ps1`（Windows）；无 `--url` 但有 `--agent-dir`；具体 flag 由对应 runner guide 维护。本 skill 按用户选定的 `framework_version` 透传；不假设 CLI 形态。
>
> **失败处理**：runner 非零退出 → 不要继续 score；先看 stderr 提示，按 runner guide 的 Q&A 段排查（典型：服务未启 / lock 残留 / 输入 CSV 字段缺失）。

#### 步骤 4：跑 score

```bash
$PYTHON_CMD scripts/score/score.py \
  -i "$OUTPUT_DIR/eval_output.csv" \
  -o "$OUTPUT_DIR/scored.csv" \
  -p "$SCORER_PROMPT" \
  -c "$CONCURRENCY_SCORE"
```

局部模式时，score 输入/输出固定为局部文件，并透传同一组 key：

```bash
$PYTHON_CMD scripts/score/score.py \
  -i "$OUTPUT_DIR/eval_output.partial.csv" \
  -o "$OUTPUT_DIR/scored.partial.csv" \
  -p "$SCORER_PROMPT" \
  -c "$CONCURRENCY_SCORE" \
  --session-turns "$SESSION_TURNS"
```

如提供了 `base_eval_output_csv` / `base_scored_csv`，必须用官方 merge 工具按 key 整行替换，禁止手工拼接 CSV：

```bash
$PYTHON_CMD scripts/csv_patch/merge_by_session_turn.py \
  --base "$BASE_EVAL_OUTPUT_CSV" \
  --patch "$OUTPUT_DIR/eval_output.partial.csv" \
  --output "$OUTPUT_DIR/eval_output.merged.csv" \
  --summary "$OUTPUT_DIR/eval_output.merge_summary.json"

$PYTHON_CMD scripts/csv_patch/merge_by_session_turn.py \
  --base "$BASE_SCORED_CSV" \
  --patch "$OUTPUT_DIR/scored.partial.csv" \
  --output "$OUTPUT_DIR/scored.merged.csv" \
  --summary "$OUTPUT_DIR/scored.merge_summary.json"
```

局部模式下交回 1a 的 `eval_source` 优先级：`scored.merged.csv`（若已 merge） > `scored.partial.csv`。只产出局部 scored 时，后续 schema / manifest 只代表局部样本，不可标记为全量评测结果。

> **`<SCORER_KEY_ENV>`**：scorer 走第三方 LLM；如未设置环境变量，score.py 自身会硬失败并提示——本 skill 在调用前先做一次软探测（同时校验非空 + 非纯空白；空字符串 / `'   '` / 未设置三种情况都视为缺失）：
>
> ```bash
> $PYTHON_CMD -c "import os,sys; key=(os.environ.get('<SCORER_KEY_ENV>') or os.environ.get('<COMPATIBLE_LLM_KEY_ENV>') or '').strip(); sys.exit(0 if key else 1)" \
>   || { echo "[ERR] <SCORER_KEY_ENV> / <COMPATIBLE_LLM_KEY_ENV> 未设置或为空白，请在 <credential_store> 中配置后重试"; exit 1; }
> ```
>
> **别名兼容性**：score.py 实际接受 `<SCORER_KEY_ENV>` **或** `<COMPATIBLE_LLM_KEY_ENV>`（OpenAI 兼容接口走 <COMPATIBLE_LLM_KEY_ENV> 也可），本探测两个变量都查；任一非空非空白即通过。

#### 步骤 5：交回 1a 主流程

把 `$OUTPUT_DIR/scored.csv`（全量模式）或上文局部模式确定的 scored 产物作为 1a 的 `eval_source`（覆盖用户原 `eval_input_csv` 输入），继续走"列类型识别 → schema.json"段。**注意**：scored CSV 已新增 `actual_output` + `ai_score` / `ai_reason` / `ai_analysis` 列（score.py 默认列名），1a 列识别段已显式列出这组别名，无需用户额外确认。

> **路径绝对化**：`extract_sample.py` / `score.py` / `run_eval.py` 都对 `-i` 输入文件用 `os.path.isfile` 字面量检查，**不会**按 cwd / repo root 兜底相对路径。1a-bis 调用时务必把 `eval_input_csv` / 中间产物路径全部用绝对路径传，否则会触发 `错误: 文件不存在: <相对路径>` 的硬失败。

> **manifest 字段补充**（与 §`analysis_manifest.json` Schema 段呼应）：本节执行后必须在 manifest 中记录以下字段，供下游 S3/S4 复用，避免在 round 阶段重复推断 runner / 服务配置——
>
> ```json
> {
>   "scored_csv_path": "<OUTPUT_DIR>/scored.csv",
>   "eval_input_csv": "<EVAL_INPUT_CSV>",        // 原始测评集，供 S4 §2 小样本提取使用
>   "eval_runs": [
>     {
>       "scope": "full | partial",
>       "session_turns": "13:4,15:2",
>       "eval_output_csv": "<OUTPUT_DIR>/eval_output.csv 或 eval_output.partial.csv",
>       "scored_csv": "<OUTPUT_DIR>/scored.csv 或 scored.partial.csv",
>       "merged_eval_output_csv": "<OUTPUT_DIR>/eval_output.merged.csv 或 null",
>       "merged_scored_csv": "<OUTPUT_DIR>/scored.merged.csv 或 null"
>     }
>   ],
>   "eval_runner": "scripts/run_eval/<framework-version>/run_eval.py",
>   "eval_runner_framework": "<framework-version>",
>   "service": {
>     "lifecycle": "external",                    // 本 skill 默认 external（推荐路径）
>     "health_url": "<SERVICE_URL>/healthz",
>     "url_args": ["--url", "<SERVICE_URL>"]      // 透传给 runner 的服务参数
>   },
>   "scorer_prompt": "scripts/score/<biz>_score.md"
> }
> ```
>
> 走"已有 scored CSV"分支时（用户直接给 scored），manifest 中 `eval_runner` / `service` 字段缺省（S4 启动时会按其 §前置检查 §5/§8 兜底询问）；只有走 1a-bis 自跑过 eval 时才强制写入。

> **局部 trace 更新**：局部模式只为目标 key 对应的新 `thread_id` 拉取 trace，并更新 `analysis_manifest.json.cases[]` 中同一 `(session_number, turn_number)` 的 `thread_id` / `trace_path`。其他 case 的 trace 与 manifest 条目保持不变，避免局部验证污染既有分析范围。

### 1b. harness：Agent Harness 获取

**如果用户提供了 Agent 版本 ID**：自动拉取对应版本的 prompt 文件、工具定义、编排逻辑，产出标准化的 `Harness.md`。

**如果用户直接提供了文件**：做格式标准化后输出。

Agent Harness 是 Agent 运行时的"外壳"，主要由以下组件构成：

- **提示词（Prompts）**：system prompt、sub-agent prompt、few-shot examples 等
- **工具定义（Tools）**：工具名称、参数 schema、返回值结构、工具间依赖关系
- **中间件（Middleware）**：拦截器（Interceptors）、钩子（Hooks）——如输入预处理、输出后处理、工具调用前/后的校验逻辑、token 限制截断策略等
- **编排逻辑（Orchestration）**：Agent 间的路由/Handoff 规则、状态流转条件、重试与降级策略、并行/串行调度逻辑

无论何种形式，提取以下结构到 `Harness.md`：
- 各 Agent 的角色定义（Role）、目标（Goal）、执行规范（Execution Spec）
- 各 Agent 的 Working Loop 逻辑（特别是判断分支和异常处理）
- 中间件的拦截/Hook 点位及其对数据流的影响
- 工具策略（Strategy）中对工具结果的处理规则
- 输出格式规范（Output）
- Agent 之间的路由/Handoff 规则

**如果没有 Harness**：`harness_path` 在 manifest 中设为 `null`，下游 skill 自动降级为 trace 实录级归因。

### 1c. trace-fetch：Trace 获取

**默认获取评测集中所有 badcase 的 trace**（而非等 HITL 圈选后再拉取），这样后续增量分析时不需要重跑 auto-trace-prep。

> **v1.3 移除"用户直接提供 trace JSON 文件"分支**——下游 viewer / analyzer 已不再保留 raw 命名兼容性（参见 `core_skills/02_analyze/auto-single-case-analyzer/scripts/generate_feedback_viewer.py` 的 `trace-*-thread-*.json` 索引规则）；强制走脚本拉取保证清洗格式（analysis-compact 默认 / fetch_and_clean LangGraph beta）一致。维护者如需手工 raw 文件，请在脚本侧用 `--format raw` 输出，但**不**接 evoloop 主链路。

用户提供 trace 数据有两种方式，按优先级处理：

#### 方式 A：用户提供 thread_id

调用 skill 自带的查询脚本拉取 trace。脚本支持两套后端：

```bash
# 后端 1（推荐，零额外依赖；兼容任何 TraceBackend 部署）：langfuse-api
$PYTHON_CMD <skill_dir>/scripts/traces_fetch.py \
  --backend langfuse-api --format analysis-compact \
  --output $TRACES_DIR <thread_id>

# 后端 2（仅当有 trace warehouse 直连权限，吞吐略高）：clickhouse
pip install clickhouse-connect --break-system-packages 2>/dev/null
$PYTHON_CMD <skill_dir>/scripts/traces_fetch.py \
  --backend clickhouse --format analysis-compact \
  --output $TRACES_DIR <thread_id>
```

> **环境变量**（连接参数从脚本中解耦，由调用方在 shell 里 export，具体值见团队 wiki）：
>
> | 变量 | 后端 | 说明 |
> |---|---|---|
> | `TRACE_BACKEND_BASE_URL` / `TRACE_BACKEND_PUBLIC_KEY` / `TRACE_BACKEND_SECRET_KEY` | langfuse-api | TraceBackend public REST API 三件套 |
> | `CLICKHOUSE_HOST` / `_PORT` / `_USERNAME` / `_PASSWORD` / `_DATABASE` | clickhouse | trace warehouse 直连 |
> | `TRACE_BACKEND_PROJECT_IDS`（逗号分隔） | clickhouse | trace warehouse IN 子句过滤；可被 `--project` 覆盖 |
> | `TRACE_BACKEND_TRACE_CREATED_AFTER`（ISO datetime，默认 `2025-01-15 00:00:00`） | clickhouse | trace 时间下限 |
> | `TRACES_FETCH_CONCURRENCY` | 通用 | 批量并发默认值（被 `--concurrency` 覆盖） |
>
> 缺失任一必填变量时脚本硬失败（`sys.exit` + 引导文案），不会静默走错路径。
>
> **`$PYTHON_CMD`**：使用环境检测阶段确定的 Python 可执行路径。首次执行时参照 `references/environment-setup.md` 完成检测。
>
> **后端选择**：
> - 跨实例 / 测试 / SaaS TraceBackend → 选 `langfuse-api`（默认推荐；只需 PK/SK，无需 trace warehouse 直连）
> - 已有 trace warehouse 直连权限 + 主 TraceBackend 实例 → `clickhouse`（吞吐高一点，并发场景下显著）
>
> **格式选择**：推荐 `analysis-compact`（在 analysis 基础上去重 system prompt / toolDefinitions + 摘要化 tool 返回值 + 压缩对话历史），体积缩减 50-70%，显著降低 subagent token 消耗。
> 已废弃 `raw` 格式作为下游分析输入——下游 viewer / analyzer 已不再支持 raw 命名（`trace_{thread_id}.json`）作为索引源；如需手工导出兼容性，仍可输出但不接 evoloop 主链路。
>
> **替代后端（beta）**：如果项目侧已有按 LangGraph 五步清洗管线产出的 trace 习惯，可改走 `scripts/traces_fetch/fetch_and_clean.py`（与本节默认 `traces_fetch.py` **二选一**，不能并用）。详见下方"#### Beta：使用 fetch_and_clean.py 替代默认 trace 抓取" 段。
>
> **批量模式（CSV 输入）默认并发 4 路**，每路独立连接所选后端。
> - 单次调整：传 `--concurrency N`
> - 全局调整：设置环境变量 `TRACES_FETCH_CONCURRENCY=N`（适合 CI / 多用户共用 shell 环境，省去逐命令加 flag）
> - 优先级：CLI `--concurrency` > env `TRACES_FETCH_CONCURRENCY` > 默认 4
> - 单 thread_id 模式不受此参数影响。
>
> **服务端压力提示**：默认 4 路并发对单实例 trace warehouse 通常无压力；以下场景务必降到 2 或与 OPS 确认 `max_concurrent_queries` 配置——
> - CI 任务多人共用同一 trace warehouse 实例（同时跑可能击穿连接池）
> - 单次 CSV 包含 ≥200 个 thread_id（连接建立成本累积明显）
> - 跨 region 访问（网络抖动会让重试退避叠加放大）
>
> TraceBackend REST API 后端的速率限制取决于上游 TraceBackend 服务配置；如果触限，先降并发再考虑切 trace warehouse 后端。
>
> 失败重试已内建指数退避（5/10/20s + 抖动，仅 trace warehouse 后端），但不替代上游限流：脚本失败时会以非零退出码退出，CI 可据此报警。

#### 失败处理风格说明（设计意图，非缺陷）

本脚本与 evoloop 编排链路（auto-trace-prep / auto-single-case-analyzer / auto-fix-executor）刻意采用**两套不同的失败语义**，不应统一：

| 层 | 失败语义 | 触发场景 | 决策依据 |
|---|---|---|---|
| 脚本层（`traces_fetch.py`） | **硬失败**——任一 thread_id 满足下列任一条件即纳入 `failed`，最终 `sys.exit(非零码)`：①重试用尽抛异常；②**`written == 0`（空导出，trace warehouse 查不到任何 trace）** | 数据缺失场景：CSV 中要求的 trace 拉不全或某 thread_id 完全无数据 | 数据完整性是下游分析的前提；半全量数据会导致归因偏差，必须由 CI / 上游脚本感知并停下 |
| 编排层（SKILL.md 中的 LLM 流程） | **软降级**——单个 case 失败标 `format_warning` / `SKIPPED`，继续推进剩余批次 | LLM 推理异常 / 单 case 报告不合规 | 单 case 异常不应阻塞整批 case 的分析；编排层有 HITL 复核机制兜底 |

future direction: 跨 skill 统一并发参数（如 evoloop 全局 `MAX_CONCURRENCY` env / config）已记录为 backlog——详见 [`docs/backlog.md` § 跨 skill 统一并发参数](../../../docs/backlog.md)。本 PR 不做以避免范围扩散。

> **多 Project 过滤**（仅 `clickhouse` 后端用，`langfuse-api` 后端忽略——按 sessionId 过滤已足够）：
> ```bash
> # 通过环境变量列出多个 project（推荐）
> export TRACE_BACKEND_PROJECT_IDS=<project-id-1>,<project-id-2>
> $PYTHON_CMD <skill_dir>/scripts/traces_fetch.py --format analysis-compact --output $TRACES_DIR <thread_id>
>
> # 单次覆盖
> $PYTHON_CMD <skill_dir>/scripts/traces_fetch.py --project <project-id-2> --format analysis-compact --output $TRACES_DIR <thread_id>
> ```

脚本会按所选后端拉取 TraceBackend 数据，导出 analysis-compact 格式的 JSON 到指定目录。

如果查询失败（网络不通、trace warehouse 不可达 / TraceBackend REST 鉴权失败等），先确认环境变量是否完整（脚本会硬失败并指出缺哪个），其次切换 backend 重试，再次才考虑切到下方 fetch_and_clean.py beta（其后端为 TraceBackend SDK，鉴权 / 网络栈不同，可能绕开 REST 故障）；**不**再回退到"用户手工导出"路径。

#### 方式 B：从评测记录 Excel 中提取 thread_id

1. 读取 Excel，定位目标行
2. 寻找 `thread_id` 列——列名通常就叫 `thread_id`，但也可能有别名。如果没有明显匹配，列出所有列名让用户指定
3. 提取所有 badcase 行的 thread_id 值
4. 批量走方式 A 的查询流程

#### Beta：使用 fetch_and_clean.py 替代默认 trace 抓取

> **状态**：beta（v1.3 引入）。仅在以下任一场景启用——
> - 用户**显式**指定使用 `scripts/traces_fetch/fetch_and_clean.py`（如他们之前已经用此脚本人工跑过 trace 清洗，希望与 evoloop 链路统一）
> - 默认 `traces_fetch.py` 两套后端都失败（typically: REST/trace warehouse 都鉴权不通或网络不可达），fetch_and_clean.py 走 TraceBackend Python SDK，凭据栈不同，可能绕开问题
>
> **与默认管线互斥**：本 skill 单次运行只用一个 trace 抓取后端，避免同一 `$TRACES_DIR` 内两种命名 + 两种清洗格式混杂导致 viewer 索引模糊。

**清洗管线差异**（决定是否切换的关键）：

| 项 | 默认 `traces_fetch.py` | beta `fetch_and_clean.py` |
|---|---|---|
| 后端 | `langfuse-api`（REST）/ `clickhouse`（trace warehouse 直连） | TraceBackend Python SDK（HTTP 包装层，与 REST 后端鉴权方式相同但代码栈不同） |
| 清洗策略 | analysis-compact：激进去噪（仅保留 GENERATION + TOOL）+ system prompt / toolDefinitions 去重 + tool 返回值摘要 + 对话历史压缩 | LangGraph 五步：删 callbacks → 删 trace 根字段 → flat obs 重组为递归树 → 裁剪 invoke_llm/execute_tools/_route 基础设施节点 → 清理冗余 metadata / messages |
| 适用 framework | 任何 TraceBackend trace（与 framework 无关） | **仅 LangGraph 框架**（`name=LangGraph` + `invoke_llm`/`execute_tools`/`_route` 节点结构）。非 LangGraph trace 会因 `assert len(roots) == 1` 失败 |
| 输出文件命名 | `trace-<hash>-thread-<thread_id>-analysis-compact.json` | `trace-<trace_id>-thread-<thread_id>.json` |
| 体积缩减 | 50-70% | 通常 70-90%（去 callbacks 压缩比更激进） |
| 凭据 | `TRACE_BACKEND_BASE_URL` / `TRACE_BACKEND_PUBLIC_KEY` / `TRACE_BACKEND_SECRET_KEY` 或 trace warehouse 五件套 | `TRACE_BACKEND_BASE_URL` / `TRACE_BACKEND_PUBLIC_KEY` / `TRACE_BACKEND_SECRET_KEY`（仅 SDK 三件套；从项目凭据配置 自动加载） |
| 脚本依赖 | 0 额外依赖（标准库 + 可选 `clickhouse-connect`） | `pip install langfuse python-dotenv` |

> **viewer 兼容性**：默认与 beta 的输出文件名都满足 `trace-*-thread-*.json` 通配，`generate_feedback_viewer.py` 的 `trace_index` 解析两者皆吃；viewer 模板会把 `analysis-compact` 与 beta `langgraph-clean` 归一化后展示，至少包含格式、trace/thread id、消息上下文、调用节点、token/cost 摘要和 raw JSON fallback。single-case-analyzer 的归因深度仍会因清洗管线不同而有差异。**如对 LangGraph 编排链路细节（如 `_route` 决策、`invoke_llm` 重试）有强归因需求，beta 更合适**；其他场景默认管线更通用。

**触发与切换**：

> **单 vs 批量阈值**：N=1 个 thread_id 直接走单次模式；N≥2 推荐预先写一份 CSV（仅一列 `thread_id`）走批量 CSV 模式（避免 N 次重复连接 + 让脚本自身的进度条工作）。`--limit 50` 是"每个 thread_id 拉取 trace 数量上限"——单/批量都可加，默认 50 条 trace/thread 通常够；只在 thread 内 trace 异常多（>50）时才提高。`--concurrency 4` 仅批量模式生效。

```bash
# 启用 beta - 单 thread_id 模式（N=1）
$PYTHON_CMD scripts/traces_fetch/fetch_and_clean.py <thread_id> \
  --output "$TRACES_DIR" --limit 50

# 启用 beta - 批量 CSV 模式（N≥2，推荐）
# 先把所有 badcase thread_id 写入一列 CSV：
#   echo "thread_id" > "$BADCASE_THREAD_IDS_CSV"
#   for tid in $thread_ids; do echo "$tid" >> "$BADCASE_THREAD_IDS_CSV"; done
$PYTHON_CMD scripts/traces_fetch/fetch_and_clean.py "$BADCASE_THREAD_IDS_CSV" \
  --output "$TRACES_DIR" --concurrency 4 --limit 50
```

> **anchor 兼容性提示**：fetch_and_clean.py beta 常见使用场景是非 biz_a/biz_b/biz_c 的 LangGraph 项目（本仓库 host <host_runtime_doc> 的 anchor 表只覆盖这 3 家 biz）。**如项目不在已知 biz 列表**，跳过 <host_runtime_doc> "Skill artifact 锚点" 表，回退到本 SKILL §"输出目录命名规则" 优先级 2（默认规则：评测文件同级目录创建 `badcase_analysis_{MMDDHH}/`）；不要试图在 `projects/<biz>/...` 下硬建一个不存在的 biz。

> **manifest 字段**：beta 启用时在 `analysis_manifest.json` 中记录 `trace_fetch_backend: "fetch_and_clean"`（默认管线为 `traces_fetch_default`），便于后续维护者复盘当前 round 用的哪条管线 + 失败时定位。

**失败语义**：beta 与默认管线一致采用硬失败。单个 thread_id 查不到 LangGraph trace、SDK 鉴权失败、断言失败，或批量 CSV 中任一 thread_id 失败，脚本都会以非零码退出；批量 CSV 会保留输入顺序并自动去重，便于和 badcase 列表对齐复盘。

**降级路径**：beta 失败时，先看脚本 stderr 的 traceback，再切回默认 `traces_fetch.py`；不要混用——切换前先 `rm -f "$TRACES_DIR"/trace-*.json` 清空已部分写入的产物。

---

## 多版本场景：评测数据采集 & 矩阵构建 & 轨迹分类

当用户提供了多个版本的评测数据时，进入多版本场景。

### 评测数据采集

数据来源灵活，没有默认格式——用户可能提供：

- **多份 Excel/CSV**：每份对应一个版本的评测结果
- **单份 Excel/CSV**：包含版本标识列（如 `agent_version`、`model_version`），不同版本的结果混在同一个文件中
- **多份 Excel + 分散的 trace 文件**：评测记录和 trace 分开提供

**采集步骤**：

1. 识别用户提供了几个版本的数据、数据格式是什么
2. 对每份数据，确定以下关键信息：
   - **版本标识**：这份数据对应的 Agent 版本名称（如"V1.0"、"V2.0"、"SFT-32B"）
   - **Case 对齐键**：用于跨版本匹配同一 case 的字段——通常是 `user_query`、`case_id`、或 `test_case_index`
   - **评分字段**：评分列名、评分值范围
   - **Thread ID 字段**：每个版本的 thread_id 列名
3. 如果无法自动识别上述信息，**立即向用户提问澄清**，不要猜测

**Case 对齐**是交叉对比的前提。对齐策略：
- 优先用 `case_id` / `test_case_index` 等显式 ID 字段
- 其次用 `user_query` 文本精确匹配
- 如果都不行，用 `user_query` 模糊匹配，但必须向用户确认匹配结果

### 评分折算（HITL——仅当评分非 1/0 时触发）

矩阵构建需要每个 case 在每个版本上有一个二值结果（pass/fail）。如果评测数据的评分不是 1/0：

1. 读取评分值范围
2. **使用 AskUserQuestion 工具向用户确认折算标准**：

```
评测数据的评分范围为 [范围]。交叉对比需要将评分折算为 pass/fail。

请定义折算标准（示例）：
(a) ≥3 分为 pass，<3 分为 fail
(b) 仅满分（5分）为 pass，其余为 fail
(c) 自定义阈值：___
```

3. 拿到折算标准后，将所有评分转为 1（pass）/ 0（fail）

### 矩阵构建

构建 `N_cases × M_versions` 的二值矩阵：

```
             V1    V2    V3
case_001      1     1     0
case_002      0     1     1
case_003      0     0     0
case_004      1     0     1
```

### 轨迹模式分类

基于矩阵，将每个 case 分类到以下轨迹模式中：

| 轨迹模式 | 定义 | 分析价值 |
|---------|------|---------|
| **一直好** (all_pass) | 所有版本都 pass | 低——不需要分析 |
| **一直坏** (all_fail) | 所有版本都 fail | 中——顽疾，值得找共性根因 |
| **退化** (regression) | 早期版本 pass → 后期版本 fail | **最高**——回归问题 |
| **修复** (fixed) | 早期版本 fail → 后期版本 pass | 中——验证改进是否真正有效 |
| **波动** (unstable) | pass/fail 交替，没有单调趋势 | 高——可能是 prompt 灵敏度 |

**2 版本场景**（最常见）：
- V1=1, V2=1 → all_pass
- V1=0, V2=0 → all_fail
- V1=1, V2=0 → regression
- V1=0, V2=1 → fixed

**版本顺序**：如果用户未明确指定版本的时间/逻辑顺序，需要询问确认。

---

## `analysis_manifest.json` Schema

```json
{
  "analysis_id": "badcase_analysis_032514",
  "created_at": "2026-03-25T14:00:00Z",
  "eval_source": "path/to/scored.csv",
  "eval_input_csv": "projects/<biz>/evals/input_<biz>.csv",
  "scored_csv_path": "{analysis_root}/eval_runs/<framework-current>_20260325/scored.csv",
  "eval_runs": [
    {
      "scope": "full",
      "session_turns": null,
      "eval_output_csv": "{analysis_root}/eval_runs/<framework-current>_20260325/eval_output.csv",
      "scored_csv": "{analysis_root}/eval_runs/<framework-current>_20260325/scored.csv",
      "merged_eval_output_csv": null,
      "merged_scored_csv": null
    }
  ],
  "agent_versions": ["v2.1-baseline", "v2.2-modified"],
  "harness_path": "{analysis_root}/Harness.md",
  "schema_path": "{analysis_root}/schema.json",
  "trace_fetch_backend": "traces_fetch_default",
  "eval_runner": "scripts/run_eval/<framework-current>/run_eval.py",
  "eval_runner_framework": "<framework-current>",
  "scorer_prompt": "scripts/score/biz_a_score.md",
  "service": {
    "lifecycle": "external",
    "health_url": "http://localhost:8088/healthz",
    "url_args": ["--url", "http://localhost:8088"]
  },
  "cases": [
    {
      "case_id": "case_017",
      "thread_id": "p-20260302-182813-54eb5c",
      "trace_path": "{analysis_root}/traces/trace-<hash>-thread-p-20260302-182813-54eb5c-analysis-compact.json",
      "eval_row": { "user_query": "...", "actual": "...", "reference": "...", "score": 0 },
      "version": "v2.2-modified",
      "paired_trace_path": null,
      "selected": true,
      "analysis_mode": "direct"
    }
  ]
}
```

**字段说明**：
- `eval_source`：本 skill 实际解析的 scored CSV/Excel 路径（即"列类型识别"段消费的输入）。走 1a-bis 时为本 skill 跑出的 scored CSV；走"已有 scored"分支时为用户提供的原文件
- `eval_input_csv`：测评集**输入**（含 `user_query` / `dialog_history` 等列，**无** `actual_output`/评分），供 S4 §2 小样本提取使用。走"已有 scored"分支时**可缺省**——S4 启动时会按其前置检查 §兜底询问
- `scored_csv_path`：仅在走 1a-bis（本 skill 自跑 eval）时写入，等于 `eval_source`；走"已有 scored"分支时缺省
- `eval_runs`：记录 1a-bis 产生的 eval/score 运行；`scope` 为 `"full"` 或 `"partial"`，局部模式必须记录 `session_turns` 和局部/merge 后产物路径
- `paired_trace_path`：仅在多版本场景下填充（baseline vs modified），单版本时为 `null`
- `selected`：默认 `true`（全量可分析），HITL 1 中人可以修改为 `false`
- `analysis_mode`：默认 `"direct"`（直接归因），多版本场景下可改为 `"compare"`（对比归因）
- `trace_fetch_backend`：取值 `"traces_fetch_default"`（默认 analysis-compact 管线）或 `"fetch_and_clean"`（beta LangGraph 五步管线）；用于 S2/S4 阶段判断 trace 文件清洗格式。**单 round 内冻结**：一旦 manifest 写入该字段，本轮分析所有 trace 必须出自同一后端；后续如需切换（如 beta 失败回退到 default）必须按 §1c "Beta 降级路径"先 `rm -f $TRACES_DIR/trace-*.json` 清空残留再覆写本字段——混用未定义行为
- `eval_runner` / `eval_runner_framework` / `scorer_prompt` / `service.*`：仅走 1a-bis 时强制写入（供 S4 复用，避免 round 阶段重复推断）；走"已有 scored"分支时**全部可缺省**，S4 前置检查 §5 / §8 会按需 AskUserQuestion 兜底
- **`service.*` 安全约束（强制）**：仅允许写入服务**端点**信息（`lifecycle` / `health_url` / `url_args` / `start_args`）。**禁止**写入任何凭证（凭据 / 凭据 / DB 密码）——manifest 是明文 JSON 落盘到 round 目录、可能进 git，凭证泄露风险高。凭证一律走环境变量或凭据配置（如 `<SCORER_KEY_ENV>` / `<COMPATIBLE_LLM_KEY_ENV>` / `TRACE_BACKEND_*`），本字段不承担凭证传递

---

## HITL 1：信息澄清 + 分析范围标注

**位置**：物料准备完成后、skill 结束前执行。

**前置条件**：auto-trace-prep 已默认拉取所有 badcase 的 trace，manifest 中所有 case 默认 `selected: true`。

### 单版本场景

使用 `AskUserQuestion` 向用户确认：

1. **schema.json 的列类型映射是否正确**（特别是 actual vs reference 列的语义）
2. **版本信息**（单版本 vs 多版本 + 基线）
3. **分析范围**：基于 badcase 的问题分类分布，提供三种筛选策略

展示格式：

```
评测记录中共有 N 条 badcase，已全部拉取 trace。请选择分析范围：

(a) 按问题类型抽样（推荐）
    当前分布：[类型A] x条, [类型B] x条, [类型C] x条, ...
    每种类型抽取 1-2 条典型 case，预计分析 M 条

(b) 某类问题专项分析
    请选择要深入分析的问题类型：
    [1] [类型A] — x条
    [2] [类型B] — x条
    [3] [类型C] — x条
    ...

(c) 人工自定义
    请指定要分析的行号（如 "5,8,13" 或 "5-10"）或筛选条件（如 "所有评分为0的"）
```

**问题类型分布的获取方式**：
- 优先使用评测记录中已有的 `problem_category` / `问题分类` / `问题分析` 列
- 如果没有人工标注的分类列，则根据 `score_reason`（评分理由）列做轻量聚类，提取高频关键词作为临时分类
- 如果既没有分类也没有评分理由，则退化为展示 badcase 列表，让用户按编号选择

**选项 (a) 的抽样策略**：
- 每种问题类型抽取 1-2 条，优先选择评分最低（问题最严重）的 case
- 总数控制在 10 条以内为宜

**如果选定的 case 数量超过 20 条**，主动提醒用户：

```
当前选定 N 条（超过建议上限 20 条）。建议分批分析——先分析前 20 条，后续 case 可在下一轮对话中继续。
是否继续分析全部 N 条，还是调整范围？
```

### 多版本场景

在单版本确认的基础上，额外展示：

1. **矩阵概览 + 轨迹分类统计**
2. 让用户选择分析的轨迹模式和具体 case
3. 对选定的 case 配置 `analysis_mode`（`direct` 或 `compare`）

```
## 交叉对比矩阵概览

版本：V1 (baseline) → V2 (current)
测试集：共 N 条 case

| 轨迹模式 | 数量 | 占比 | 分析价值 |
|---------|------|------|---------|
| 退化 (V1✓→V2✗) | X | XX% | ⚠️ 最高 |
| 修复 (V1✗→V2✓) | X | XX% | 中 |
| 一直坏 (V1✗→V2✗) | X | XX% | 中 |
| 一直好 (V1✓→V2✓) | X | XX% | 跳过 |

请选择要分析的轨迹模式（可多选）：
(a) 退化 case（推荐首选）
(b) 修复 case
(c) 一直坏的顽疾
(d) 自定义——指定具体 case 编号
```

### 输出

`analysis_manifest.json (confirmed)` —— 未被选中的 case 保留在 manifest 中（`selected: false`），其 trace 文件也保留在 `traces/` 目录。后续增量分析只需修改标签，无需重跑 auto-trace-prep。

**下游前置条件**：auto-single-case-analyzer 启动时检查 manifest 是否存在且包含至少 1 个 `selected: true` 的 case。

---

## 幂等性保证

同一份 Excel + 同一组 thread_id → 产出相同的 manifest 和 trace 文件。trace-fetch 是纯获取操作，eval-data 是纯解析操作，harness 是纯格式化操作。由于默认拉取所有 badcase trace，后续增量分析只需 HITL 1 修改 `selected` 标签，不需要重跑此 skill。

---

## 环节结束提醒

当 HITL 1 确认完成、`analysis_manifest.json (confirmed)` 已写入后，**必须**向用户展示以下后续操作指引：

```
✅ 物料准备完成！analysis_manifest.json 已确认，共选定 N 条 case 待分析。

📋 后续操作：
1. 输入 /compact 压缩当前上下文（推荐，释放 token 空间给下一环节）
2. 输入 /auto-single-case-analyzer 启动归因分析
```

> **元反思推荐判定**（AI 自行评估，判定逻辑不向用户展示）：若本轮执行暴露了方法论的结构性漏洞（自行判断——HITL 反复 / 跨层字段未被消费 / 跨轮口径漂移 / 其他非预期摩擦皆是线索），**在上述列表首位插入一条** "1. （新建分支/branch）然后输入 /meta-reflection 做元过程反思 — 触发理由：<一句话>"，原条目编号顺延；本轮顺畅则不追加，**不要给"可选"等通用提示**。
