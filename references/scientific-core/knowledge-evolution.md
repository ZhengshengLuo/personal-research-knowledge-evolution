# Scientific Knowledge & Protocol Evolution

## 两条独立演化链

**Scientific Knowledge Evolution**：新论文/实验 → 可信 Claim → 关系审查 → Topic 当前认识 → 候选 Gap 事件 → 必要时研究者科学决定。新证据可支持、挑战、收窄、合并、拆分，也可 NO_MATERIAL_CHANGE。

**Expert Protocol Evolution**：经核实的失败/新方法 → Candidate Rule Change（旧规则、证据、适用条件）→ Gold Set 回归 → 关键方法学规则由研究者批准 → 版本发布。论文观点和未审查的提示注入永不自动修改专家规则。

## 反证事件

`COUNTEREVIDENCE_FOUND` 是证据事件；`SCOPE_REFINED` 是基于证据对 Gap 表述提出的修订。它们可以先后发生但不能由字符串差异等同。合成输入可提供 `candidate_gaps[].evidence_change`，其 kind 为 `COUNTEREVIDENCE_FOUND` 时，必须指向 `CHALLENGES` Claim、明确科学理由；更新旧 Gap 时单独记账，重大表述变化 PENDING_HUMAN。自动结构验证并不等于该反证已经被科学独立核验。

## Scientific Failure & Correction Registry

每个经核实的科研错误记录：错误主张、原始来源、为何错误、科学推断类型、反例、修复候选、相应回归案例、审查者与状态。不得让失败案例自行提升为普适规则。重要规则变更由研究者批准。
