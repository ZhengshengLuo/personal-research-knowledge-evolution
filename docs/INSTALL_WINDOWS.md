# Windows 安装｜先让科研 Skill 真正可用

PRKE 首先是一个科研协作入口，并非必须同时安装的 Zotero–Obsidian 一体化平台。推荐逐步启用，不使用正式研究资料作调试对象。

## 1. 启用 Skill

将 `personal-research-knowledge-evolution` **整个目录**放在当前 Codex/Antigravity 版本官方支持的 Skills 位置；不同版本的安装与注册方法可能不同，以宿主实际提供的技能列表/加载结果为准。

进入该目录，在独立的 Python 3.10+ 环境安装：

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -q
python scripts/router_cli.py doctor
python scripts/execution_core.py doctor
python scripts/scientific_semantics.py doctor
python scripts/review_gate.py doctor
```

**重点：** 在宿主新会话里确认 Skill 真正加载，再用一句自然语言科研请求检查 Router。单独执行 `doctor` 不能证明宿主已自动注册或调用外部学术工具。

## 2. 区分三个位置

建议：

- **Skill 安装目录**：只有程序、规范与模板，不放科研原件或正式 Vault。
- **任务暂存目录**：如 `E:\Codex_workspace\PRKE_STAGING`，保存此次科研任务的文件、暂存知识和日志。
- **正式科研知识库**：如 `E:\Research_Knowledge_Base`，用于长期 Paper/Reading/Topic/Method/Data/Workspace/Idea 笔记。

已有 Obsidian Vault 时不要自动建立第二份；没有时由研究者确定位置，用**空测试 Vault**先验证脚本初始化与恢复。不对现有正式库运行 `init-vault --execute`。

## 3. Zotero 与 Obsidian 按需接入

- **Zotero**：开启本地 Zotero 并确认是否支持当前只读 API；`python scripts/organize_cli.py zotero-probe --limit 3` 验证读到真实题录。未连接则保持 `ZOTERO_PENDING`，不影响普通科研工作。
- **Obsidian**：先用独立测试 Vault 检查笔记结构、人工内容保护、批次修改、备份及恢复。正式知识的科学认识更新由用户确认。
- **可信写入**：要保证未授权 Agent 无法在操作系统权限层直接写正式 Vault，需要独立可信的执行身份和 Windows ACL 等实际隔离。CLI 的 `--acknowledge-vault-write` 不是身份认证。本包未部署可信写入服务，**禁用无人值守正式提交**。

## 4. 真实科研核验

至少选择一项能够真正访问全文及 Figure 的科研任务，检查原文、实际视觉访问、统计尺度、科学审查与反证。PDF 已解析或图像已渲染不能代表真正看过图表。不得把 128 项离线单元测试直接当成真实科研 Gold Set。

## 5. 回滚与升级

升级前保存原始 1.6.0 完整包及用户项目备份。本包保留既有 JSON/CLI 使用方式；研究者正式知识资产**不自动迁移或修改**。先在新 Skill 路径测试，再切换宿主加载目录。对未知旧索引、陈旧授权、真实写入冲突和不可解释的科学关系停下审查，不执行自动覆盖。长期 Worker 未部署时，不承诺跨会话后台持续运行。
