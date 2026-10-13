# PRKE vNext — 个人科研知识演化 Skill 统一设计冻结合同

> **状态**：DESIGN_FROZEN（设计规格已归并，**并非软件已实现/上线**）  
> **日期**：2026-10-13  
> **现有可执行基线**：PRKE v1.3.0（Router + Acquire + Understand）  
> **下一工程目标**：v1.4.0（Organize 首版；Synthesize 保留接口，后续实现）  
> **项目目标**：以“科学问题—原始证据—个人理解—综合认识—研究决策”为主线，建立可追溯、可维护、可持续演化的个人科研知识系统。  
> **注意**：本合同用于后续 Codex 实施；没有运行你 Windows 主机上的 Zotero、创建 Vault 或启动后台任务。

## 1. 总体定位与不可变原则

PRKE 是**一个 Codex Skill**，以单个 `SKILL.md` 为入口，由 Router 选择性调用四个业务模块：Acquire、Understand、Organize、Synthesize。用户通过自然语言或聊天发出任务，Skill 不因功能增加而拆成四个独立的总入口。

- **科学问题驱动**：用户可提出 Idea，AI 可以依据文献证据主动提议，但研究方向、关键科学结论和正式 Research Idea 由研究者裁决。
- **协同运行**：兼容交互与静默；按需执行，授权后可在 Windows 本地后台持续检查任务和断点恢复。没有实际调度器时不得宣称后台任务存在。
- **证据追溯**：直接原文、作者解释、Agent 推断、研究者判断和跨论文综合必须分层记录；不能把模型生成的观点变成原文事实。
- **知识长期可用**：以 Markdown 原生笔记为中心；HTML/CSS 只影响可视化与可选教学阅读，不将核心知识封装为不可检索的网页。
- **单一身份、多重关联**：一篇论文只保留一个内部稳定 `paper_uid`，可关联多个 Workspace/Topic；正式知识库每篇最多两份主 Markdown（Paper Note 与精读笔记）。
- **渐进式自动化**：只读和隔离草稿可自主执行；正式库写入实行一次任务/批次范围授权；覆盖人工判断、破坏性修改、机构全文外传须另行批准。
- **版本可检查**：每一步“设计合同 → 唯一实现 → 实际验收记录”；旧版本归档，不在同一功能上维持互相冲突的执行路径。

### 1.1 四模块的责任边界

| 模块 | 最终负责 | 明确不负责 |
|---|---|---|
| Router | 任务理解、Workspace 选择、模块调用、计划/预算/授权、状态与恢复 | 凭空替代专业科学审查 |
| Acquire | 真实检索、来源交叉核验、筛选与覆盖、合法 PDF 获取 | 将题录核验当全文科学审查；无授权自动写入 Zotero |
| Understand | 按贡献类型精读、原图与公式核验、科学论证重建、批判性评价及选定论文比较 | 未读全文冒充精读；在单篇阅读中无界追文献；绕过 Organize 写 Vault |
| Organize | 身份去重、Zotero/Obsidian 连接、模板、笔记、知识关联、更新与事务、阈值调度 | 自动批准科学共识；直接代替 Synthesize 作广域综合 |
| Synthesize | 基于可比证据综合认识、解释分歧、检验 Research Gap、提出可检验问题和方案 | 以个人库内未发现文献证明“无人研究”；未经确认升级个人科学判断 |

### 1.2 当前发布真实性（不能混淆）

| 模块 | 2026-10-13 现有真实基线 | 下一目标 |
|---|---|---|
| Router | v1.3.0 的入口、治理、指令路由和模块注册存在 | 保持兼容，增加 Organize 及事件调度 |
| Acquire | 实际五篇题录交叉核验 PASS；三篇自动下载中一篇 VERIFIED、两篇 NEEDS_MANUAL_REVIEW | 修 Windows UTF-8；优化 DOI→合法 PDF 来源筛选和失败记录 |
| Understand | v1.3.0 离线测试 76/76；一次真实论文精读获得 `COMPLETED` 和图表审查记录 | 增加正式独立 Deep Reading Note 交接；继续开展科学真实性抽查及反向测试 |
| Organize | v1.3.0 注册表 `NOT_CONNECTED` | 首个待实施模块，Zotero 只读、本地 Vault 授权写入 |
| Synthesize | v1.3.0 注册表 `NOT_CONNECTED` | 冻结合成接口与阈值事件；科学综合执行器单独实现 |

**重要**：图表检查记录完备、Schema 审计通过不等于科学内容已被第三方独立验证；Zotero/Obsidian 本地安装不等于 API 已真实连通。

## 2. 固定运行环境与路径

