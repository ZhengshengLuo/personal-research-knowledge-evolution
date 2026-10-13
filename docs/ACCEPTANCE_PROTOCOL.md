# 阶段 06｜PRKE 最终集成科学与工程验收协议

## 六层验收

| Layer | 测什么 | 判据 |
|---|---|---|
| L1 | v1.4 基线与新命令回归、Windows 编码、安装哈希 | 单元/契约检查无非预期回退，任一失败明报 |
| L2 | Understand PDF 真证据 → Bridge → Synthesize → Knowledge Stage | 论文身份、PDF sha、Claim Ref、定位与输入版本一致 |
| L3 | 3–5 篇人工独立 Gold Set | 关键来源全覆盖人工裁决，零伪造或重大科学过度推断 |
| L4 | Topic 10 篇、Gap 反证与演化 | 真实论文非合成科研结论；去重、幂等、人工区保护、变更原因可重放 |
| L5 | Zotero 只读、受控 Vault 写入、Prompt Injection、错误恢复 | 未授权写入、私有文献外传及原始资料损坏为零 |
| L6 | Windows 24h 运行，故障注入与恢复 | 实际 ≥86400 秒记录，心跳/异常/恢复/重试/断点真实可查 |

## 四个端到端真实科研案例

1. **A Krich 2021**：使用其真实审读任务中的 Figure Inventory、Claim-Evidence、论文身份与 PDF SHA，经过 `evidence_bridge_cli.py`、Synthesize Stage 和独立测试 Vault 的 Knowledge Stage，抽查原图与论文结论一致。
2. **B 因果与依赖区分**：使用真实原文比较 PCMCI、Granger、Transfer Entropy 等；不得将相关/时间条件独立性网络自动升级为已识别处理效应。必须报告样本与方法可比性。
3. **C 10 篇知识演化**：选择一个 Topic 至少10篇真实去重且核验来源的相关论文，对**旧+新**证据再综合。合成数据只用于阈值边界与故障测试。
4. **D Research Gap 反证**：选择确有关键先前研究的真实 Gap，经外部检索更新 `closest_prior_work`、审计状态和 Gap 版本，并检查分叉/归档审查链。

## Gold Set

必须由人工或独立审阅者核对3–5篇。每篇记录 DOI、PDF 版本、正文全部重要图表、方法链、研究结果原文数值和页码、论断强度、作者及 Agent 局限和一项可能过度解读的审查问题。使用 `docs/SCIENTIFIC_GOLDSET_TEMPLATE.md`；不使用 PRKE 自己的输出作为独立标准答案。

## 批次与恢复

任何正式 Vault 首次写入之前必须展示用户选择的目标 Vault、更新路径、变化预览、Plan SHA，并等待真实批准。只在复制或空白实验 Vault 中进行崩溃与恢复测试。`knowledge_cli.py recover` 仅处理未完成的备份/收据；已经 COMMITTED 的批次不能重演。

## 24 小时测试

`soak_cli.py run --output <taskdir> --hours 24 --interval-seconds 300` 在具备使用权限的 Windows 计算机上运行，`verify` 检查真实 Unix elapsed ≥86400 秒；随后结合后台任务日志评审任务创建、重试、取消、暂停、故障恢复与实际丢失/重复情况。仅通过时间门槛不能宣称“后台可靠性 PASS”。未经明确授权不得配置 Task Scheduler。

## 最终发布判断

- `PASS`：上述全部必须项通过。
- `CONDITIONAL_PASS`：核心科学与安全功能通过，仅有不影响已声明范围的非关键限制。
- `BLOCKED`：重大科学伪造、关键功能缺失、越权/破坏，或必要真实环境未完成。

当前 RC1 仅完成离线工程基线，因此**正式最终验收状态：NOT_RUN**。
