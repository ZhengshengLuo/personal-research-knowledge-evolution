# Organize Expert Protocol
**Purpose**: 将经过来源核验的论文发现整理为可理解、可关联、可演化的知识，不泛滥生成文件。
**Triggers**: 入库、论文身份匹配、跨主题关联、知识更新；**Exclude**: 纯研究问答且无保存需求。
**Decision Rules**: 保留 Paper/Reading/Topic/Method/Data/Workspace/Idea 七类主要笔记；Claim/Evidence/Relation/Gap 为结构化对象。先核验 Paper UID 与 DOI/arXiv/PDF SHA/Zotero Library+Key 的映射。对预印本与正式版建立版本关联而不静默合并。仅具长期复用价值才新建 Method/Data/Topic。
**Evidence**: 关联只基于真实的 Claim 与可定位的 Evidence；Metadata-only 不能冒充全文。
**Failure Modes**: 创建重复笔记、覆盖人工区、把 Agent 候选写成科研者确认、把 SHA 视为授权签名。
**Deliverable/DoD**: 简洁 Markdown、受控差异、权限状态、真实提交回执；无正式写入授权时只 Stage。
**Example**: 两篇论文使用相同 SIF 重建产品应记录共享输入/训练依赖，不应作为完全独立证据重复计数。
