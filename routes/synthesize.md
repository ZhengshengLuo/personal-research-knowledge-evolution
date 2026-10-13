# Synthesize｜跨论文科学综合与 Research Gap Evolution（v1.5.0-rc1）

执行本路由前阅读 `SKILL.md`、`references/synthesize/evidence-and-gap-gates.md` 与相关 Router 协议，避免自动补造证据。

## 模式
- `TOPIC_INCREMENTAL`：由 Organize 对某 Topic 新增 ≥10 篇去重有效 Paper UID 或核验的重大反证触发，对**旧+新**证据复核；允许 `NO_MATERIAL_CHANGE`，不得强制制造 Idea。
- `FOCUSED_SYNTHESIS`：围绕指定 Research Question 的科研综合；检索边界和论文质量说明清楚。
- `SYSTEMATIC_REVIEW`：需要用户确认检索方案/范围与真实筛选审计；默认无法直接声称完成发表级系统综述。

## 工作流
1. 确认任务、Topic、论文来源版本及可用原文证据。优先从 Organize、Understand 获得经过审查的 claim-evidence；资料不足时请求 Acquire。
2. 建立统一 Evidence Matrix；记录可比性、重复使用数据、研究设计、估计目标和来源定位。科学主张的强度不超过原始证据。
3. 由宿主科研 Agent 对同一问题下的证据开展定性综合。不得凭相同方向数量简单表决；区分作者解释、Agent 解读和研究者判断。
4. 分析真实冲突与表面差异。针对重要争议有界检索相关原始研究，保留搜索式、数据库、时间与未获得的 PDF 清单。
5. Gap Discovery 的每个候选必须有支持证据，提交 closest prior work 和反证搜索记录，缺项标 PARTIAL。
6. 使用 `scripts/synthesize_cli.py stage --input <reviewed_evidence_packet.json> --output <new_stage_dir>` 生成不写正式库的结构化综合草稿。其科研解释是待人审底稿，不是 AI 自动完成的独立科学验证。
7. 若涉及 Gap 演化，经 `scripts/knowledge_cli.py` 在库外 stage 生成 Topic 管理区/Gap Overview/append-only Ledger；**提交须显式批准计划 sha 与受控写入**，重大修改需要额外的人类批准，不能将 CLI ack 当成身份认证。
8. 结果通过 Router 现有 `module_result` 的 COMPLETED/PARTIAL/BLOCKED 反馈；模块自己须保留独立科学质量状态。

## 限制
- 当前本地工具不实现独立的语义大模型审稿、自动外部检索或通过真正用户身份签名的审批服务；这些由宿主已授权 Agent/工具协作完成，实测结果分别标记。
- 未经科研者明确同意，不向外部传输内部实验、未公开手稿和受限 PDF。
- 调度器的独立 Windows 后台运行需另行授权，不能假装聊天会话退出后自动继续。
