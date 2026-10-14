# PRKE 1.6.0-integration-preview — 实现与验收状态

**基线**：使用研究者提供的 v1.5.0-rc1 完整 ZIP 隔离解压；基线运行 116 项 unittest，全部通过。**本次实施依据** `docs/PRKE_FINAL_DESIGN_CONTRACT.md`。仅改动隔离构建目录，不写远程仓库、Obsidian 正式 Vault 或 Zotero。

## W0–W7 实际交付

| 工作包 | 当前完成 | 未完成/边界 |
|---|---|---|
| W0 基线保护 | 完成：独立原始 ZIP、可重复 116 项回归、原文件快照 | GitHub HEAD 同步需用户在目标仓库现场核实 |
| W1 Agent/Router | 完成：科研意图驱动 SKILL、QUICK/RESEARCH/MANAGED、专家按需加载入口 | 宿主 Agent 行为准确率仍需 S0 真实试验 |
| W2 执行 | 完成：声明型 capability registry、P0/P1 Host Handoff、产物哈希与不可重复回执 | **无通用外部 SDK；host 自报回执不是可信第三方执行证明；未实测实时工具交接** |
| W3 科研审查 | 完成：Scientific Core、11 项任务/方法/学科专家协议、独立复核数据结构与边界门槛 | **未完成独立人工 Gold Set 和真实 PDF 全面验证** |
| W4 科学知识 | 完成：候选 Claim/Evidence/Relation 验证、论文身份候选、反证与范围修订分离、Gap 历史摘要 | **结构核验不等于科学关系真值**；跨任务统一事务索引仍需集成 |
| W5 Organize | 完成：Method/Data 新节点类型修复、原有 stage/commit/recovery 保留 | **可信独立提交主体和 Windows ACL 未实现/验收；无人值守生产写入禁用** |
| W6 可靠性 | 完成：合成离线安全、去重和事件测试；提供真实评估计划 | Windows/Zotero 实机、24h soak、跨学科 Gold Set、S1–S6 真实闭环未完成 |
| W7 发布 | 完成：预览包、README/安装指南、CI 文件、版本及能力矩阵 | Stable RELEASE BLOCKED；上游 LICENSE 尚需作者选定，CI 尚需真实 GitHub 运行 |

## 科学和安全发布承诺

状态命名：`IMPLEMENTED`（有程序/协议）、`OFFLINE_TESTED`（合成测试）、`HOST_DEPENDENT`（宿主可用时依赖真实工具）、`NOT_RUN`、`BLOCKED_FOR_PRODUCTION`。不得声称 v1.6 通过 S0–S6 或 G0–G3；仅 G0 **本容器离线子集**已运行。

因原仓库没有明确 LICENSE，本次不擅自为原作者选定开源许可证。欲公开正式发布前，须由知识产权人决定授权条款，并核对上游所有资源的许可。
