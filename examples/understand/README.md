# Understand 实例格式

真实记录由 `scripts/understand_cli.py prepare` 基于用户授权的本地 PDF 生成，而不是通过伪造论文元数据建立演示数据库。请查看 `schemas/understand/*.schema.json`；本目录仅说明使用方法。

内部证据需保留 PDF 物理页码（从 1 计数），另行记录印刷页码（若发现），注意它们不一定相同。AI 不可仅凭提取的 Figure Caption 将图表记录标记 `VISUALLY_CHECKED`。