- Codex、Zotero Desktop、Obsidian 均以**同一台 Windows 主机**为主要使用场景。
- Codex 开发和任务：`E:\Codex_workspace\...`（具体 PRKE Skill 安装位置由本机发现，不在规范内硬编码）。
- 长期 Obsidian Vault：**`E:\Research_Knowledge_Base`**；与 Codex 工作区分离。
- PDF 的权威管理位置：**Zotero**；无 Zotero 条目的已核验重要论文允许先生成 Obsidian Paper Note，标记 `ZOTERO_PENDING`，以后匹配。
- Excel 仅作从规范数据生成的**总表 + 四类论文专项表**导出视图，不维护平行主库。
- Zotero 实测预检：程序报告 **9.0.6**、未运行、本地 `23119` 未监听、样本 **0 篇**；重新启动并启用本地 API 后需复测，不能把“文档说明支持”当实测已连通。
- Obsidian 实测预检：**1.12.7**，拟定 Vault 当时尚不存在；用户已经同意**未来实施时**创建空白 Vault，不导入旧演示 ZIP，当前并未实际创建。
- Zotero 第一阶段**只读**；不改条目、Collection、附件和批注，不直接写 `zotero.sqlite`。不接入远程网络写端口。

## 3. 统一数据对象与状态模型

### 3.1 业务对象

1. `ResearchTask`：一次检索、阅读、对比、入库或增量综合的任务合同。
2. `Workspace`：具体科研项目的长期语义入口，不要求文件夹内复制全部论文。
3. `Paper`：论文身份、版本、DOI、Zotero 条目、原始 PDF 与核验来源。
4. `Reading`：实际阅读范围、深度、图表审查及批判性判断。
5. `Claim/Evidence`：原文科学主张、证据来源、可比条件、支持/反驳关系及审查状态。
6. `KnowledgeAsset`：PaperNote、DeepReading、Topic、Method、Data、Idea 等笔记内容及版本。
7. `Relation`：证据支撑的知识关系与其审核状态。
8. `SynthesisRun`：某 Topic 的某期综合所使用的证据快照、结论、变更建议和人工裁决。

### 3.2 不得互相冒充的状态维度

| 维度 | 最小值域/字段示例 |
|---|---|
| 原文访问 | `METADATA_ONLY` / `ABSTRACT_ACCESSED` / `FULLTEXT_ACCESSED` / `SOURCE_PARTIAL` |
| 阅读深度 | `SCAN` / `FOCUSED` / `DEEP`，真实执行记账 |
| 图表核验 | `VISUALLY_CHECKED` / `TEXT_ONLY` / `UNREADABLE` / `NOT_AVAILABLE` |
| 科学主张来源 | `AUTHOR_OBSERVATION` / `AUTHOR_INTERPRETATION` / `AGENT_ANALYSIS` / `EXTERNAL_EVIDENCE` / `HYPOTHESIS` / `USER_JUDGMENT` |
| 审计任务状态 | `COMPLETED` / `PARTIAL` / `BLOCKED` |
| 知识库状态 | `DRAFT` / `PENDING_APPROVAL` / `COMMITTED` / `CONFLICT` / `NEEDS_RECOVERY` |
| 综合状态 | `EVIDENCE_ACCUMULATING` / `SYNTHESIS_QUEUED` / `AI_SYNTHESIS_DRAFT` / `RESEARCHER_CONFIRMED` |

**不允许**：PDF 已下载 → 已读懂；笔记已入库 → 科学已验证；10 篇论文 → 领域共识；`audit COMPLETED` → 实验复现成功。

### 3.3 论文身份

`paper_uid` 是 PRKE 稳定内部主键；规范化 DOI 是高优先级匹配依据，Zotero `library type + library ID + item key` 是已存在条目的外部主映射；标题、作者、年份仅用于辅助判断。预印本、正式版、撤稿/勘误和同 DOI 不同稿件须保留版本关系，歧义时不得静默合并。论文文件名只用于人类阅读，不当唯一数据库键。

## 4. Router：运行治理与用户交互合同

- 从**用户当前科研目标**而非模块名出发识别意图，允许用户自然语言直接说“精读后入库”“给我比较这个方法”“积累到十篇自动总结”。
- `Mission → Stage → Action` 分层；对只读或已授权任务自主推进，必要时说明计划/质量标准/预算。
- P0/P1：已授权的只读和 Vault 外暂存；P2：明确 Vault、路径、批次、操作与内容指纹的一次范围授权；P3：危险覆盖、删除、大范围迁移、私有全文外传须单独批准。
- 用户已选择 **任务级授权方案 A**：一次批准某批次后，合规且无冲突的新增/增量可自动提交，不用逐篇弹窗；遇到歧义、人工内容变更和目标文件冲突暂停该项。
- 可信批准须由宿主独立交互或受保护提交者记录，不能靠 Agent 自填 `approved: true`。实际保护还需 Windows 文件权限/独立提交程序，而不仅是 Prompt 提醒。
- 断点、日志、任务状态、重试幂等和错误边界必须清晰；模块不可用时回报 `NOT_CONNECTED`/`PARTIAL`，不假执行。

## 5. Acquire：维持 v1.2.0 科研逻辑，修复实际验收问题

### 5.1 固定科研功能

