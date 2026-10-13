# Progress Controller — 状态、检查点与恢复

## 任务状态
`CLARIFYING / READY / PLANNING / RUNNING / WAITING / REPLANNING / VALIDATING / COMPLETED / PARTIAL / BLOCKED / CANCELLED`。

Task 状态与 Asset 阅读状态、具体证据核验状态和正式治理状态独立，不互相升级。

## 何时保存
持久任务在阶段结束、重要批次、外部异步任务启动或进入等待、重大计划变更、预算触顶和工具失败时落盘。单次轻量解释可以仅保留当前会话逻辑合同。

## 最低 checkpoint
`task_id / recorded_at / state / plan_revision / current_stage / completed_artifacts / pending_actions / external_job_refs / budget_usage / unresolved_issues / resume_hint`。

恢复先校验 checkpoint 和关联输出是否仍存在、外部异步任务是否已完成或仍在运行。重复执行前检查任务身份、输入摘要和已提交产物；不得盲目二次启动外部深检索。

## 实现界限
本包的 `router_cli.py checkpoint` 只提供本地 JSON 检查点及 SHA-256 摘要验证的基础示例，不是分布式事务、后台调度或跨文件崩溃一致性保证。记录与真实生产提交必须分离。
