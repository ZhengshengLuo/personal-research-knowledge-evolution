# Module Dispatcher — 按交付成果分派

| 用户主要要求 | 主路由 | 当前可执行状态 |
| --- | --- | --- |
| 检索论文、代表综述、科学/方法论文、数据/代码、资源与候选证据 | `acquire` | `INSTRUCTION_READY`（指令协议 + 实际宿主工具能力检测） |
| 论文原文审阅、方法审查、具体 Figure 解读 | `understand` | `INSTRUCTION_READY`（宿主视觉能力 + 本地解析/核验工具） |
| 既有知识检索、管理、正式入库与笔记 | `organize` | `INSTRUCTION_READY`（只读 Zotero + 受控本地 Vault 更新） |
| 多篇证据综合、科学争议、Research Gap 及假设演化 | `synthesize` | `INSTRUCTION_READY`（宿主科研判断 + 本地证据结构/Gap 演化） |

优先按最终交付物决定主模块；只有必要时加辅助模块。单纯语言翻译不应该触发科研 Skill。

## Router → 模块 → Router

- 路由前读取 `router/interfaces/module-registry.json`，检查状态和外部工具权限。`INSTRUCTION_READY` 表示协议可读取，**不保证工具可用**；`NOT_CONNECTED` 不得假装已运行。
- 向已接入模块提供符合 `schemas/router/module_request.schema.json` 的请求，并核实真实结果符合 `module_result` schema；其真实文献候选产物参见 `schemas/acquire/candidate_set.schema.json`。
- Acquire 完成仅表示约定的文献**发现**阶段完成；不能把其元数据或摘要推荐当作原文核验或学术定论。只有显式调用具体工具并收到可检查结果后才可报告实际执行。Understand 仅在查看原图后才能记录视觉核验；Organize 已有明确授权的正式 Vault 批次写入工具，但 Router 默认 P0/P1；只有可信宿主取得具体授权才能调用 commit。
- 无对应模块但有宿主独立工具时，可透明使用该工具完成用户任务，不得伪装成模块已连接；保留任务来源、证据状态与下一步限制。
- 重大偏离 Mission/硬预算或正式权限时返回 Router 重新规划或征询用户。不能直接让子模块修改 Workspace 或正式知识库。