- 探索型（EXPLORATORY）/深化型（DEEPENING）/定向型（TARGETED）需求与检索强度 QUICK / FOCUSED / DEEP / SYSTEMATIC 双轴分离。
- 检索：Undermind（宿主可用时）、OpenAlex、Crossref、官方来源、引文链等，以真实调用结果和 `SearchLog` 为准。
- 题录、摘要、全文可得和科学内容审查分别标记，区分 DML/CATE 处理效应估计、因果发现、预测解释和相关邻近方法。
- `CandidateSet`、`SearchPlan`、`SearchLog`、`CoverageMatrix`、PDF 状态报告为规范交付；检索覆盖仅能在约定研究范围内表述。
- 开放 PDF 走白名单、授权来源、官方 API、合法 OA；机构限制 PDF 继续使用用户人工获取到 `manual_inbox`，PRKE 本地身份核验复制到 `verified`，不上传第三方云服务。

### 5.2 从真实报告确定的修复清单

- **P0**：两处 Windows 默认 GBK 模式下的 `read_text()` 显式 `encoding='utf-8'`，真实 Windows 环境回归；`PYTHONUTF8=1` 只是过渡执行条件。
- **P1**：逐源审查 IOP 官方域名与机构仓库合法性，完善受控来源发现与安全下载，记录 URL 被过滤的原因；**禁止无限制放开域名白名单**。
- **P1**：Springer API 先判断 DOI 出版商归属；`HTTP 401` 与配置是否存在、权限是否有效分开报告。
- **P2**：UNPAYWALL_EMAIL 缺失只报告配置缺项，用户配置后再单独验收；不索取密钥原文。
- **P2**：由 Agent 发现的候选 PDF 来源可在受控 Schema 中记录 URL、来源类型、许可与验证状态，但不能任意链接直通下载器。
- `exit 0` 表示工具运行/报告生成，不等于所有 PDF VERIFIED；按逐项下载状态验收。

## 6. Understand：完整科研精读合同

### 6.1 三个独立阅读维度

1. **阅读深度**：`SCAN` 快速初读、`FOCUSED` 定向核查、`DEEP` 正式精读。
2. **论文主贡献类型**：REVIEW / SCIENTIFIC / METHOD / DATA_RESOURCE，允许次类型。
3. **交互方式**：INTERACTIVE（互动学习，可选 HTML）/ SILENT（自主精读、批量整理），静默不降低 DEEP 核验要求。

用户科研目标决定重点，论文主贡献决定默认审查协议。多篇时少量关键论文逐篇精读；大量论文先围绕共同问题交叉取证，未完整精读必须单独标注。

### 6.2 四种论文类型的核心协议

| 类型 | 研究逻辑 | 重点批判检查 | 精读成果 |
|---|---|---|---|
| 综述 REVIEW | 范围、分类、路线、代表原始研究、共识/争议、知识空白 | 选择性引用、分类合理性、二手证据外推 | DomainMap |
| 科学分析 SCIENTIFIC | 假设、数据设计、直接结果、机制、结论 | 混杂/中介、因果识别、尺度、统计不确定性、替代解释 | ScientificEvidence |
| 技术方法 METHOD | 瓶颈、算法设计、公式与模块、Baseline/消融、泛化 | 泄漏、对照公平性、复现条件、稳健性 | MethodBlueprint |
| 数据资源 DATA_RESOURCE | 来源、生成处理、变量、覆盖、验证、使用 | 独立真值、误差传播、代表性、版本与适用范围 | ResourceProfile |

### 6.3 两个不可跳过的 DEEP Gate

- **Visual Evidence Gate**：全部正文主 Figure/Table 须实际查看原始图像或页面渲染；重点子图放大；支撑核心结论的 Supplement 必须核验。单独读取文字、图注或 OCR 绝不等于图像核验。不可读记 `UNREADABLE` / 缺失记 `NOT_AVAILABLE`，相关成果为 `PARTIAL`。
- **Critical Evidence Gate**：核心主张关联 PDF **物理页码**、原文图号/子图/公式、必要限定条件和统计量；区分作者数据结果、作者解释与 Agent 分析。适配论文类型审查，不生成无依据的统一评分。
- 单篇默认不追逐所有引文；多篇科学结论有关键差异时，先检查可比性，再有限度调用 Acquire 核验原始研究。
- `prepare` 只是 PDF 解析与渲染；`audit COMPLETED` 表示记录满足确定性关卡，不能单凭该结果证明真实视觉理解质量。应保留实际访问/工具记录供抽查。

### 6.4 Understand → Organize 新版交付（在 v1.3.0 基础上增量）

