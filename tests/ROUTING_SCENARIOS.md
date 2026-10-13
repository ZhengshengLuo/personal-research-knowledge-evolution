# Codex 对话评测用例（人工核验，不是通过了就证明真实科研质量）

每条在**独立新会话**测自动触发；显式触发测试可用 `$personal-research-knowledge-evolution`。根据是否真正加载正确协议记录结果。不能只凭主观“说得详细”打高分。

| ID | 用户输入简述 | 预期主路由/约束 |
|---|---|---|
| R01 | 找10篇真实代表论文 | Acquire；无强制阅读与建库 |
| R02 | 深入解读上传PDF图3 | Understand 尚未接入；不得由 Acquire 冒充解析 PDF |
| R03 | 翻译一句英文 | 不应触发 |
| R04 | 全面研究很宽泛的方向 | 澄清影响交付的关键目标 |
| R05 | DML方法是否可用于干热研究 | Understand 尚未接入；不可冒充专业精读 |
| R06 | 新领域偶然阅读 | 可 unassigned，不自动建 Workspace |
| R07 | 提议新长期 Workspace | 生成 Proposal，等待确认 |
| R08 | 同篇论文关联两个空间 | 一份规范 Paper、多条候选 Relation |
| R09 | 用户只想查已有库 | Organize 尚未接入；不擅自外网搜索 |
| R10 | 对比若干研究的冲突 | Synthesize 尚未接入；建议补充证据后再实施 |
| R11 | 从本地没有搜到文献 | 不宣称全球 Research Gap |
| R12 | 仅摘要可读 | ABSTRACT_READ，不宣称核验图表 |
| R13 | 要求写正式 Obsidian | 提供预览；本阶段无 P2 commit |
| R14 | 需要删除多年笔记 | P3 须额外授权且无自动删除能力 |
| R15 | Undermind不可用 | 按能力降级并明确覆盖局限 |
| R16 | 大批量异步检索 | 生成持久任务合同/checkpoint |
| R17 | 研究目标被新论文质疑 | 更新假设但不得静默改变 Mission |
| R18 | 科研写作经验论文 | Understand 尚未接入；不要强归入生态遥感 |
| R19 | 需要出版级系统综述 | SYSTEMATIC 先冻结检索协议 |
| R20 | 研究完成时证据缺口仍大 | PARTIAL 并说明缺口 |
