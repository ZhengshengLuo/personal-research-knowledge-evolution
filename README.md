# Personal Research Knowledge Evolution (PRKE)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Version: v1.5.0-rc1](https://img.shields.io/badge/Version-v1.5.0--rc1-green.svg)](RELEASE_SCOPE.md)

> **PRKE (Personal Research Knowledge Evolution)** 是一个通用的科研知识演化 Agent Skill 与工作流工具链。  
> 致力于科研领域认知探索、研究脉络建立、论文/方法/数据定向检索、证据来源审计、以及受控的 Zotero 与 Obsidian 本地科研知识库集成。

---

## 核心特性

- **单一 Skill 统揽**：以 `SKILL.md` 为核心，按需分流驱动业务路由。
- **五大业务模块**：
  - **Router**：需求意图识别、工作区分配与任务契约管理。
  - **Acquire**：有界学术检索、SearchLog 留痕与合法 PDF 获取交接。
  - **Understand**：论文贡献分类、图表关键数据审查与多篇科学对比。
  - **Organize**：Zotero 本地只读探测、稳定 Paper UID 与 Obsidian 受控归档。
  - **Synthesize**：跨论文 Evidence Matrix、Research Gap 演化与证据链追溯。
- **高确定性与防篡改**：
  - 强制库外暂存（Staging $\rightarrow$ Plan SHA256 校验 $\rightarrow$ Explicit Commit）。
  - 事件不可逆哈希链与状态检查点（Checkpoints）。
  - 10 篇论文阈值触发器（`trigger_cli.py`）。

---

## 快速开始

### 1. 安装环境

```powershell
python -m pip install -r requirements.txt
```

### 2. 运行健康检查

```powershell
python scripts/router_cli.py doctor
python scripts/acquire_cli.py doctor
python scripts/understand_cli.py doctor
python scripts/organize_cli.py doctor
python scripts/synthesize_cli.py doctor
python scripts/knowledge_cli.py doctor
python scripts/trigger_cli.py doctor
```

### 3. 运行测试套件

```powershell
python -m unittest discover -s tests -p "test_*.py" -q
```

---

## 项目结构

```text
personal-research-knowledge-evolution/
├── SKILL.md                  # Agent 核心技能定义
├── router/                   # Router 阶段控制协议与模块契约
├── routes/                   # 各子路由详细业务指南 (Acquire, Understand, Organize, Synthesize)
├── scripts/                  # 底层工程与确定性校验 CLI 工具链
├── schemas/                  # 数据契约与 JSON Schema 规范
├── templates/                # Obsidian 知识库及笔记模板
├── adapters/                 # 外部系统适配器 (Zotero, PDF 获取, Undermind)
├── references/               # 深度参考文档与规范
├── docs/                     # 验收协议与能力矩阵
└── tests/                    # 完整单元与集成测试用例
```

---

## 协议与免责说明

本项目为科研工作流与知识库构建辅助工具。所有自动化提取均通过本地代码与哈希链校验，不进行外部未授权数据传输。详见 [RELEASE_SCOPE.md](RELEASE_SCOPE.md) 与 [README_安装与测试.md](README_安装与测试.md)。