- `PaperNoteDraft`：简洁的研究知识入口；快速阅读、明确要求入库或重要论文可产生，但标注阅读深度。
- **`DeepReadingDraft`（下一版新增规范成果）**：每篇完成正式精读的论文，单独生成完整科研精读笔记；重建研究逻辑、方法与公式、重要原图、结论、批判性评价和个人科研关联；不是把 `FigureInventory` 机械复制进正文。
- `ReadingRecord`、`SourceBundle`、`ClaimEvidenceMatrix`、`FigureInventory`、`ReadingAudit`：结构化证据与状态，交 Organize 长期归档，**不产生第三份主阅读 Markdown**。
- 关键图像 `FigureAssetManifest`（目标新版交接契约）：图像提取位置、所属 paper_uid、原 Figure/子图、PDF 哈希、版权/本地引用限定。
- 已存在初步阅读结果时可以静默快速入库，未通过 DEEP Gate 的记录不得伪称正式精读。后续重新精读应更新同一篇正式 Reading Note，保留历史及用户文字。

## 7. Organize：连接、知识对象与权限

### 7.1 数据系统分工（已经确认）

| 系统 | 规范角色 | 初期写入权限 |
|---|---|---|
| Zotero Desktop | 所有论文的正式书目、PDF、引用与全部原始高亮批注 | **只读**；不能自动改条目或库数据库 |
| Obsidian Vault | 重要科研知识的长期 Markdown 表达；项目、主题、方法、数据和个人思考 | **明确任务/批次授权后受控写入** |
| PRKE evidence & index | 稳定 UID、来源与图表哈希、Claim–Evidence、关系、版本、审计与事务 | 受控内部写入，长期可备份和重建 |
| Excel | 从规范记录导出的 Master + Review/Analysis/Method/Data 横向比较视图 | 仅按需导出，不形成平行主库 |

- Zotero 重要批注由 Agent **选择性提取**，用户原文原样保留，注明笔注来源和定位；全部批注继续在 Zotero。
- 未存在 Zotero 条目的重要论文可以在授权后先进入 Obsidian，标记 `ZOTERO_PENDING`，以后 DOI/版本核对后补齐映射；禁止生成虚假 Zotero 链接。
- 授权 Workspace 路径下的项目代码/合同/日志可以只读提炼**阶段性科研经验**；原始代码、数据和完整运行日志不复制到 Vault，也不擅自修改。

### 7.2 最终 Vault 目录（无数字前缀；按知识对象扁平化）

```text
E:\Research_Knowledge_Base\
├── Home.md
├── Workspaces\
│   ├── CHFD-SIF保真度研究.md
│   └── 干旱热浪植被响应综述.md
├── Topics\
│   ├── 领域知识\
│   │   └── 干旱与植被响应.md
│   └── 科学问题\
│       └── 连续SIF产品的极端响应保真度.md
├── Papers\
│   └── Krich 2021 - Functional convergence.md
├── Readings\
│   └── Krich 2021 - Functional convergence - 精读.md
├── Methods\
│   └── PCMCI因果发现.md
├── Data\
│   └── TROPOMI SIF.md
├── Ideas\
│   └── <仅有研究者确认的Idea笔记>.md
├── Assets\
│   └── Figures\
│       └── <paper_uid>__Fig04.png
├── Templates\
│   └── <PRKE内置模板的Vault侧副本>.md
├── .obsidian\
└── .prke\
    └── <系统索引、映射与审计状态>
```

**说明**：目录中举例的学术对象是使用效果演示，**初始化时不凭空创建这些论文/研究成果**。`Assets/Figures` 是全 Vault 的共享附件目录，文件名带 stable UID 避免碰撞；没有“每篇论文一个文件夹”，不强制复制原始 PDF。任务级缓存仍在 Vault 外；长期证据索引可以有 Vault 内 `.prke` 侧文件及 Vault 外的独立可恢复备份，不能依赖会清理的临时目录。

### 7.3 两份论文笔记：不再产生 Evidence.md

**Paper Note**：可在几分钟内由研究者或 AI 读取。含论文身份与 Zotero 链接、实际阅读状态、一句话贡献、科学问题、2–5 条核心发现、关键证据/边界、科研价值、关联 Topic/Method/Data/Workspace、完整精读笔记链接。普通不重要的 Zotero 论文**不自动入 Obsidian**。

**Deep Reading Note**：仅正式精读后形成。详细学术内容随四种论文类型动态生成：问题/机制/方法/数学公式、各主要 Figure 的实际分析、数据和设计、结果及不确定性、批判性评价、精选 Zotero 批注和用户独立思考。重要原图嵌入正文相应章节，其他图表仍有来源索引；不设死板字数上限。

**Evidence Archive**：作为 PRKE 内部结构化证据资产（JSON/可重建索引及其版本），而不是第三份展示型 Markdown；两个主笔记以 Claim ID 和来源定位引用。已有 v1.3.0 原始记录可以迁移，需保存原始哈希和读取状态。

### 7.4 其他长期笔记模板

