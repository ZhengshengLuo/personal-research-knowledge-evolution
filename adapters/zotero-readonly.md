# Zotero 本地只读连接

Zotero Desktop 启动后，在设置 → 高级启用本地 API；只走 `http://127.0.0.1:23119/api/`、API v3 的 GET 请求，不读取本机 `zotero.sqlite`、不通过第三方登录、不请求写入授权。回环 HTTP 绕过外部代理，不跟随重定向；当前先支持本地个人库 `users/0` 三条题录/children 抽样，群组库和批注具体定位需后续实测扩展。API 未启用返回 403、服务未启动连接失败，不能标为 PASS。
官方依据：https://www.zotero.org/support/dev/web_api/v3/local_api
