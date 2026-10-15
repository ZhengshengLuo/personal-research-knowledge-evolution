# PRKE｜个人科研知识演化（完整 Skill 包）

**版本：1.7.0-research-first-preview**  
**性质：以真实科研为中心的集成升级包，仍非正式生产验收版本。**

PRKE 是一个可在受支持宿主 Agent 中加载的科研 Skill。它把科研问题的理解、文献与数据发现、原文精读、科学综合和长期知识积累组织在一起，使 AI 既能协助研究，也能明确自己的证据局限。

## 主要能力

- **Acquire**：找到真实的论文、方法、数据与可能的反证；记录检索覆盖和原文获取情况。
- **Understand**：读懂论文的假设、研究设计、统计结果、图表和局限；证据可回到原文。
- **Synthesize**：比较研究、解释分歧、检查竞争机制、提出或否定候选科学问题。
- **Organize**：把值得积累的科研认识与 Zotero 文献、Obsidian 知识、Claim/Evidence/Gap 历史联系起来。

**Router** 根据科研目标按需组合能力；**Scientific Reasoning / Critic** 提醒模型重视研究设计、尺度、估计量、反证和推断边界。任何结构脚本都不能自动证明科学真值。

## 安装（三步）

1. 将完整 `personal-research-knowledge-evolution/` 目录放进**当前宿主官方支持的 Skills 目录**，确认在宿主技能列表中可见；仅复制到任意工程目录不等于已经启用。
2. 在该目录执行 `python -m pip install -r requirements.txt`（Python 3.10+），运行 `python -m unittest discover -s tests -q`。也可单独检查 `python scripts/router_cli.py doctor` 等。
3. 在宿主的**新会话**中自然提出科研问题，或显式引用该 Skill 测试触发。使用外部检索、图像阅读和独立 Agent 前，务必确认宿主真的提供这些工具。

Windows 安装及正式科研资产保护请先阅读 `docs/INSTALL_WINDOWS.md`。

## 典型用法

> “请比较这些论文对干旱下 SIF–GPP 关系的结论，重点找出研究尺度不同导致的表面冲突。对无法核验的图表请说明缺口。”

> “我已有一批论文，先找出有争议的关键假设，提出可以证伪的研究方案；不要为了凑数制造 Research Gap。”

> “查看已有 Topic 的结论，在库外提出新证据触发的修订建议，保留旧版本，不修改正式知识库。”

**不需要先连接 Zotero、创建 Obsidian 才能开展科研问答、检索与阅读。** 如果需要长期保存，再连接现有 Zotero（原则上只读）、选择一个已有或新建的长期 Vault，先在测试 Vault 验证；正式 Vault 写入必须受可信授权保护。

## 核心文件

| 文件 | 用途 |
|---|---|
| `SKILL.md` | 科研协作入口，建议先读 |
| `routes/` | 四项科研能力的实际工作原则 |
| `references/scientific-core/` | 科学推理、反方审查、原文证据和知识演化 |
| `references/experts/` | 按需加载的任务、方法及学科专家协议 |
| `router/` | 需求理解、动态规划、模块选择、Workspace 与权限 |
| `scripts/` | 本地证据、任务、PDF、综合、知识暂存与恢复工具 |
| `docs/PRKE_FINAL_DESIGN_CONTRACT.md` | 研究者批准的原始设计（保留不变） |
| `docs/CAPABILITY_MATRIX.md` | 本次实际可声明的能力边界 |
| `docs/UPGRADE_1.7.0.md` | 本次升级内容、兼容性和待验收事项 |

## 现实边界

PRKE 的本地脚本可以校验结构、来源引用声明和文件完整性；**科研理解、图像查看、在线检索和独立审查依赖宿主真实执行**。`execution_core.py` 的回执仅证明有一个宿主报告，并不是真实外部平台的加密执行证明。普通 Agent 只靠同一身份与 CLI 确认标志，不能完成可信的无人值守生产入库。未部署 Worker 时不声称能持续后台运行。

**版本声明：** 1.7.0 修正并强化了若干可复现的本地行为，但没有凭提示词更新“实现”自主运行时、独立科研 Gold Set 或正式 Zotero/Obsidian 可信连接。详见能力矩阵与升级说明。