| 模板 | 固定核心 | 自动更新边界 |
|---|---|---|
| Domain Topic | 研究领域边界、科学知识分类、代表证据、阶段性认识、分歧/不足、研究路线 | 原始证据增补自动；新重要主题及综合判断升级经确认 |
| Question Topic | 明确科学问题、估计对象/尺度、竞争假说、可比证据、分歧与设计缺口 | 同上；不因某个结果不同自动判定争议 |
| Method Note | 算法原理、公式、关键假设、变体/版本、验证、适用边界、来源论文及个人实践摘要 | 已有方法自动增补证据；重大新节点需确认 |
| Data Note | 数据产品来源、变量、版本、时空尺度、质量/误差、独立验证、适用条件及实践摘要 | 已有数据节点自动增补；重大新节点需确认 |
| Workspace | 项目目标、当前科学问题、关联 Topic/Paper/Method/Data、阶段决策、实验摘要及原件路径 | 仅可读授权项目路径；关键研究决策不可静默更改 |
| Idea Note | 起源证据、Candidate Gap、反证检索、科学问题、可检验假设、实验路线与风险 | **Agent 的新 Idea 先留 Vault 外暂存；正式建档须研究者确认** |

默认以**完整科研笔记**为知识颗粒度，不为每项科学主张自动建单独 Markdown；原子主张留在结构化索引。Method/Data 主笔记容纳一般变体，存在实质性原理/版本差异时建议拆分，需确认。长期项目实践详细原件仍在项目目录。

### 7.5 证据积累与知识判断严格分区

已有 Topic/Method/Data 可在任务授权范围内自动增加**带来源、限定条件、阅读状态的研究发现**；原有确认性认识、用户亲手写的判断和批注不可被新论文覆盖。发现潜在冲突时先标明：`CONDITIONS_DIFFER`、`POTENTIAL_CONFLICT` 或 `INSUFFICIENT_EVIDENCE`；科学权衡交 Synthesize，重要修订再由研究者确认。

### 7.6 真实身份映射与 Obsidian 图谱

- Paper→Reading 是一对零或一；一篇 Paper 可以关联多个 Topic/Workspace，文件不复制。
- 类型化关系：`RELEVANT_TO`、`USES_METHOD`、`USES_DATA`、`SUPPORTS`、`CHALLENGES`、`INSPIRES`、`BELONGS_TO_WORKSPACE` 等。每条重要关系保存 paper_uid、Claim/证据来源、条件和 `SUGGESTED/CONFIRMED/DISPUTED` 状态。
- Obsidian 原生 **Graph View** 显示 `[[WikiLinks]]` 构成的连接，默认不显示不同关系类型的标签或强度；PRKE 在 YAML/关系索引中保留语义。用户主要使用 Workspace、Topic、Paper 的**局部关系图**，不追求生成全库毛线球。
- 从 Papers 到 Readings、Topics、Methods、Data、Workspace 使用原生双链；页面排版不应该依赖外部 HTML 才能阅读。

### 7.7 笔记主题视觉风格（A+B 冻结）

- **A Academic Editorial**：Paper Note、Deep Reading Note 采用暖白/低饱和森林绿、可长期阅读的学术正文层级、克制的证据标注与图文。
- **B Research Studio**：Topic 和 Workspace 使用统一视觉语言下更清晰的模块化科研信息面板、指标与证据区。
- 仍采用原生 `Markdown + YAML Properties + [[WikiLinks]] + Callouts + CSS snippets`；CSS 作为可选外观增强，不把内容生成 HTML 表格脚本。Obsidian 原生链接可搜索可维护；图谱基于真链接。
- 视觉与内容分离：一套语义模板可在浅色/深色 Obsidian 主题中保证内容可读；预览中的进度数据、图示不是实际运行结果。

## 8. Topic 自动增量综合与科学演化

### 8.1 分层更新（已经确认）

1. **即时层**：每篇有充分相关性与可追溯证据的论文入库后，Organize 即时更新现有 Topic 的证据索引与关系；不重新撰写全篇领域总结。
2. **知识综合层**：每个 Topic 自上次成功综合的**证据快照**之后累计新增默认 **10 篇去重后、具有有效相关证据的论文**，自动生成 `SynthesisRequested`，交 Synthesize 对现有全部证据及新增部分实施完整阶段性综合。
3. **落库层**：Synthesize 输出版本化 `AI_SYNTHESIS_DRAFT`，Organize 自动写入 Topic 的**候选综合区**并保留旧版；实质性共识变更、研究者结论升级和正式 Research Idea 仍需研究者确认。

- 计数按 Topic 独立，重复入库/再次阅读相同论文不重复计；新版本证据或新检测到的支持质量变化可标记另行复核，但不冒充新增论文篇数。
- **不是做论文多数投票**：需要对研究对象、指标、干预/暴露定义、尺度、方法、独立性和证据强度建立可比性对照。
- 用户主动请求、重要潜在冲突或项目/写作需要时可以提前触发。
- 若 Synthesize 仍 `NOT_CONNECTED`，**只排队或发出待处理事件，不伪造综合结果、不假更新科学结论**。

### 8.2 混合自动运行（已经确认）

