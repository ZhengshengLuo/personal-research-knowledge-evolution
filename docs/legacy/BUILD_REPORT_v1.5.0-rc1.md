# v1.5.0-rc1 隔离构建记录（2026-10-13）

## 源码来源与继承

源包：`PRKE_v1.4.0_Router_Acquire_Understand_Organize_完整测试包.zip`。依照已批准的阶段 05 + 06 冻结合同从原 ZIP 解压，保留全部原有模块、CLI 与模板，不覆盖原 ZIP 或用户本机数据。改动主要在 Router Synthesize 注册、旧阶段说明、原有期望状态的回归断言更新和新增模块。

## 已在容器运行的检查

- 原始源包安装后离线基线：**97 个 unittest**，通过。
- 新增后开发目录隔离离线测试：**116 个 unittest**，通过（合成/隔离工程场景，不是独立科研真值）。
- `router_cli.py doctor`、`synthesize_cli.py doctor`、`knowledge_cli.py doctor`、`trigger_cli.py doctor`：通过。
- 合成来源 Synthesize Stage 演示：预期 `PARTIAL`，不误报结构性 `COMPLETED`。
- 五表 Excel：以合成 Organizer Index 运行 `artifact_tool` 导出，已在当前隔离 Python 环境成功创建 .xlsx；**用户 Windows 依赖仍待现场核验**。

## 测试范围之外

- 真实 Zotero 本机 API 和 Obsidian Windows GUI；用户 v1.4.0 Organize 的正在进行的外部验收结果尚未提供。
- 未在本环境独立审查 3–5 篇真实论文，不运行真实24h；所以不宣称 G5/G6 PASS。
- 外部反证检索和学术综合逻辑依赖宿主可用的检索/阅读 Agent，离线工具只校验其交付的来源引用与限定状态。
- 本地 CLI 参数审批不提供不可伪造的人类身份认证；生产环境需要可信宿主/ACL 权限分离。
