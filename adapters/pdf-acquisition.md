# PDF 下载与人工文件夹适配器（P1 任务级暂存）

当前实现：`scripts/pdf_acquisition.py` + 命令入口 `scripts/acquire_pdf_cli.py`。本地执行，不与 Zotero/Obsidian/校方系统绑定。原 `downloader.rar` 经过静态代码审查后仅参考了其缓存/日志/官方 API 思路；**不会执行原下载器**，尤其不会运行其中 Sci-Hub / 机构浏览器 / Cookie 代码。

## 可执行 CLI

```powershell
$skill = "$HOME\.agents\skills\personal-research-knowledge-evolution"
$task = 'E:\Codex_workspace\PRKE\tasks\my-research-task'
$candidates = "$task\papers\candidate_set.json"

python "$skill\scripts\acquire_pdf_cli.py" prepare --task-dir $task --candidates $candidates
python "$skill\scripts\acquire_pdf_cli.py" auto-fetch --task-dir $task --candidates $candidates --limit 20
# 明确同意执行自动 OA / 合法授权 API 下载后，才添加 --execute：
python "$skill\scripts\acquire_pdf_cli.py" auto-fetch --task-dir $task --candidates $candidates --limit 20 --execute
python "$skill\scripts\acquire_pdf_cli.py" manual-queue --task-dir $task --candidates $candidates
# 用户从学校图书馆手工获取 PDF 并放入 $task\pdf\manual_inbox\ 后：
python "$skill\scripts\acquire_pdf_cli.py" manual-import --task-dir $task --candidates $candidates
```

不需要重命名用户下载的 PDF；程序通过 PDF 首页正文、元数据与候选题录尝试匹配。`--execute` 必须针对具体任务显式启用；第一次未加该参数只是生成计划，不读取或使用真实密钥；API 失败会写入报告，不凭空宣称成功。

## 密钥

优先读取用户进程环境变量；其次从 `Path.home() / '.env'` 读取以下*变量名*：`ELSEVIER_API_KEY`, `WILEY_API_KEY`, `TDM_API_TOKEN`, `SPRINGER_OA_API_KEY`, `SPRINGER_API_KEY`, `SPRINGER_META_API_KEY`, `UNPAYWALL_EMAIL`。支持 `--env-file` 指向经用户授权的私有文件。**不得**将密钥写入本包、README、日志或候选题录；已在聊天中公开的历史密钥应轮换。

## 接口真实性及限制

- OpenAlex / Unpaywall 通过 DOI 找公开 PDF 候选，是否成功由 HTTP 和本地校验决定。
- Elsevier Article Retrieval API (`application/pdf`) 仅适用于具备真正访问权的文章，不保证每篇 Elsevier 论文都可下载。
- Wiley TDM 仅使用官方 Token、按真实权限调用；遵守 429/机构授权。
- Springer OA Metadata API 不等于 PDF API；本实现只有拿到明确 `format=pdf` 的 URL 才尝试获取。JATS XML 不是 PDF。
- 为防止恶意元数据把下载器引向私有主机或不可信网站，仅允许 HTTPS 和明确的学术主机名单；其他 URL 进入人工审查，用户可在后续测试后扩展白名单。
- Python CLI 不直接调用 Undermind MCP；宿主 Agent 可以使用实际可用的 `get_pdf_download_links` 将**许可允许**的真实 PDF 导出/放入任务 `manual_inbox`，但不得因工具存在就假定其具有所有论文的全文。
- 避免在未经许可时上传机构订阅 PDF 给外部服务。跨平台许可由实际版权条款和用户授权决定。

## 本版限制

仅离线环境测试了下载协议、PDF 内容检测、批量匹配与错误状态；未用用户的真实 API Key/机构权限执行下载。真实网络与 Windows 路径行为须在用户本机验收。当前不实现后台轮询下载或异步持续运行；操作由用户或宿主显式触发。大规模批次应另行配置并发与限速，本版顺序下载并有明确上限，不允许无界并发。
