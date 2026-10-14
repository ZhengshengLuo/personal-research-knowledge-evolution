# PRKE 1.6.0-integration-preview 发布范围

本包属于**受控集成预览版**，不是经过 G0–G3 完整认证的稳定版本。

已在隔离构建中进行合成离线回归，包括新增 Host Handoff 回执合同、Paper 身份保守匹配、Claim 级候选语义核验、Scientific Critic 声明门槛、Gap 反证独立事件、Method/Data 模板修复。**上述测试不能证明科学结论真实。**

需要真实执行的宿主能力（Undermind/其他检索、原始 PDF 视觉、跨学科科学评价）仍取决于实际工具连接。可信 Windows 文件权限隔离、Zotero 真实连接、人工 Gold Set、≥24h Worker 尚未验收；**不得**声称无人值守正式 Vault 写入或稳定跨会话后台执行。

正式发布前还需用户选定上游代码 LICENSE，补齐真实宿主兼容、科研准确性测试和 CI 实跑。详见 README.md、docs/IMPLEMENTATION_STATUS.md 与 docs/CAPABILITY_MATRIX.md。
