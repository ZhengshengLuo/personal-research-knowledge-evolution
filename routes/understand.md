# Understand — PRKE 科研理解与证据评估（v1.3.0）

本模块接受 Router 分派，**以用户阅读目的为首要轴、论文主要贡献为默认协议**；不替代 Acquire 的检索、不执行 Organize 的正式存储、不宣布 Synthesize 的领域共识。详细规范按需读取 `references/understand/`，不重复复制 Nature 项目全部代码或他人许可证内容。

## 路由与工作模式

- 阅读深度：SCAN/FOCUSED/DEEP；方式：INTERACTIVE/SILENT。独立选择；静默不降低证据标准。
- 主类型 REVIEW/SCIENTIFIC/METHOD/DATA_RESOURCE，可增次类型。类型特化阅读重点见 `paper-type-protocols.md`。
- 单篇精读无需默认外部引文扩展；多篇比较先对齐估计目标、数据、定义、尺度及实验设计，关键争议才有界委托 Acquire；对未精读论文明确标记为定向审查。
- 已经大致阅读的论文可以静默整理 Paper Note，保留实际阅读深度，不能自称 DEEP。

## 质量硬门槛

1. 在本地逐篇 PDF 准备 SourceBundle、实际渲染图表。正文主要 Figure/Table 在 DEEP 模式必须全检查，相关 Supplement 同样检查，图像必须实际查看，不可只读 Caption。见 `visual-evidence.md`。
2. 所有 DEEP 模式必须完成结构化批判性证据审查，按主类型核验。原文声明、作者解释、Agent 推断及假说分开。见 `critical-appraisal.md`。
3. 报告真实读到的范围；图像缺失、来源版本不匹配、重要结果未核验须 PARTIAL/BLOCKED，不能用文字解析成功代替视觉成功。
4. 本地 `scripts/understand_cli.py prepare` **只是渲染/提取**；Agent 必须实际通过可用的视觉工具查看所渲染图像，记录证据及图号，再以 `audit` 审查。审计脚本不能证明 Agent 眼睛读过图，必须保留宿主操作日志。

## 交付与授权

- `note` 生成库外 PaperNoteDraft；如审计 PARTIAL 必须显式 `--allow-partial` 才可出草稿，并显示不完整项。
- `html` 是可选轻量本地阅读视图；交互由宿主 Agent 对话完成，**不声称 HTML 内有 AI 聊天或划线回写**。
- `init-comparison` 只生成多篇比较骨架，跨研究可比性和证据差异由实际阅读 Agent 执行。
- `handoff` 仅生成未来 Organize 执行的 `PENDING_ORGANIZE` 材料：即便用户选择任务级授权 A，本版也没有正式 Vault 写入接口，**不得报告“已存入 Obsidian”**。

## 本地入口

`python scripts/understand_cli.py doctor`。其余命令见 README。PDF 所在地及产物仅在用户控制的库外任务目录，禁止未经授权的云端上传。
