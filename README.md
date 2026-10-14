# PRKE — Personal Research Knowledge Evolution

**状态：`1.6.0-integration-preview`（隔离集成预览，非正式科研验收或稳定生产发布）。**

一个以**科研问题和可检查证据**为中心的单入口 Agent Skill。共享科学推理/证据/治理规则，四个业务路由：Acquire、Understand、Organize、Synthesize。宿主 Agent（例如 Codex 或 Antigravity）进行科研推理和可用工具的实际调用；PRKE 确定性脚本负责证据结构、任务回执、去重、候选关系及受控知识变更。

## 安装和使用

1. 解压根目录 `personal-research-knowledge-evolution/` 到宿主支持的 Skills 位置，按当前宿主官方方式启用。不要将资料 Vault 放在 Skill 包内。
2. 使用 Python 3.10+：`python -m pip install -r requirements.txt`。普通 QUICK 科研问答不要求运行 Zotero、Obsidian 或所有 PDF 组件。
3. 运行 `python -m unittest discover -s tests -q`，或逐项执行 `router_cli.py doctor`、`execution_core.py doctor`、`scientific_semantics.py doctor`、`review_gate.py doctor`。
4. 在聊天中直接提出科学问题：例如“精读这篇方法论文并指出其因果识别假设”，或“对比已有论文的事件响应 onset 证据，主动检索相反研究”。无需记忆路由名称。
5. 管理正式科研知识时，首先阅读 `router/governance.md` 和 `docs/INSTALL_WINDOWS.md`。**普通 Agent 持有 Vault 写入权限的环境不允许无人值守正式提交。**

## 关键文件

| 组件 | 路径 | 实际功能 |
|---|---|---|
| Skill 入口 | `SKILL.md` | Agent-first、QUICK/RESEARCH/MANAGED、四业务路由与安全红线 |
| 专家协议 | `references/scientific-core/`, `references/experts/` | 科学推理、Scientific Critic、11 份按需专家协议 |
| Host Handoff | `scripts/execution_core.py` | P0/P1 请求准备、宿主报告、文件哈希、幂等回执；**不执行真实 provider** |
| 科学语义 | `scripts/scientific_semantics.py` | Claim/Evidence/Relation 候选数据核验；**不判断科研真值** |
| 论文身份 | `scripts/paper_identity.py` | DOI/arXiv/文件版本与候选重复识别，库外记录 |
| 独立审查合同 | `scripts/review_gate.py` | 审查来源/方法声明核验；不伪称人类同行评审 |
| 既有业务 CLI | `scripts/{router,acquire,understand,organize,synthesize,knowledge,trigger}_cli.py` | 保留旧版代码与回归测试，Gap 事件/Method/Data 模板修复 |
| 验收和限制 | `docs/IMPLEMENTATION_STATUS.md`, `docs/CAPABILITY_MATRIX.md` | 真实与未测试能力逐项区分 |

## 最小 Host Handoff（外部工具由宿主调用）

```powershell
python scripts/execution_core.py capabilities
python scripts/execution_core.py prepare --workspace C:\ResearchTasks\prke-test --task-id demo1 --action-id action01 --capability literature.search --provider host_search --input examples/vnext/host_input.example.json
# 宿主真实调用搜索工具后，形成与 action01 匹配的结果 JSON，再 finalize；不能把 prepare 当成检索成功。
python scripts/execution_core.py inspect --workspace C:\ResearchTasks\prke-test --action-id action01
```

`execution_core` 不自带 Undermind、联网搜索 SDK；外部检索、PDF 视觉、独立科学评价需要真正可用的宿主工具。正式 Vault P2 提交使用现有受控 CLI 的历史功能，但**其参数开关无法核实人类身份**，稳定权限必须经 Windows/宿主隔离后重新验收。

## 真实能力边界

已在隔离容器中通过合成数据回归测试，**不能**把这解释为真实科研 Gold Set、Windows Zotero 联动、Antigravity/Codex 每种环境、可信自动写入或 24h Worker 已验收。没有满足 G0–G3 的功能不发布稳定声明。详见 `docs/IMPLEMENTATION_STATUS.md`。

完整批准的最终设计合同：`docs/PRKE_FINAL_DESIGN_CONTRACT.md`。历史资料在 `docs/` 中保留供追踪，不能替代本文和能力矩阵的当前发布说明。
