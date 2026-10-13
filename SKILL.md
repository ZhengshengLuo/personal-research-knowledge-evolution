---
name: personal-research-knowledge-evolution
description: PRKE 通用科研知识演化 Skill；用于科研领域认知探索、研究脉络建立、论文与方法/数据检索、证据来源筛选以及合法 PDF 获取与人工全文交接。Router 负责需求、规划、权限和跨模块调度；Acquire、Understand、Organize、Synthesize 四个路由均已接入业务协议；本地综合程序提供来源审计和草稿，实际科学检索及判断依赖授权宿主。普通翻译或文字润色不应触发本 Skill。
---

# PRKE v1.5.0-rc1 — 单一 Skill（Router + Acquire + Understand + Organize + Synthesize）

本 Skill **只有一个 SKILL.md**。先从用户研究需求和交付目标出发，再按需读取 `router/` 六份控制协议和 `router/interfaces/module-registry.json`；不能无目的地加载所有参考文件。

## Router

1. 根据用户当前科研目标判断任务是否足够清晰（`router/intake.md`）；不为收集常规背景机械询问。允许领域探索型任务先取证后提问。
2. 对研究空间采用自动匹配已有 Workspace、创建长期空间前询问（`router/workspace.md`）。不因为仅下载一篇论文就创建 Workspace。
3. Mission → Stage → Action 分层计划，自主执行安全的只读工作及任务暂存，重大范围、预算、权限变化时交用户确认（`router/planning.md`、`router/governance.md`）。
4. 根据交付物分派业务模块（`router/dispatch.md`）。Acquire、Understand、Organize 为 `INSTRUCTION_READY`，Synthesize 为 `INSTRUCTION_READY`，通过 `routes/synthesize.md` 对接科研 Agent 和证据草稿工具；本地 CLI 不自动开展外部文献检索，也不等于科研内容独立核验。
5. 长任务留 checkpoint，状态和真实证据以 `router/checkpoints.md` 和 `router/interfaces/module-contract.md` 为准。

## Acquire（获取知识）

读取 `routes/acquire.md`。区分 **探索型、深化型、定向型**用户需求，与 QUICK / FOCUSED / DEEP / SYSTEMATIC 检索强度分开判断。

- 陌生领域：先用可用学术检索工具做有界领域预探索，提供带实际来源的初步研究地图，再基于专业线索提出关键问题。
- 已明确的定向检索：直接针对问题查找相关方法、证据、数据、引用关系及最新工作，不先重复整个领域介绍。
- 动态设定合理时间范围，结合语义检索、关键词、种子论文、作者、前后向引文与反向证据；真实检索过程进 SearchLog。未调用成功不编造 DOI 或论文。
- 文献价值按相关性、原创贡献、证据和研究路线代表性评价；将元数据、摘要、取得 PDF、全文科学审查明确区分。研究覆盖评价不是“全领域已经找全”的证明。
- 需要 PDF 时读取 `references/acquire-pdf-policy.md` 和 `adapters/pdf-acquisition.md`。机构全文由用户人工下载到任务 `pdf/manual_inbox`；可执行本地身份匹配和合法自动 OA/官方 API 获取，但必须**显式执行**下载命令，不处理学校账户或上传受限 PDF 到外部 AI。
- 自适应输出研究脉络、经核验的候选文献、检索边界、覆盖矩阵与可交给 Understand 的已核验 PDF。无权访问或未完成任务返回 PARTIAL/BLOCKED，不伪报成功。

## Understand（理解知识）

读取 `routes/understand.md`；按需加载 `references/understand/`，不得全部机械加载。

- 用户科研目的决定本次阅读优先级，论文主要贡献决定默认科学评价框架。主类型 REVIEW / SCIENTIFIC / METHOD / DATA_RESOURCE，可辅次类型。
- 支持交互或静默，初读 / 定向 / 正式精读，以及多篇对比。静默 DEEP 仍须真正查看原文所有正文主图表及核心 Supplement，并开展批判性审查。
- 使用本地 `scripts/understand_cli.py` 做 PDF 文本提取、页面渲染、证据索引、确定性审计、Paper Note 草稿及比较骨架；**仅执行 prepare 不构成真正阅读，更不构成图像视觉核验**。原始图表必须由宿主实际查看。
- 单篇默认不延伸外部参考文献；多篇差异按需有界委托 Acquire。未覆盖论文不冒充领域共识。
- 交互 HTML 可选；快速静默入库生成草稿，用户已经选择任务级授权后自动入库方案，但Organize 已有本地草稿与受控提交 CLI；只有实际执行并核对 `commit_receipt.json` 的 `COMMITTED`，才可以声称已写入对应 Vault。

