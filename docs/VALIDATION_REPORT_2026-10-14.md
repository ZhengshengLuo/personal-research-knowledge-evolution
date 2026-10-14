# PRKE 1.6.0-integration-preview｜隔离构建与验收报告

**日期：** 2026-10-14（当前工具容器）  
**基线：** 用户提供 v1.5.0-rc1 ZIP，包含一个主 SKILL.md、四业务路由和旧版确定性 Python CLI。  
**执行范围：** 隔离构建、离线 unittest、示例合同/CLI doctor 与静态校验；没有修改用户远程仓库或正式 Zotero/Obsidian 文件。

## 真实完成结果

| 检查 | 结果 | 解释 |
|---|---|---|
| 旧版基线 `python -m unittest discover -s tests -q` | **116/116 PASS** | 原始安装包隔离回归 |
| 优化后同一命令 | **128/128 PASS** | 包含新增 12 项合成契约/回归测试 |
| `router_cli.py doctor` | PASS | 四业务协议、Router Schema 与入口检查 |
| `execution_core.py doctor` | PASS | Provider 注册表结构检查，不是在线工具验证 |
| `scientific_semantics.py validate` 示例 | PASS | 一篇虚构示例，结构与引用一致，非科研真值 |
| `review_gate.py validate` 示例 | PASS | 诚实记录 `SELF_CHECK` 高风险审查未独立完成 |
| Gap 反证/范围修订测试 | PASS | 合成测试中生成分开的两类事件，历史哈希链有效 |
| Method/Data 类型修复 | PASS | 合成 Vault 中分别生成为 method/data_resource，非 Topic |

**失败/阻断类测试：** 对无授权写入、Host 重复动作、错误 provider、伪造全文可用范围、目标冲突等场景按预期拒绝；这些预期拒绝不是回归失败。

## 未完成验收，不可宣称 PASS

G1：真实 Codex/Antigravity Host Handoff、获取/精读/综合/知识更新 S0–S4 全程实跑。

G2：独立人工 Gold Set 3–5 篇开发集和 10–20 篇保留集，以及基础模型、旧版、新版、专项 Skill 的公平比较。此前 Undermind 论文级审查可作为示例，不能当独立 Gold Set。

G3：Windows 实机 Zotero 连接、Obsidian 正式 Vault 保护、不同操作系统身份的 Trusted Committer、人工审批可靠性、S5/S6、24 小时 Worker。

**安全说明：** 旧版 `organize_cli.py`/`knowledge_cli.py` 具有用 CLI 参数执行受控提交的能力，但没有独立 Windows 用户身份认证。保留它们仅为了兼容与测试；在真实 NTFS/宿主隔离验收完成前不允许运行无人值守生产写入。

## 发布决定

**可交付：集成预览 ZIP / 合成离线验收记录。**  
**不得宣称：Integration Candidate、Scientific Validation Candidate、Scoped Stable Release 通过**（G1/G2/G3 尚未完成）。

下一阶段真实任务及 Windows 验收步骤参见 `docs/WINDOWS_VALIDATION_PROMPT.md`。
