#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对“文章采集助手 v5.3”的服务器兼容补丁示例。

用法：把本文件中的函数/改动点合并到你的主脚本里。
核心目标：
1) 无 DISPLAY 的 Linux 服务器也能运行（禁用 Tk GUI）
2) Selenium 在容器/服务器更稳定
3) 修复字符串引号导致的语法错误
"""

from __future__ import annotations

import argparse
import os


def has_display() -> bool:
    """Linux 服务器通常没有 DISPLAY；无显示环境时不要初始化 Tk。"""
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def safe_init_tk():
    """仅在有图形环境时才导入并初始化 tkinter。"""
    if not has_display():
        return None
    import tkinter as tk  # 延迟导入，避免服务器缺少 Tk 时直接崩溃

    return tk.Tk()


def build_chrome_options(options):
    """给你原脚本里的 Selenium Options 增补服务器参数。"""
    # 你已有的参数可保留，这里是服务器常用增强：
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--remote-debugging-port=9222")
    return options


def fix_syntax_example() -> str:
    """修复你代码末尾的弯引号语法错误。"""
    # 原来是：self._log(f"   [图片筛选] 开始筛选 {len(candidates)} 个候选图片”
    # 应改为：
    return 'self._log(f"   [图片筛选] 开始筛选 {len(candidates)} 个候选图片")'


def main():
    parser = argparse.ArgumentParser(description="服务器模式启动示例")
    parser.add_argument("--no-gui", action="store_true", help="强制不启动 GUI")
    args = parser.parse_args()

    if args.no_gui or not has_display():
        print("[server] 检测到无图形环境，已切换为 CLI 模式。")
        print("[server] 请在你的主程序中调用抓取/处理逻辑，而不是 Tk 主循环。")
        return

    root = safe_init_tk()
    if root is None:
        print("[server] Tk 不可用，改用 CLI 模式。")
        return
    print("[desktop] GUI 可用。")
    root.destroy()


if __name__ == "__main__":
    main()
