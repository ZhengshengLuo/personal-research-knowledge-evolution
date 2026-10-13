# PRKE v1.5.0-rc1 · 可测试全功能集成候选版

**创建于**：2026-10-13。**状态**：候选版，不能宣称 Windows 真实科研环境/科学 Gold Set/24h 稳定性已通过。

## 真实继承与新增

- 基线为用户提供 `PRKE_v1.4.0_Router_Acquire_Understand_Organize_完整测试包.zip`，保留已有五个 CLI、现有 Acquire、Understand、Organize 的文件和数据格式、单一 `SKILL.md`、8份 Obsidian 模板与 A+B CSS。
- 新增 `synthesize_cli.py` + `synthesize_engine.py` + `schemas/synthesize/`：具有来源定位的主张输入、跨论文 Evidence Matrix、科学综合结论（宿主科研 Agent 明确提交）、分歧、Gap 候选与外部反证检索状态；`AI_SYNTHESIS_DRAFT` 不能升级为已证实共识。
- 新增 `evidence_bridge_cli.py`：读取此前真实 Understand 记录，**科学对齐字段保持未评价**，等待宿主进行独立分析；不会从 PDF 直接编造科学方向。
- 新增 `knowledge_cli.py`：Stage → explicit plan-SHA batch commit；Topic AI 区、全库唯一 Gap Overview、Merkmaid 概览、稳定 Gap ID、事件哈希链、重大修订待人审、人工裁决交接、正式 Idea 的独立授权创建；Method/Data/Topic 的证据追加候选；源和目标哈希冲突拦截及未完成提交恢复。
- 新增 `trigger_cli.py`：按 Topic×有效唯一 Paper UID 进行 10 篇阈值与持久 pending 状态；支持经外部核验的重大反证标记；不自动安装系统任务。
- 新增 `export_excel_cli.py`：**可选** `artifact_tool` 实现总表/Review/Analysis/Method/Data 五表按需导出，正式知识源依然是 Zotero/Obsidian，不进行双向同步，专项分类依已有 Index 字段；尚需在 Windows 检查可选依赖。
- 新增 `evidence_assets_cli.py`：受控 PDF 原图指定区域裁切及溯源侧文件，以及 Zotero 只读批注快照；不自动确认裁切是否完整、精选哪些批注仍需宿主核验。
- 新增 `soak_cli.py`：真实时钟连续运行的心跳验收工具，绝不以模拟 24 小时代替真实 24h；该工具本身不等于后台 Worker 的故障恢复通过。

## 工程能力与科学能力必须分开声明

| 能力 | 本地候选版已有 | 仍需独立现场验证或后续加强 |
|---|---|---|
| Router 四路由、旧 CLI、旧 Schema | 已实现并回归 | 真实宿主路由任务联调 |
| Acquire 获取/Understand 精读 | 原 v1.4 继承 | 用户环境真实 PDF、图表、科学抽查 |
| Zotero 只读 / Obsidian 写入 | 原 v1.4 继承 | Zotero Desktop、本机 Vault 访问及可信宿主审批 |
| Synthesize Evidence Matrix/草稿 | 本地确定性审计、Host Agent 科学综合协议 | **程序不提供自主语义综合模型，也不直接连接外部学术检索服务**；由宿主调用工具并证据复核 |
| Gap 演化 & Topic、Method、Data | 候选事件、可追溯历史、AI 管理区、受控提交 | Windows Obsidian 可视化、并发跨模块写锁、真实科学审查 |
| Research Idea | 用户申明授权的分批创建 / 账本关联 | 可信人的身份认证服务不由 CLI 实现 |
| Topic 10 篇阈值 | 持久去重阈值与 pending 队列 | 独立系统后台任务调度需要用户部署、重启/多主机高可用未完成 |
| 24h 工程测试 | 真实经过时间校验器 | 尚未运行任何真实 24h 窗口；需用户 Windows 环境现场运行 |
| 独立科学 Gold Set | 模板和审查协议 | **3–5 篇尚未由人类独立复核**，不能宣称通过 |
| Excel 五表 | 可选 exporter，隔离合成 fixture 实测 | Windows 可选依赖和实际用户的分类字段覆盖需复验 |

## 安全与权限

- P0 只读 / P1 staging 默认；正式提交仍需要用户审查具体 plan 并将 SHA-256 与确认开关传给可信宿主。
- CLI 的 `--acknowledge-*` **不是不可伪造的人工身份认证**。生产部署必须通过可信执行主体或操作系统 ACL 实现“Agent 只暂存，人才能授权写入”的真实权限分离。
- 不修改原 v1.4 ZIP、真实 Zotero SQLite、用户正式 Vault，不发送受版权保护 PDF 或未公开实验数据到外部。
- Gap 演化日志哈希链能检测普通未经协调篡改，但不能抵御拥有所有文件写权限的恶意执行者；这种场景应交给 OS 访问控制和外部备份。
- 不得以一个 Schema PASS、自评审计或合成测试替代科学真值。

## 发布判据

**本 ZIP 的发布状态是 CANDIDATE / OFFLINE_TESTED**。正式 `PASS` 需要 G5 Windows 原文、3–5 篇独立 Gold Set 和 G6 24h 实际运行与故障恢复审核。未执行的关卡标 `NOT_RUN`，不得偷换为成功。
