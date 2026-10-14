# Windows 安装与安全使用（预览版）

## 安装

解压单一 `personal-research-knowledge-evolution` 目录，使用宿主当前支持的 Skills 安装或工作区指定机制加载 `SKILL.md`。安装位置以当前 Codex/Antigravity 的实际版本配置为准；PRKE 不修改宿主全局配置。建议隔离 Conda/venv Python 3.10+，运行 `python -m pip install -r requirements.txt`，然后运行离线 unittest 和各 CLI `doctor`。

## 路径与权限

任务暂存建议使用单独目录如 `E:\Codex_workspace\PRKE_tasks`。正式 Vault 如 `E:\Research_Knowledge_Base` 须由用户确认；PRKE 不应自动创建、迁移或覆盖已有正式知识库。源论文通常由 Zotero 或研究项目目录管理，预印本与正式版本的 PDF SHA 单独保留。

**生产权限先决条件**：把受保护 Vault 的 NTFS ACL 设为普通研究 Agent 账户只读或拒绝写入；可信提交主体使用另一具独立访问权限的 Windows 身份/受信宿主审批路径。只做 Prompt 限制或检查 `--approve-plan-sha256` **不构成**技术隔离。由于此包未实现可信身份 broker，不应进行无人值守 P2/P3 操作。实际账户和 ACL 改动必须由用户在本机另行配置、验证，不能由聊天中的 Agent 自行授予自己权限。

## 部署检查

1. 验证 `python -m unittest discover -s tests -q`；离线模拟测试通过仅覆盖合成输入。
2. 只读 `python scripts/organize_cli.py zotero-probe --limit 3`；若连接失败则保持 `ZOTERO_PENDING`。
3. 对一个独立新建的**测试 Vault**执行 Stage/Commit/Recovery，检查人工内容、并发冲突与回执。正式 Vault 禁止先用作测试素材。
4. 使用不同权限的 Agent 身份尝试直接写测试 Vault，**必须被 Windows 权限拒绝**，再验证可信主体能够凭真实用户批准提交。此项未通过不得声称可信写入已启用。
5. 只有真实配置持久化 Worker 后才能声称跨会话运行。长期任务另行通过 24h 真实运行验收。

## 迁移和回滚

保留旧 v1.5.0-rc1 ZIP 原件。升级预览版时，不修改现有 Vault、Zotero 与服务账号；先在测试目录跑旧/新脚本比较。遇到未知索引版本、受管内容被编辑或非幂等提交问题立即停止，保留回执和备份，不自动覆盖。
