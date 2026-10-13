# 直接交给 Windows Codex 的 PRKE v1.5.0-rc1 集成验收 Prompt

继续调用我提供的 **PRKE v1.5.0-rc1** 统一 Skill，在本机完成阶段 06 的首轮真实端到端验收。先读取指定目录下的 `SKILL.md`、`routes/{acquire,understand,organize,synthesize}.md`、`RELEASE_SCOPE.md`、`docs/ACCEPTANCE_PROTOCOL.md` 和 `router/governance.md`，严禁改用旧版分离 Skill。

**默认 Skill 路径**（先核实实际解压位置，再执行）：
`E:\Codex_workspace\05_AI提示词与工作流\SKILL创建\PRKE-v1.5.0-rc1-sandbox\personal-research-knowledge-evolution`

**已有 Krich 2021 正式审读任务（若现场仍存在）**：
`E:\Codex_workspace\05_AI提示词与工作流\SKILL创建\prke-live-test-20261013\understand\krich2021-functional-convergence`

**正式 Vault**：`E:\Research_Knowledge_Base`。本次默认**只读正式 Vault**，涉及知识变更必须在全新隔离测试 Vault 中操作。不得修改现有 v1.4.0 Skill、真实 Zotero 或原始 PDF。

## 1. 基线与安全
1. 保存原 v1.4.0 完整安装包的 SHA256，核对新包文件清单与唯一 SKILL.md；运行 Router/Acquire/Acquire PDF/Understand/Organize/Synthesize/Knowledge/Trigger doctor。用实际 `--help` 确认新 CLI 用法。
2. 在 Windows 默认编码与 UTF-8 环境分别执行 `python -m unittest discover -s tests -p "test_*.py"`；记录测试数量、失败或 skip，不得伪报。
3. 显式核对 Source PDF 不变、Zotero 只执行 GET、Vault 人工区不被覆盖，任何未经批准的正式提交必须被阻断。

## 2. 单篇真实论文交接
4. 如 Krich 2021 的 Understand 工作目录完整，重新审计其原文 PDF、Figure Inventory、Claim–Evidence Matrix 以及审计 status，实际检查关键原始图表，确认没有以图注/OCR 代替视觉核验。
5. 运行 `scripts/evidence_bridge_cli.py --paper-dir <Krich工作目录> --topic-id SIF-环境相互作用 --research-question "..." --output <独立任务目录/synthesis_input.json>`，建立来源真实的 Synthesize Input。不得自动把 `NOT_ASSESSED`、`UNCLEAR` 变为支持证据。
6. 在实际查阅已有原文和可访问学术资料后，人工科研 Agent 补充研究背景、设计、证据方向、时间尺度、来源独立性、跨文献主要综合结论。执行 `scripts/synthesize_cli.py stage --input <科学审读后的输入JSON> --output <新的Synthesis任务目录>`；核对 Evidence Matrix、主要 Claim Ref、`AI_SYNTHESIS_DRAFT`、审计状态。

## 3. 知识库隔离闭环
7. 只在新建空白**实验 Vault** 中运行 Organize `init-vault`。执行 `knowledge_cli.py stage` 生成 Topic Note、唯一 Research Gap Overview、Gap Evolution Ledger，检查原生 Markdown/Mermaid 和稳定 Gap ID。Stage 不得改变正式 Vault。
8. 显示 Plan SHA 与拟写入变更，实验 Vault 中完成一次经过明确同意的 `knowledge_cli.py commit`；再次执行相同输入，必须幂等拒绝；在 Topic 人工区插入测试文字，确认下一轮候选演化不会删除该文字。
9. 独立测试未经批准的重大 Gap 修订保持 `PENDING_HUMAN`；用 `stage-decision` 预览批准/拒绝后，再由独立测试批准完成；检查事件历史前后可追溯，不允许修改过去事件。
10. 测试 Method/Data 的 `stage-knowledge`：已有节点可追加带真实证据的 AI 管理部分；重要新节点无明确确认不得创建。`APPROVE_IDEA` 只能按用户批准的独立批次产生正式 Idea Note。

## 4. 十篇自动触发与研究分歧
11. 用**合成有效性记录**测试第9/10篇阈值、重复UID/版本去重、重复check不重复排队、PARTIAL不重置成功门槛、失败恢复与安全降级。合成记录不能充当科学论文。
12. 使用真实已获得全文的多篇文献，构建同题 Evidence Matrix，重点区分数据共享、估计目标、科学解释和因果识别。发现 Candidate Gap 时通过 Acquire/真实学术检索工具主动搜寻 closest prior work 和反证，记录数据库/日期/检索式/未找到的资料及失败原因。缺外部核验须 PARTIAL，不得声称首次创新。
13. 验证科学综合没有创造未经原文支持的数值、图号、引用和因果处理效应。对允许的内部实验，保持 `INTERNAL_EXPERIMENT` 标识，不向外部上传实验文件。

## 5. 正式验收剩余工作
14. 真实 Zotero 连接、原始批注快照、原图精确裁切以及按需五表 Excel 导出分别报告完成情况；若 Zotero 不运行或可选 Excel 依赖不可用，明确报告，不通过伪造数据弥补。
15. 根据 Gold Set 空白模板规划3–5篇真实论文的**独立人工复核**，不要把本次 Agent 的自评当成独立核验。没有真实完成就标记 NOT_RUN。
16. 不立即创建 Windows Task Scheduler 任务，不提前开始 24h；先核对 `soak_cli.py --help`、恢复与时间验证要求。只有我另行同意安排后台运行后，才执行真实≥24h窗口、重启模拟和人工检查。

**最终只需准确汇报：** 所有 doctor/旧回归/新增测试数量与原始日志、真实 Krich 2021 交接、Synthesize 来源对齐与 Gap 反证质量、实验 Vault 写入与回滚、Topic/Method/Data/Idea 状态、10篇触发安全、各模块 `OFFLINE_TESTED`/`LIVE_TESTED`/`NOT_RUN`、3–5篇 Gold Set 与24h仍需做的事项。

本次验收结束时**不要提交到正式 `E:\Research_Knowledge_Base`**。如需正式写入，单独给我具体 plan、变更摘要与 SHA-256，等待我的明确同意。
