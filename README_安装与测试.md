# PRKE v1.5.0-rc1｜单 Skill 集成候选版

- 包含 **一个 `SKILL.md`** 与 Router / Acquire / Understand / Organize / Synthesize 四个业务模块（阶段05=Synthesize，阶段06=集成验收，不是第六个业务 Skill）。
- **完整继承 v1.4.0 基线**的命令和模板；新增 Gap Evolution、Topic/Method/Data 的受控写入、Synthesize 科学草稿、阈值触发等候选功能。
- 工程离线测试通过才可以声明 OFFLINE_TESTED，未完成真实 Windows/Gold Set/24h 现场验收。`RELEASE_SCOPE.md` 列明限制。

## 解压及基础运行

使用干净新目录安装，**不要覆盖**正在使用的 v1.4.0，也不要把技能目录直接放到正式 Obsidian Vault 内。

```powershell
$skill = 'E:\Codex_workspace\05_AI提示词与工作流\SKILL创建\PRKE-v1.5.0-rc1-sandbox\personal-research-knowledge-evolution'
Set-Location $skill
$env:PYTHONUTF8 = '1'
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_*.py' -q
python scripts/router_cli.py doctor
python scripts/acquire_cli.py doctor
python scripts/acquire_pdf_cli.py doctor
python scripts/understand_cli.py doctor
python scripts/organize_cli.py doctor
python scripts/synthesize_cli.py doctor
python scripts/knowledge_cli.py doctor
python scripts/trigger_cli.py doctor
```

根据你实际存在的 Conda 环境更换 `python`，不要擅自安装或修改系统级 Python。

## 科研证据路线

1. `evidence_bridge_cli.py --paper-dir <已验收的Understand任务> --topic-id <主题> --research-question <明确RQ> --output <task/input.json>` 输出待科学核验的真实来源证据包。
2. 根据 `routes/synthesize.md` 调用可用学术工具、原文与科学审阅 Agent **真实形成**科学综合，在 input JSON 明确 `scientific_findings`、研究可比性、研究分歧和 Gap 的外部 `verification.searches`，不得虚构。
3. `synthesize_cli.py stage --input <科学核验后的JSON> --output <库外新任务>` 生成 Evidence Matrix、Synthesis 草稿、审计。
4. `knowledge_cli.py stage --vault <隔离实验Vault> --synthesis-result <任务/synthesis_result.json> --stage-dir <另一新任务>` 生成 Topic/Research Gap Overview/哈希链草稿；展示 `plan.json` 和计划 SHA。
5. 只有取得用户**针对这个批次**的明确批准，在可信宿主下运行 `knowledge_cli.py commit --vault <隔离Vault> --stage-dir <任务> --approve-plan-sha256 <实际SHA> --acknowledge-vault-write`。命令行参数不是可信身份认证。
6. 重大科学修订通过 `stage-decision`（`APPROVE_REVISION`/`REJECT_REVISION`/`APPROVE_IDEA`/`ARCHIVE_GAP`）单独操作；Method/Data/Topic 的 AI 补充通过 `stage-knowledge`，人工区不自动改写。
7. `trigger_cli.py check` 用经核实有效唯一论文清单检查10篇阈值，任务记录持久化。Windows 后台调度默认**不安装、不启动**。

## Excel 按需导出

只有需要对照表时运行 `export_excel_cli.py`，其可选依赖为 `artifact_tool`，在用户 Windows 上需要安装并验证；不必为了主科研流程强制安装。

## Windows 真实验收

阅读 `docs/PRKE_v1.5.0-rc1_Windows_真实科研集成验收Prompt.md`、`docs/ACCEPTANCE_PROTOCOL.md`、`docs/CAPABILITY_MATRIX.md`。

明确：**本包是测试候选，不表示科学创新已经独立核验、自动外部检索已在本机成功、3–5篇 Gold Set已确认或 Windows 24 小时运行已完成。**
