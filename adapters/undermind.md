# Undermind 工具适配 — Acquire

本文件描述**如何在宿主真的提供 Undermind MCP 连接时**调用；本地安装 Skill 不自动安装或连接 Undermind。工具签名或权限变动时，以当前实际工具描述为准。

## 开始前

1. 先调用 `get_orientation`（本会话第一次使用时），再 `list_workspaces`。
2. 根据用户明确选定或已有资料匹配已有 `workspace_id`；不要自动调用 `create_workspace`：这是持久化的远端变更，应由用户确认。
3. 保存 workspace ID、任务目标以及结果 cite_key。cite_key **仅在该 workspace 内唯一**，不能当作全局文献 ID；跨 workspace 用 DOI / 完整题录复核。
4. 工具未连接、需要新的授权或外部传输风险：交给 Router 进行权限决策；不可假装调用成功。

## 优先工具

| 任务 | Undermind 工具 | 核心约束 |
| --- | --- | --- |
| 探索性/定向语义检索 | `search_papers` | 必填 workspace_id + 2–3 句像论文摘要的自然语言 `sample_abstract`，不是关键词列表 |
| 参考文献/引用扩展 | `search_papers` + search_type=references/citations | 提供 seed_papers cite_key，遵守单次数量和页数约束 |
| 领域完整深度调研 | `launch_deep_search` | 传递自包含的自然语言 `goal`，不是 WoS 检索式；异步运行，不能直接声称完成 |
| 查看已有深检索状态 | `inspect_deep_searches` | 启动前先查重，恢复任务时优先查询已有搜索状态 |
| 确认指定论文 DOI/题目 | `lookup_papers_by_metadata`、`get_paper_info` | 未查到要标 UNKNOWN，不推测 DOI |
| 专家/团队线索 | `find_papers_by_author` | 同名需消歧，不因作者头衔将文献直接评为高质量 |
| 为后续 Understand 准备 PDF | `get_paper_info`、`get_pdf_download_links` | 记录实际 PDF 可用/下载状态，不代表已阅读；不要绕过权限 |
| 原文针对性阅读（属于 Understand） | `read_pdfs` | 最多 4 篇/次，调用后结果应由 Understand 处理证据，不得在 Acquire 冒称已完成 |

## Deep search 操作边界

- 典型耗时数分钟；返回通常是任务开始结果。只有 `inspect_deep_searches` 确认完成并取得列表后，才能报告检索成果。
- 用户目标已改变时，不重复创建大量相似深检索；保留目标字符串和搜索路径以利复用。
- `launch_deep_search` 为自主多轮主题检索，不自动满足 WoS/Scopus 等数据库可复现式系统检索要求。
- 工作区创建、文件写入、加星、移动文件夹属于持久化远端动作；Acquire 默认不执行。即使可以调用也需要遵守 PRKE 的独立权限策略。

## 工具降级和真实性

- 缺少 Undermind 时：检测其他**真正可用**的学术搜索服务、官方元数据或检索工具。若未提供任何工具则 `BLOCKED`/`PLAN_ONLY`，不能由语言模型自行生成貌似真实的推荐列表。
- AI 检索报告不是原始出版证据；科研主张核验仍须阅读对应论文内容。
- 暂不建议自动向外部服务上传未公开资料。远端工具的已有开放论文读取与传输用户机密资料应分别判断。
