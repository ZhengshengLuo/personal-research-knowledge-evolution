# PRKE v1.4.0 · Windows / Codex 真实验收 Prompt

请对 **PRKE v1.4.0** 在我当前 Windows 主机上开展严格的真实验收。不得另起项目、重写 Router，也不得使用模拟 Zotero、虚构论文或合成科学证据来冒充真实结果。

## 已知路径与约束

- Skill（解压后的隔离安装）：`E:\Codex_workspace\05_AI提示词与工作流\SKILL创建\PRKE-v1.4.0-sandbox\personal-research-knowledge-evolution`
- Python 首选：`D:\Anaconda\python.exe`，实际运行前核对可用性；不要影响原有科研环境。
- Zotero Desktop：上次检测 9.0.6，当前须复查实际运行版本；**只读**，禁止修改库、附件、批注或 `zotero.sqlite`。
- Obsidian：上次检测 1.12.7，正式空 Vault 获得用户方案批准，目标 `E:\Research_Knowledge_Base`，不能导入旧示例 Vault。
- 真实 Understand 精读记录：`E:\Codex_workspace\05_AI提示词与工作流\SKILL创建\prke-live-test-20261013\understand\krich2021-functional-convergence`
- 真实原 PDF 的路径和 SHA 均由 `source_bundle.json` 读取并复核，预期 DOI `10.5194/bg-18-2379-2021`，不靠预期值覆盖实际文件结果。
- **本轮允许只读检查、库外暂存及用户既已允许的“创建空白 Vault”。** 对已经存在的 Vault 内容、论文笔记与证据写入，必须先展示预览并等待我对**本批次**的明确确认。

## 第一阶段：版本、依赖、回归

1. 检查 Skill 目录只有一个根 `SKILL.md`，读取 `RELEASE_SCOPE.md`、`routes/organize.md` 和最新 Registry。
2. 依次运行 Router、Acquire、Acquire PDF、Understand、Organize 五个 `doctor`。
3. 先在普通 Windows 默认编码环境复测全部离线单元测试，再以 `PYTHONUTF8=1` 补充复测。记录原始退出码、通过数、错误及所需依赖；不要通过跳过失败测试获得 PASS。
4. 检查当前 PRKE v1.3.0 生产工作目录未被覆盖、没有任何修改。

## 第二阶段：Zotero 真实只读连接

1. 检查 Zotero Desktop 实际是否运行，本地 API 是否可访问；若未运行或未启用，只报告需要我进行的手工操作，不擅自修改系统偏好或启动高风险服务。
2. Zotero 连接就绪时调用 `organize_cli.py zotero-probe --limit 3 --children`，确实读取最多 3 篇论文，核对题名、DOI、Item Key、Collection、附件/批注元数据及本机 API 版本。
3. 如果已有 Krich 2021 论文，核验真实 Item Key 和对应 `users/0` 或组库标识；**不能靠 DOI 猜测 Item Key**。若没有，正式笔记使用 `ZOTERO_PENDING`。
4. 不做 POST/PUT/PATCH/DELETE，不读取/改写数据库，不外传凭证。

## 第三阶段：Obsidian 空白 Vault

1. 检查 `E:\Research_Knowledge_Base` 是否不存在/为空；若已有内容，**停止创建，不覆盖**。
2. 先执行 `organize_cli.py init-vault --vault <目标>` 的 PLAN_ONLY。
3. 使用事先明确同意的空白 Vault 初始化方案，在确认目标安全后执行 `--execute --acknowledge-empty-vault`。
4. 检查无数字前缀目录，`Papers`、`Readings` 为扁平结构；`Templates` 有 8 份模板；`.obsidian/snippets/prke-hybrid.css` 已安装但不自动启用；`.prke/index.json` 存在。
5. 在 Obsidian 中打开该 Vault，验证 Markdown 可读性。若无法通过当前工具检查 GUI，如实说明，不得冒称 Obsidian UI 已验证。

## 第四阶段：真实 Krich 2021 精读交接预览（先停在这里等待确认）

1. 使用真实 `source_bundle.json`、`reading_record.json`、`claim_evidence_matrix.json`、`figure_inventory.json`、`reading_audit.json` 和原始 PDF，重新运行 Understand 的确定性审计。
2. 若重新审计为 `COMPLETED`，执行：

```powershell
$root  = 'E:\Codex_workspace\05_AI提示词与工作流\SKILL创建'
$skill = "$root\PRKE-v1.4.0-sandbox\personal-research-knowledge-evolution"
$vault = 'E:\Research_Knowledge_Base'
$paper = "$root\prke-live-test-20261013\understand\krich2021-functional-convergence"
$stage = "$root\prke-organize-live-20261013-batch01"
$py = 'D:\Anaconda\python.exe'
& $py "$skill\scripts\organize_cli.py" stage-paper `
  --paper-dir $paper --vault $vault --stage-dir $stage `
  --stem 'Krich 2021 - Functional convergence'
```

3. 核查 `drafts/paper.md`：科研问题、核心发现、证据位置、批判性局限、阅读状态、Zotero PENDING 或真实映射。
4. 核查 `drafts/reading.md`：正式精读结构、图表记录、PCMCI 因果解释边界、未核验细节；**不要宣称本版已自动裁切并嵌入每一张原图**。
5. 检查本次 `plan.json` 所列 CREATE/UPDATE、稳定 UID、原 PDF SHA-256、目标索引哈希、Snapshot 和所有将要写入的路径。报告 plan 的 SHA-256。
6. **此时停止，不运行 commit。** 请向我展示简明 diff/计划、待写文件和仍然存在的缺口，等待我明确批准当前批次。

## 第五阶段：仅在我明确批准第四阶段的计划后

由我确认范围及计划摘要后，使用 `plan.json` 的真实 SHA-256 执行 `organize_cli.py commit ... --approve-plan-sha256 <SHA256> --acknowledge-vault-write`。验收完成必须核对 `commit_receipt.json` 中 `state=COMMITTED`、Vault 内实际文件内容和 `.prke/evidence` 快照，另验证没有修改 Zotero、没有复制 PDF 到 Vault、没有覆盖人工批注。未经我在本次对话里确认，不得执行第五阶段。

## 质量和安全反向验收

先在**独立测试 Vault 和测试任务副本**中验证：缺审批无法提交；源 PDF/阅读 JSON 变化无法提交；目标文件在预览后被人工编辑无法提交；重复提交不重复建文档；人工笔记区域保留；已有 AI 管理区被人工修改会拦截；危险路径拒绝。不得为了测试而破坏正式知识库。

## 最终汇报

分别报告 Router、Acquire、Understand、Organize 的离线状态、Zotero 真实连接状态、Vault 实际状态、Krich 论文的草稿交接质量、待审批计划以及失败原因。准确区分 `OFFLINE_PASS`、`REAL_CONNECTION_PASS`、`PARTIAL`、`NOT_IMPLEMENTED`，特别标明 Synthesize、Topic 十篇自动综合、图像裁切嵌入和 Excel 导出仍属于后续阶段。所有报告放在库外测试任务目录，不编造未实际执行的操作。