## Organize（知识组织与可追溯入库）

读取 `routes/organize.md`，需要时加载 `references/organize/` 和 `adapters/zotero-readonly.md`、`adapters/obsidian-local.md`。

- Zotero 第一阶段只读，使用 `organize_cli.py zotero-probe` 检验真实本地 API；不能从安装版本推断已经连通。
- 以规范化 DOI 或 PDF 版本 SHA 建立稳定论文身份；Zotero 未真实匹配保持 `ZOTERO_PENDING`。
- Obsidian 采用独立单 Vault、扁平 Papers/Readings，每篇 1–2 个主要 Markdown；DEEP 且 `audit COMPLETED` 才提供精读笔记。
- `stage-paper` 默认 Vault 外预览，真实提交必须经独立批次授权参数并再次验证目标文件和源证据，保留人工记录；本地文件权限隔离仍需 Windows 实测。
- Topic 十篇有效唯一 Paper UID 阈值通过 `scripts/trigger_cli.py` 持久记录，需经授权的任务执行者调度；Synthesize `scripts/synthesize_cli.py` 生成有来源的库外草稿；`scripts/knowledge_cli.py` 负责 Topic AI 区与 Gap Overview 的预览、审批提交和事件账本。Excel 只有按需的可选导出，真实原图精准裁剪与自动科研语义判断仍需独立验收。

## 接入状态与本地命令

- 检索/Undermind：若宿主提供真实工具，按 `adapters/undermind.md` 的签名及当前工具文档使用；本包不包含直接请求 Undermind 的 Python 客户端。
- 离线检查：`python scripts/router_cli.py doctor`、`python scripts/acquire_cli.py doctor`、`python scripts/acquire_pdf_cli.py doctor`、`python scripts/understand_cli.py doctor`、`python scripts/organize_cli.py doctor`、`python scripts/synthesize_cli.py doctor`、`python scripts/knowledge_cli.py doctor`、`python scripts/trigger_cli.py doctor`。
- PDF 预览/执行、人工交接：详见 `adapters/pdf-acquisition.md`。必须指定库外任务目录，使用真实且格式有效的 `CandidateSet`；演示数据不得作为论文事实。
- 本地程序绝不自动修改 Zotero；Obsidian 仅在单独提交命令及批准批次范围内可修改；所有在线权限和成功状态要依据运行日志与真实返回判断。

## Synthesize（科学综合、Gap Evolution）

读取 `routes/synthesize.md` 和 `references/synthesize/evidence-and-gap-gates.md`。

- 三层模式：TOPIC_INCREMENTAL、FOCUSED_SYNTHESIS、SYSTEMATIC_REVIEW；用户可选，不能默认宣称做了系统综述。
- 以已有可信知识为基础，面对领域共识、实质冲突和 Gap 创新性时按需有界委托 Acquire 实际检索并记录反证，遇到未获取原文或检索失败不得补造科学结论。
- `scripts/synthesize_cli.py stage` 读取经宿主科研 Agent 逐项核验的证据包，校验来源结构并生成 Evidence Matrix 和 `AI_SYNTHESIS_DRAFT`；代码本身不具有独立的学术语义理解，必须由宿主完成科学分析。
- `scripts/knowledge_cli.py stage/commit/recover` 持久化候选 Gap 演化与 Topic AI 专区，全库仅一个 `Research Gap Overview.md`；旧人工认可结论与原始批注不得被覆盖。
- `scripts/trigger_cli.py check/complete` 用可复核的有效唯一 Paper UID 进行十篇阈值判定，持久保存待执行任务。默认只有主动调用才运行，不自动安装 Windows Task Scheduler。
- Gap 证据/创新性/任务状态分别记录；对于实质 Gap 表述变化先成为 PENDING_HUMAN，不自动改写当前科学判断；正式 Idea 需可信用户同意后另行创建。
- 内部实验严格按 INTERNAL_EXPERIMENT 标识，用户未授权的私有研究资料不得对外转移。
