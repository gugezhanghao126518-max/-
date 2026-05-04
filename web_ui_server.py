#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文章采集助手（服务器网页版）

目标：在无桌面环境的服务器中，提供接近 Tk GUI 的操作体验。
当前版本提供：
1) 上传 CSV/XLSX/XLS 并预览前 N 行
2) 输入文章 URL，抓取标题、正文摘要、首图
3) 页面日志输出

依赖：
  pip install flask requests beautifulsoup4 openpyxl
可选：
  pip install selenium webdriver-manager
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
from dataclasses import dataclass
from urllib.parse import unquote

from flask import Flask, jsonify, render_template_string, request


HTML = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>文章采集助手（服务器版）</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif; margin: 0; background: #f6f8fb; color: #222; }
    .wrap { max-width: 1180px; margin: 20px auto; padding: 0 12px; }
    .grid { display:grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .card { background: #fff; border: 1px solid #e5e8ef; border-radius: 10px; padding: 14px; box-shadow: 0 2px 6px rgba(0,0,0,.03); }
    .title { font-size: 16px; font-weight: 700; margin-bottom: 10px; }
    .row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    input[type=text] { flex:1; min-width: 260px; padding:8px 10px; border:1px solid #ccd3df; border-radius:8px; }
    button { padding:8px 12px; border:0; border-radius:8px; background:#2563eb; color:#fff; cursor:pointer; }
    button.secondary { background:#64748b; }
    pre, .log { white-space:pre-wrap; background:#0f172a; color:#cbd5e1; padding:10px; border-radius:8px; min-height:140px; max-height:360px; overflow:auto; }
    table { width:100%; border-collapse: collapse; font-size:13px; }
    th, td { border:1px solid #e2e8f0; padding:6px; text-align:left; }
    th { background:#f1f5f9; }
    .img { max-width:100%; border-radius:8px; border:1px solid #e2e8f0; }
  </style>
</head>
<body>
<div class="wrap">
  <h2>文章采集助手（服务器网页版）</h2>
  <div class="grid">
    <section class="card">
      <div class="title">1) Excel/CSV 预览</div>
      <div class="row">
        <input id="file" type="file" />
        <button onclick="uploadFile()">上传并预览</button>
      </div>
      <div id="tableWrap" style="margin-top:10px"></div>
    </section>

    <section class="card">
      <div class="title">2) 文章抓取</div>
      <div class="row">
        <input id="url" type="text" placeholder="粘贴文章链接" />
        <button onclick="fetchArticle()">抓取</button>
      </div>
      <div style="margin-top:10px"><b>标题：</b><span id="title"></span></div>
      <div style="margin-top:10px"><img id="img" class="img" /></div>
      <div style="margin-top:10px"><b>正文摘要：</b><pre id="content"></pre></div>
    </section>
  </div>

  <section class="card" style="margin-top:12px">
    <div class="title">日志</div>
    <div id="log" class="log"></div>
  </section>
</div>
<script>
function log(msg){ const el=document.getElementById('log'); el.textContent += msg + "\n"; el.scrollTop = el.scrollHeight; }
async function uploadFile(){
  const f = document.getElementById('file').files[0];
  if(!f){ alert('请选择文件'); return; }
  const fd = new FormData(); fd.append('file', f);
  log('开始上传: ' + f.name);
  const r = await fetch('/api/preview', {method:'POST', body:fd});
  const d = await r.json();
  if(!d.ok){ log('❌ '+d.error); return; }
  log('✅ 文件解析成功，共 ' + d.total + ' 行');
  const cols=d.columns, rows=d.rows;
  let html='<table><thead><tr>' + cols.map(c=>`<th>${c}</th>`).join('') + '</tr></thead><tbody>';
  for(const row of rows){ html+='<tr>' + cols.map(c=>`<td>${row[c]??''}</td>`).join('') + '</tr>'; }
  html+='</tbody></table>';
  document.getElementById('tableWrap').innerHTML = html;
}
async function fetchArticle(){
  const url = document.getElementById('url').value.trim();
  if(!url){ alert('请输入URL'); return; }
  log('开始抓取: ' + url);
  const r = await fetch('/api/fetch', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url})});
  const d = await r.json();
  if(!d.ok){ log('❌ '+d.error); return; }
  document.getElementById('title').textContent = d.title || '';
  document.getElementById('content').textContent = d.content || '';
  document.getElementById('img').src = d.image_url || '';
  log('✅ 抓取完成');
}
</script>
</body>
</html>
"""


@dataclass
class FetchResult:
    title: str
    content: str
    image_url: str | None


class ExcelHandler:
    def load_bytes(self, filename: str, data: bytes):
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".csv":
            return self._csv(data)
        if ext in {".xlsx", ".xls"}:
            return self._xlsx(data)
        raise ValueError(f"不支持的文件格式: {ext}")

    def _csv(self, data: bytes):
        text = None
        for enc in ["utf-8-sig", "utf-8", "gbk", "gb18030"]:
            try:
                text = data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            raise ValueError("CSV 编码无法识别")
        reader = csv.DictReader(io.StringIO(text))
        rows = [r for r in reader]
        cols = reader.fieldnames or []
        rows = [r for r in rows if any((v or "").strip() for v in r.values())]
        return rows, cols

    def _xlsx(self, data: bytes):
        import openpyxl

        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.active
        raw = list(ws.iter_rows(values_only=True))
        wb.close()
        if not raw:
            return [], []
        cols = [str(c) if c is not None else f"列{i+1}" for i, c in enumerate(raw[0])]
        rows = []
        for r in raw[1:]:
            item = {cols[i]: ("" if v is None else str(v)) for i, v in enumerate(r) if i < len(cols)}
            if any((v or "").strip() for v in item.values()):
                rows.append(item)
        return rows, cols


class ArticleFetcher:
    def __init__(self):
        import requests

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    def fetch(self, url: str) -> FetchResult:
        from bs4 import BeautifulSoup

        resp = self.session.get(url, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title = (soup.title.string or "").strip() if soup.title else ""

        text = ""
        for sel in ["article", "#js_content", ".article-content", ".rich_media_content", "main"]:
            node = soup.select_one(sel)
            if node:
                text = re.sub(r"\n{3,}", "\n\n", node.get_text("\n", strip=True))
                if len(text) > 80:
                    break
        if not text:
            text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))[:2000]

        image_url = None
        og = soup.select_one("meta[property='og:image']")
        if og and og.get("content"):
            image_url = og.get("content")
        else:
            img = soup.select_one("article img, main img, img")
            if img:
                image_url = img.get("data-src") or img.get("src")

        return FetchResult(title=title, content=text[:3000], image_url=image_url)


app = Flask(__name__)
excel = ExcelHandler()
fetcher = ArticleFetcher()


@app.get("/")
def home():
    return render_template_string(HTML)


@app.post("/api/preview")
def preview():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "缺少文件"}), 400
    f = request.files["file"]
    try:
        rows, cols = excel.load_bytes(f.filename or "data.csv", f.read())
        return jsonify({"ok": True, "columns": cols, "rows": rows[:20], "total": len(rows)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/api/fetch")
def fetch_api():
    data = request.get_json(force=True, silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"ok": False, "error": "URL 不能为空"}), 400
    try:
        result = fetcher.fetch(url)
        return jsonify({"ok": True, "title": result.title, "content": result.content, "image_url": result.image_url})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    app.run(host="0.0.0.0", port=port, debug=False)
