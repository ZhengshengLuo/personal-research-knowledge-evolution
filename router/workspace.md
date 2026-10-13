# Workspace Resolver — 多研究空间与一份知识资产

## 三层对象
- `Research Workspace`：长期研究上下文与知识视图（科研领域、通用方法、科研写作都可以）。不是单独数据库。
- `Research Task`：一次有目标的科研活动，可很短，也可多阶段、跨会话；任务生命周期与知识价值不相关。
- `Knowledge Asset`：稳定 ID 的 Paper / Reading Note / Claim / Evidence / Method / Concept / Synthesis / Research Idea，独立于产生它的任务。
- `Relation`：用于连接这三层的有类型、带来源、可审计关联；同一 Asset 可以关联多个 Workspace，不复制其规范身份。

## 关联规则
1. 用户指定 Workspace 且已有匹配 ID 时优先使用；对明显冲突提出说明，不能凭空编造 ID。
2. 检索经批准的 Workspace 注册表，根据名称/别名/范围/核心问题推断 0..n 个可能相关的空间，记录 rationale + `USER_CONFIRMED` 或 `INFERRED_FROM_CONTEXT`。
3. 当前 Task 的 `TASK_IN_WORKSPACE` 可以在**仅任务上下文**中自主建议；不等于正式永久关系。
4. 无可靠匹配时 `unassigned`，仍允许检索/阅读；不自动生成一个长期「未分类」Workspace。
5. 当需要长期新空间时生成 `workspace_proposal`（创建/改名/合并/拆分/归档的理由、边界、重叠、受影响资产预览）。用户明确批准后才创建。对已有规范知识的永久重归属仍进入 P2 批次审批。
6. 改名维持 `workspace_id`，旧名进入 aliases；合并记录重定向，不复制或删除关联资产；归档空间保留历史。

## 科学关系边界
`EVIDENCE_SUPPORTS_CLAIM`、`METHOD_APPLICABLE_TO_TOPIC` 等不能只凭关键词或 embedding 相似建立事实关系。候选关系标记 `PROPOSED`；源证据、适用边界与审核状态一同记录。新的反证需要留下历史版本与双方条件，而不是覆盖旧认识。
