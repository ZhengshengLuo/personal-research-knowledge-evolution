# Router｜让科研任务自然地使用正确能力

根据**当前要交付的科研成果**而非关键词数量决定主路线，必要时调用其他能力。Router 是协调方式，不是第五项科研工作。

| 用户需要 | 首选能力 | 什么时候补充其他能力 |
|---|---|---|
| 了解某领域、找原始论文/方法/数据 | Acquire | 关键主张需要全文精读时转 Understand |
| 解释特定论文、图表和统计方法 | Understand | 需要比对其他工作时补 Acquire / Synthesize |
| 比较科学认识、寻找反证或研究问题 | Synthesize | 证据不够时返回 Acquire/Understand |
| 利用或修订已有知识、整理材料 | Organize | 需要新的科学审查时转 Understand/Synthesize |

先检查已接入宿主的**实际工具能力**。`INSTRUCTION_READY` 只说明有协议；不能宣称 Undermind/PDF/子 Agent 已运行。复杂任务记录必要的论文身份、来源、访问等级、模块交接与剩余问题；简单问题直接回答即可。

同一任务可在不同能力间往返。模块报告的 `COMPLETED` 只表示其约定交付完成，不能自动代表科学论断被证明。用户未要求入库时无需启用 Organize 正式写入。正式资产操作遵守 `router/governance.md`。

实际请求/结果可按 `schemas/router/module_request.schema.json`、`module_result.schema.json` 交接；有需要时用 `scripts/execution_core.py` 留下宿主报告，但其回执不是不可伪造的第三方证明。