- PRKE 活跃时，论文符合入库条件即可检查阈值并加入综合队列。
- 在用户授权且 Windows 调度器/常驻执行端实际可用时，后台周期性查找待处理 Topic 和失败重试；具体检查频率为**部署配置项**，不能由本规格凭空宣布定时任务已存在。
- 任务应具有 topic_uid、证据快照哈希、上次成功 checkpoint、幂等键、状态、开始与完成时间、失败原因。
- 机器关机/服务不可用时任务留待恢复，不能将队列状态报为执行完成。

## 9. 知识库安全提交：从草稿到正式笔记

**建议流程**：`Inventory → Identity → Normalize → Draft → Relation → Stage → Preview/Approve → Commit → Reindex`。

- 用户给定 Vault、路径范围、论文/笔记批次、允许的新增或增量操作后，独立权限的 Committer 在批准范围内自动提交无冲突内容。
- 验证目标文件预像哈希、待写内容哈希、`batch_id/fingerprint`、Windows 路径与链接是否越界、Zotero 只读约束、阅读状态合法性。
- 区分 `AI_MANAGED` 和 `USER_AUTHORED` 区域；人工批注和用户判断原样保留。人工改动已受管理区段后应报告 diff 并重新批准，不能默默覆盖。
- 提交前备份、写前日志、原子替换、提交后核对；多文件批次中断需 `NEEDS_RECOVERY` 并可恢复。重试同一批次必须幂等。
- 一次审批不自动授权永久修改 Vault；安全性不能只依赖生成一份 `approved: true` JSON。

## 10. 最小模板字段与表现示例（设计，不代表已安装）

### 10.1 Paper Note 的 YAML 最小契约

```yaml
---
prke_id: paper:krich2021-functional-convergence
asset_type: paper_note
paper_uid: krich2021-functional-convergence
title: Functional convergence of biosphere–atmosphere interactions in response to meteorological conditions
doi: 10.5194/bg-18-2379-2021
zotero_library_type: null
zotero_library_id: null
zotero_item_key: null
zotero_status: ZOTERO_PENDING
primary_type: SCIENTIFIC
reading_depth: DEEP
reading_audit: COMPLETED
knowledge_status: DRAFT
source_sha256: d9963901af92c96e9a4a84893e81057a8e16fd306c0acae0a2a3c6dd1e5cfaf9
workspaces: []
topics: []
methods: []
data_resources: []
related_reading: "[[Krich 2021 - Functional convergence - 精读]]"
---
```

上述 Zotero/Workspace 关联字段为空是因为当前未完成实际数据库匹配，不能凭示例制造归属。

**Paper Note 正文的固定范围**：一句话认识；科学问题与贡献；关键发现（2–5）；可靠证据和边界；我的科研价值；精选人工批注/疑问；关联论文精读、Topic、Method、Data、Workspace。以简洁、可高频阅读为原则。

### 10.2 Deep Reading Note

相同 `paper_uid`，`asset_type: deep_reading`，必须反映实际 `DEEP` 和核验结果。正文根据四类论文动态展开研究背景/问题、假设、数据与设计、技术路线与公式、图表与结果、机制讨论、批判性审查、论文贡献、个人研究应用、读书问题；重要原始 Figure 的本地图像在对应章节嵌入并标 PDF 物理页、Figure/Panel 和来源哈希；保留人工作者区，不机械复制机器 JSON。

### 10.3 Topic Note

区分 `topic_kind: DOMAIN` / `QUESTION`；最小包含主题边界、重点科学问题、分类/研究路线、累计证据、**已确认认识**、**AI_SYNTHESIS_DRAFT 候选综合**、可比条件与争议、未解决证据缺口、关联方法/数据、历史综合版本和计数 checkpoint。

### 10.4 Method / Data / Workspace / Idea

- Method：定义、假设、核心公式与步骤、版本/变体、与对照方法差别、证据、可用边界、实际项目摘要与原件引用。
- Data：生产机构/来源、原始观测与派生性质、分辨率/时空、波段/变量/单位、质量筛选/不确定性、版本、独立验证、适用边界、实践经验与原件。
- Workspace：科学目标、当前研究问题、相关 Topic、关键论文、方法、数据、决策、阶段成果与需要核验事项；与项目文件建立只读引用，不搬运大文件。
- Idea：研究动机、原始来源、竞争解释、候选 Gap、主动反证检索、假设与预期结果、可实施性、研究者裁决；未经确认只能留在 Vault 外候选区。

## 11. 端到端任务路径

