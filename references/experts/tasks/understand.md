# Understand Expert Protocol
**Purpose**: 还原论文科学论证，而非按章节翻译摘要。
**Triggers**: 指定论文的科学问题、方法、公式、图表、研究设计和局限；**Exclude**: 用户只要求题录确认。
**Decision Rules**: 先判断 research/method/review/data 论文类型；识别问题-假设-数据-分析-结果-作者解释；检验关键 Figure、附录和数据支持。明确论文材料范围及未读部分；目标主张按原文页码/图表定位。
**Evidence**: 原始 PDF 版本、文件哈希、物理页码、图号、表号和实际视觉访问；pdf.prepare 或图像路径存在不足以通过视觉审查。
**Failure Modes**: 论文版面页码与 PDF 物理页码混淆，作者推断冒充观测结果，复制摘要当原文短引，未核对消融/基线。
**Deliverable/DoD**: 可独立复查的核心 Claim 表、方法评价、关键图表解释、可复用知识和未决问题。
**Example**: SIF 论文中的显著相关下降不能直接外推为 onset 误差，若文章未标记独立事件时刻，应报告 NOT_TESTED。
