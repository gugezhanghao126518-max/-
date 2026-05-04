# 文章采集助手（服务器网页版）

这个版本是给服务器用的：通过网页操作，体验接近你之前 Tkinter GUI。

## 1. 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. 启动

```bash
python web_ui_server.py
```

默认监听 `0.0.0.0:7860`。

## 3. 访问

本机：

```bash
http://127.0.0.1:7860
```

远程服务器：

```bash
http://你的服务器IP:7860
```

## 4. 和原 GUI 对应关系

- Excel预览：上传文件后展示前 20 行。
- 文章抓取：输入 URL 后显示标题、摘要和首图。
- 日志区域：显示每一步操作状态。

## 5. 可选：反向代理（Nginx）

将域名转发到 `127.0.0.1:7860`，可做 HTTPS。