1. **找文献**：“查找极端干热植被响应的因果方法研究” → Router→Acquire→经过题录核验的候选与合法 PDF 状态；只报告真实获取数量。
2. **认真读**：“静默精读这篇 PCMCI 论文” → Understand 真实原图与论文类型专属审查 → Paper Note 草稿 + Deep Reading 草稿 + 证据资产。
3. **快速入库**：“这篇之前看过，整理进 Obsidian” → 复用实际已存在的阅读成果，按状态生成 Paper Note → Organize 去重、授权后正式提交；未 DEEP 不产生虚假的精读笔记。
4. **边读边学习**：“我今天想交互理解这篇” → Understand 交互式问答，可选 HTML 查看；完成后按已有阅读状态更新相关笔记。
5. **知识自动积累**：“再读十篇相关论文” → 每次入库即时更新 Topic 证据；达阈值发出 Synthesize 事件 → 生成新一期综合草稿 → 保留研究者确认结论。
6. **科学问题孵化**：“这个领域现有结论为什么不一致？” → Understand 的指定文献比较 + Synthesize 更广证据协调、必要时 Acquire 反证检索 → 候选 Idea 暂存 → 研究者确认后 Organize 正式创建 Idea Note。
7. **项目实践经验**：“将 CHFD 代码和运行报告的关键经验记下来” → 仅在已批准项目路径中只读提炼 → Workspace 阶段实践摘要 + Method/Data 关联；不复制数据日志、不自动改变科研代码。

## 12. 统一接口、目录和最小工程结构（目标）

**现有 Skill 根目录和 CLI 不重命名，不将路由重写为多个 Skill：**

```text
personal-research-knowledge-evolution/
├── SKILL.md                        # 单一总入口
├── router/                         # intake/planning/dispatch/governance/workspace/checkpoints
│   └── interfaces/module-registry.json
├── routes/
│   ├── acquire.md
│   ├── understand.md
│   ├── organize.md                  # vNext 新增
│   └── synthesize.md                # 暂为接口与协议，未实现不得标 CONNECTED
├── references/
│   ├── understand/
│   ├── organize/                    # 笔记规范、Zotero/Obsidian 连接及安全提交
│   └── synthesize/                  # 综合和反证规则（实现后启用）
├── adapters/
│   ├── pdf-acquisition.md
│   ├── zotero-readonly.md           # 新增
│   └── obsidian-local.md            # 新增
├── templates/
│   └── obsidian/                    # 规范的 Paper/Reading/Topic/Method/Data/Idea/Workspace 模板
├── schemas/
│   ├── router/
│   ├── acquire/
│   ├── understand/
│   └── organize/                    # 新增 identity/relation/note/batch/synthesis-event
├── scripts/
│   ├── router_cli.py
│   ├── acquire_cli.py
│   ├── acquire_pdf_cli.py
│   ├── understand_cli.py
│   └── organize_cli.py              # 目标接口，尚不存在
├── tests/
└── docs/
```

新增模块遵循**合同 → 数据 Schema → 实现代码 → 原始测试收据**，由 Router Registry 真实记录状态：协议存在不等于后端已连通。模板文件的形式与渲染样式分离；`Templates/` 复制部署到 Vault 时应记录版本，更新旧模板不得无差别改写既有个人笔记。

## 13. 开发与验收顺序（按事实逐步放行）

### M0 — 现有工程和环境补齐

- 基于 v1.3.0 的 69 个文件作为**唯一现有软件基线**，保留当前测试与脚本签名；修 Acquire 两项 UTF-8 失败及 PDF 来源诊断，完成 Understand 反向审计。
- 启动 Zotero 9.0.6，确认本机 API，在真实条目读取最多三篇题录、附件、批注且零写入；核验 API/代理/库类型。
- 经用户既有授权**在实施阶段**初始化 `E:\Research_Knowledge_Base` 空白 Vault，再验证文件权限与 Markdown 显示；当前这一步尚未执行。

### M1 — Organize 数据结构和只读联通

- 在 Vault 外创建身份证据映射、候选笔记、关系记录、差异预览；建立 `paper_uid` 与 Zotero Item Key 的真实对应。
- 用真实 Krich 2021 论文生成 Paper Note + Deep Reading Note 草稿；用已审核图像生成本地受限图像资产并保证原图准确定位。
- 生成五表 Excel 导出，验证内容源自规范资产，不成为第二条主数据线。

### M2 — Obsidian 写入与更新

- 仅在**隔离 Vault** 检验提交者、批次授权、备份、更新时人工内容保护、路径越界、重复入库、回滚与中断恢复。
- 通过后才向正式 Vault 开放范围受限的 P2 新建/补充写入；Zotero 仍只读。
- 引入双链建议与统一图谱关系索引，保证一篇论文跨 Workspace 仍只有一份主笔记。

### M3 — Topic/Method/Data 增量演化

- 实现对已有 Topic/Method/Data 的可追溯证据增补、冲突标注、版本及重要节点新建审批。
- 落地每 Topic 的 10 篇阈值计数、幂等消息、checkpoint、待综合队列。

### M4 — Synthesize 与后台联合验收

- 完成综合协议和科学反证检查实际执行器，验证一轮真实多论文科学综合，候选结论默认 `AI_SYNTHESIS_DRAFT`。
- 授权后在 Windows 后台调度器配置周期检查和恢复；测试主机停机、失败重试、重复触发、Synthesize 未连接时等待等行为。
- 真实 Vault 经全量备份和试点验收，再决定是否扩大自动写入范围。

