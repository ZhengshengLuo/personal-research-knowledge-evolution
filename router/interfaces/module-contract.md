# Router ↔ Module 统一接口（四路由）

- 统一请求 `schemas/router/module_request.schema.json`：任务/阶段目标、输入引用、输出、证据、授权。业务模块不能自行升级权限。
- 统一结果 `schemas/router/module_result.schema.json`：COMPLETED/PARTIAL/BLOCKED、真实产物、来源、访问与证据、问题、下一步。**文本承诺或规划不能代替真实执行证明**。
- 当前注册表的四个业务路由均为 `INSTRUCTION_READY`，分别引用 `routes/{acquire,understand,organize,synthesize}.md`；指令可用不等于外部工具已真实连接或科学结果已独立验收。
- `INSTRUCTION_READY` 只表示宿主 Agent 可按协议执行，当 Undermind/其他检索工具不可用时，要 PLAN_ONLY/BLOCKED 或明确降级。Router 当前 CLI 不包含可直接调用 Undermind 的 Python SDK。
- Acquire 本地 S1 记录按 `schemas/acquire/search_plan.schema.json`、`candidate_set.schema.json` 和 `search_log.schema.json`；这几份是**中间数据**，可交给现有 Understand 模块。
- Router 逐项检查 `ModuleResult` 交付和 provenance，不因 status=COMPLETED 自动提高 PDF 阅读/科学证据核验等级。
