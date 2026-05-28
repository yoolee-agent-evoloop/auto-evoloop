# Skill 内容熵增治理 Checklist

适用于所有修改 `core_skills/**/SKILL.md` 的 MR/PR。作者自检 + reviewer 复核。

## 原则

1. **单一权威源 + 单向引用**：同一条规则、schema、enum 只有一处定义文本；其他位置只引用，不复述。
2. **不为可能的未来加 enum / 抽象 / 分支**：新增的 enum 值、JSON shape、渲染分支，每一个都必须有当前已存在的下游消费者。
3. **新增内容必须进主索引**：新 artifact / 文件 / 配置项必须登记进该 skill 的「输出 Artifact」清单或等价索引。不进索引的产物会被忘记、被重新发明。

## 作者自检

提交 `skill:` 前缀 commit 前逐条过：

- [ ] 新增章节是否复述了同一 SKILL.md 内已有规则？→ 合并为一处，其余引用
- [ ] 新增 enum 值是否每个都有当前下游消费者？→ 无消费者的值删除
- [ ] 同一 schema / 数据结构是否有 2+ 处描述源？→ 择一为权威，其余标 `see §X`
- [ ] 新增 artifact 是否登记进「输出 Artifact」清单？
- [ ] 文本 + 代码块/JSON 是否对同一信息双重呈现？→ 择一保留
- [ ] viewer / script 端的 schema 假设是否散落多处硬编码？→ 抽 const 表集中维护
- [ ] 新增的兼容分支（JSON shape / 字段别名）是否标注了 canonical vs legacy？
- [ ] 可选步骤是否被升格为主流程编号？→ 降级为文末补充说明

## 量化信号

reviewer 可用以下命令快速感知篇幅变化：

```bash
# SKILL.md 行数变化（MR 前后对比）
git diff master --stat -- 'core_skills/**/SKILL.md'

# 约束密度（"禁止"/"必须"/"不得" 出现次数）
grep -cE '禁止|必须|不得|不允许' core_skills/<stage>/<skill>/SKILL.md

# 同义重述嗅探（同一文件内相似度高的段落）
grep -n 'fallback\|三选一\|授权.*subagent' core_skills/<stage>/<skill>/SKILL.md
```

行数增幅超 20% 时建议 reviewer 重点检查上方 checklist。

## 参考案例

- [MR!11 — skill: improve S2 viewer HITL workflow](https://primary.aliyun.com/<primary-org-id>/<primary-repo-path>/change/11)：v1 「并行执行策略」4 子节复述同一规则 → v3 合并为 1 节，enum 从 4 值收到 3 值，schema 描述源从 3 处收到 1 处 + 2 引用，viewer JS 散落硬编码提升为 const 表。