## 14. 最终验收清单

| ID | 必须通过的真实测试 |
|---|---|
| R-01 | 一个入口正确区分四模块；`NOT_CONNECTED` 不被误报为成功 |
| R-02 | 普通任务不要求重复授权，正式写入要限定批次，危险操作单独审批 |
| A-01 | 真实题录核验不混淆因果估计/因果发现/解释模型 |
| A-02 | Windows GBK 默认环境测试不因 UTF-8 漏标异常；下载逐项状态真实 |
| A-03 | IOP 与合法仓库来源筛选原因透明；Springer 401 与密钥存在性分离 |
| U-01 | 原文主图未实际核验时 DEEP 不能完成；缺核心 Supplement 应 PARTIAL |
| U-02 | PDF 哈希变更与证据来源不匹配应阻断；证据主张可追溯 |
| U-03 | 四类论文有差异化阅读，PCMCI 不能冒充 ATE/CATE 处理效应 |
| U-04 | 正式 DEEP 可以生成独立精读笔记，非 DEEP 不伪装精读 |
| O-01 | Zotero API 读取三篇真实论文、附件/批注；零 Zotero 写入 |
| O-02 | `E:\Research_Knowledge_Base` 空 Vault 初始化、读写、Obsidian 原生链接可用 |
| O-03 | 同一论文多次导入只保留一份 Paper 和至多一份正式 Reading |
| O-04 | 无 Zotero 条目时标 PENDING，不编造外部链接；以后匹配不重建 UID |
| O-05 | User-authored 区域及精选 Zotero 原始批注不被覆盖或篡改 |
| O-06 | 正式库写入要有可信授权、diff、目标哈希复查、备份和恢复收据 |
| O-07 | 重要 Figure 引用真实原图、实际 PDF 页码、原文 Figure；图片不乱配 |
| O-08 | 研究主题关联真实双链；关系语义与证据状态不只凭模型猜测 |
| O-09 | Topic/Method/Data 已有节点自动增量；重要新建与判断修订触发确认 |
| O-10 | Topic 按十篇有效相关文献去重阈值触发，重复任务幂等 |
| S-01 | 自动综合比较新旧证据与研究条件，保留差异解释和独立性限制 |
| S-02 | `AI_SYNTHESIS_DRAFT` 不自动变为研究者确认的科学共识 |
| S-03 | Candidate Gap 经过有界反证检索；Idea 正式入库需研究者确认 |
| B-01 | 后台调度经授权后才启动，断电后可恢复，未完成不报 COMPLETED |
| X-01 | Excel 按需输出 Master + 4 类型表；不以 Excel 行号作为主键 |

**最小真实端到端验收**：在隔离环境复用 Acquire VERIFIED 的 Krich 2021 PDF 和 Understand 已通过的结构化证据，确认 `paper_uid → Zotero(PENDING 或真键) → Paper Note → Deep Reading Note → 关键 Figure → Topic/Method/Data 双链` 的正确性与完整性。科学可靠性仍须对原文图像和关键主张进行独立抽样检查。

## 15. 冻结决议与后续变更管理

### 已冻结的用户偏好

- **统一单 Skill、统一 Router、四模块；Chat/Codex 协作，可静默与交互。**
- **独立单一 Vault**；一份知识可关联多个 Workspace；无 `00_` 之类数字前缀。
- **Zotero 先只读，Obsidian 本地 Markdown 优先，Excel 仅导出。**
- **每篇论文 1–2 份主要 Markdown；Papers 和 Readings 扁平化；机器 Evidence 后台存储。**
- **原始图表实际核验 + 批判性科学评价为正式精读硬要求。**
- **内置统一 Paper + Deep Reading + Topic(Domain/Question) + Method + Data + Workspace + Idea 模板。**
- **已有知识自动增补、重要新建/Idea/实质科学修订人工确认，人工笔记受保护。**
- **Topic 每新增默认十篇有证据的相关论文自动触发科学综合，并支持授权后台检查。**
- **外观 A+B**：学术长文排版 + 现代科研工作台；实际笔记以 Markdown 为主体。

### 工程落地前的环境事实

- 已授权方案上允许创建新空白 Vault，但**尚未实际创建**；Zotero 本地 API 尚未实连，必须首先复测。
- Understand 现版只有 PaperNoteDraft 和底层 Evidence，独立 DeepReadingDraft 与 Organize 提交者是目标能力，不能宣称 v1.3.0 已支持。
- Synthesize 尚不存在；达到十篇阈值时本版最多排队/记录，不能宣称已自动做完科学综合。
- 后台运行方案需独立安装及验证本地执行/调度器，**本设计不创建计划任务**。

> **最终验收判据**：PRKE 的价值不在“存储了多少篇论文”，而在能否保留真实原文证据、让科研者重新理解和比较这些证据，并可靠地形成可以检验和不断修订的科学认识。
