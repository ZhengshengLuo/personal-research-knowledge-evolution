# Organize — PRKE v1.5.0-rc1（本地知识整理与安全入库）

## 明确范围

由 Router 分派知识管理任务，**不得绕过用户授权自动修改正式 Vault**。本阶段业务协议和本地 CLI 已具备，Zotero 主机连接以及真实 Windows/Obsidian GUI 操作尚待现场验收。Synthesize 当前为 `INSTRUCTION_READY`，但只有宿主实际获得并审查文献、执行真实综合任务，才能声称科学综合已开展；阈值状态本身不构成综合完成。

- Zotero：只读 `GET http://127.0.0.1:23119/api/`，读取真实元数据与可用附件/批注信息；绝不更新 Zotero 条目、PDF 或 SQLite。
- Obsidian：一个长期 Vault（约定 Windows 路径 `E:\Research_Knowledge_Base`），目录无编号；Papers/ 与 Readings/ 扁平化，一篇论文对应至多两篇主 Markdown。已有实验项目其他路径不自动纳入。
- Excel：仅按需结构化导出，非另一个权威数据库；已提供可选 `scripts/export_excel_cli.py`（需要 Windows 环境额外验证 artifact_tool 依赖）。
- 知识对象：Paper / DeepReading / Topic(Domain/Question) / Method / Data / Workspace / Idea，后者重要新建和 Idea 正式化均须用户确认。
- 稳定主键：规范化 DOI 优先、无 DOI 时原始 PDF SHA（此为临时退化策略；跨版本身份合并须人工确认），已在 Zotero 的真实 Key + Library ID 才可关联，否则 `ZOTERO_PENDING`。
- 已有 Topic/Method/Data 可有证据增补，但重要综合结论不覆盖；由 `knowledge_cli.py` 在库外 stage 生成候选更新、Gap Overview 与事件账本；依据真实 plan SHA 与批次确认后才能提交。

## 实际命令与职责

`python scripts/organize_cli.py doctor` 验证协议。
`python scripts/organize_cli.py zotero-probe --limit 3 --children` 真实 Zotero 只读检测。
`python scripts/organize_cli.py init-vault --vault PATH` 预览；只有 `--execute --acknowledge-empty-vault` 才创建空白 Vault，已有内容则阻断。
`python scripts/organize_cli.py stage-paper --paper-dir DIR --vault VAULT --stage-dir NEWDIR` 读取 Understand 原证据，对原 PDF 重新做哈希检查和审计，只在 Vault 外生成 Paper/Reading 草稿、长期证据快照与 plan；完成正式 DEEP 才生成 Reading。审计 PARTIAL 只可显式 `--allow-partial` 生成 Paper。
`python scripts/organize_cli.py commit --stage-dir DIR --vault VAULT --approve-plan-sha256 HASH --acknowledge-vault-write` 单独的明确批次写入操作。要求人类先核对计划和差异；命令标志本身不构成无法伪造的人工身份验证，生产模式仍需独立的宿主审批/OS 权限隔离。

严禁将初次 `prepare`、`audit COMPLETED`、数据结构有效或受控提交成功，描述成独立科学结论的证明。PRKE 管理来自 Understand 的证据及其核验边界。

## v1.5 协作工具

`knowledge_cli.py stage` 生成 Topic AI 区 / Research Gap Overview / Gap Ledger 的持久化计划；`stage-knowledge` 仅更新指定 Topic/Method/Data 的 AI 管理区；`stage-decision` 在研究者明确批准后交接 Gap 决策或正式 Idea。提交和恢复均有独立命令，禁止覆盖人工区或陈旧来源。

`trigger_cli.py check` 处理有效唯一 Paper UID 的10篇阈值与 pending 状态；`complete` 只有将该轮新增论文真实纳入综合且结构审计完成，才记录轮次完成，不代表独立科学评估。未经单独授权绝不安装后台调度。

`evidence_assets_cli.py` 可通过真实源 PDF + 已核验 Figure Inventory 导出有页码及 SHA 的图像裁切候选，以及官方 Zotero 本地 API 只读批注快照。实际视觉核验、批注筛选和嵌入 Markdown 仍由宿主 Agent 完成。
