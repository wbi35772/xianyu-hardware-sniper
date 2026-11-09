#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闲鱼登录态一键提取器（Playwright Storage State）

模式 A：独立弹窗扫码
    python scripts/extract_login_state.py
    python scripts/extract_login_state.py --timeout 600 --account-name account_1

模式 B：CDP 端口接管（指纹浏览器 / Chrome --remote-debugging-port=9222）
    python scripts/extract_login_state.py --cdp-url http://127.0.0.1:9222

输出：
    xianyu_state.json               项目根目录默认登录态（STATE_FILE）
    state/account_1.json            项目多账号池（ACCOUNT_STATE_DIR=state）
    accounts/account_1.json         用户侧多账号镜像
    state.json                      兼容命名

依赖：
    pip install playwright
    python -m playwright install chromium
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("错误：未安装 playwright。请先执行：")
    print("  pip install playwright")
    print("  python -m playwright install chromium")
    sys.exit(1)


STEALTH_SCRIPT = r"""
(() => {
  try {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  } catch (e) {}
  try {
    window.chrome = window.chrome || {};
    window.chrome.runtime = window.chrome.runtime || {};
    window.chrome.loadTimes = window.chrome.loadTimes || function () {};
    window.chrome.csi = window.chrome.csi || function () {};
  } catch (e) {}
  try {
    Object.defineProperty(navigator, 'languages', {
      get: () => ['zh-CN', 'zh', 'en-US', 'en']
    });
  } catch (e) {}
  try {
    Object.defineProperty(navigator, 'plugins', {
      get: () => [1, 2, 3, 4, 5]
    });
  } catch (e) {}
  try {
    Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 5 });
  } catch (e) {}
  try {
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
      parameters.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : originalQuery(parameters)
    );
  } catch (e) {}
  try {
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function (parameter) {
      if (parameter === 37445) return 'Intel Inc.';
      if (parameter === 37446) return 'Intel Iris OpenGL Engine';
      return getParameter.call(this, parameter);
    };
  } catch (e) {}
})();
"""

LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--start-maximized",
    "--lang=zh-CN",
]


def log(message: str) -> None:
    print(f"[login-state] {message}", flush=True)


def cookie_map(cookies: list[dict]) -> dict[str, str]:
    return {str(cookie.get("name")): str(cookie.get("value", "")) for cookie in cookies}


def has_login_cookie(cookies: list[dict]) -> bool:
    values = cookie_map(cookies)
    token = values.get("_m_h5_tk", "")
    user_id = values.get("unb", "")
    return bool(token and token != "undefined" and user_id)


def save_state(context, output: Path, account_name: str) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(output))

    mirrors = [
        Path("state") / f"{account_name}.json",
        Path("accounts") / f"{account_name}.json",
        Path("state.json"),
    ]
    for mirror in mirrors:
        if mirror.resolve() == output.resolve():
            continue
        mirror.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output, mirror)

    with output.open("r", encoding="utf-8") as handle:
        state = json.load(handle)

    cookies = state.get("cookies", [])
    names = sorted({str(cookie.get("name")) for cookie in cookies})
    log(f"已保存主文件: {output.resolve()}")
    for mirror in mirrors:
        if mirror.resolve() != output.resolve():
            log(f"已镜像: {mirror.resolve()}")
    log(f"Cookie 数量: {len(cookies)}")
    log(f"包含 _m_h5_tk: {'是' if '_m_h5_tk' in names else '否'}")
    log(f"包含 unb(用户ID): {'是' if 'unb' in names else '否'}")
    if "_m_h5_tk" not in names:
        log("警告：未发现 _m_h5_tk，登录态可能不完整。")
    if "unb" not in names:
        log("警告：未发现 unb，当前很可能未真正登录。")
    log(f"Cookie 名称: {', '.join(names[:30])}")
    return state


def pick_channel(playwright, requested: str):
    """按 chrome -> msedge -> 内置 chromium 的顺序尝试有头浏览器。"""
    if requested and requested != "auto":
        return requested
    for channel in ("chrome", "msedge"):
        try:
            browser = playwright.chromium.launch(
                headless=False, channel=channel, args=LAUNCH_ARGS
            )
            browser.close()
            return channel
        except Exception:
            continue
    return None


def mode_qr_login(args) -> int:
    output = Path(args.output)
    with sync_playwright() as playwright:
        channel = pick_channel(playwright, args.channel)
        launch_kwargs = {"headless": False, "args": LAUNCH_ARGS}
        if channel:
            launch_kwargs["channel"] = channel
        log(f"启动浏览器通道: {channel or 'playwright-chromium'}")
        browser = playwright.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            permissions=["geolocation"],
            geolocation={"longitude": 121.4737, "latitude": 31.2304},
        )
        context.add_init_script(STEALTH_SCRIPT)
        page = context.new_page()
        page.goto(args.start_url, wait_until="domcontentloaded", timeout=60000)
        log("浏览器已打开闲鱼。请使用闲鱼小号扫码登录。")

        # 尽量自动点开登录二维码弹窗
        try:
            for text in ("登录", "立即登录", "扫码登录"):
                locator = page.get_by_text(text, exact=True).first
                if locator.count():
                    locator.click(timeout=2000)
                    break
        except Exception:
            pass

        deadline = time.time() + max(30, args.timeout)
        last_report = 0.0
        while time.time() < deadline:
            try:
                cookies = context.cookies()
            except Exception as exc:
                log(f"读取 Cookie 失败: {exc}")
                cookies = []
            if has_login_cookie(cookies):
                log("检测到 _m_h5_tk，登录成功，等待 3 秒同步其余 Cookie...")
                time.sleep(3)
                cookies = context.cookies()
                values = cookie_map(cookies)
                if "unb" in values:
                    log(f"检测到用户 ID (unb): {values['unb']}")
                save_state(context, output, args.account_name)
                browser.close()
                return 0
            now = time.time()
            if now - last_report >= 10:
                remaining = int(deadline - now)
                log(f"等待扫码中... 剩余 {remaining}s（检测 _m_h5_tk + unb）")
                last_report = now
            time.sleep(2)

        log("超时：未检测到 _m_h5_tk。请确认已扫码并完成登录。")
        browser.close()
        return 1


def mode_cdp(args) -> int:
    output = Path(args.output)
    with sync_playwright() as playwright:
        log(f"连接 CDP: {args.cdp_url}")
        browser = playwright.chromium.connect_over_cdp(args.cdp_url)
        if not browser.contexts:
            log("错误：CDP 浏览器没有可用的 context。")
            browser.close()
            return 1

        context = browser.contexts[0]
        pages = list(context.pages)
        target_page = None
        for page in pages:
            try:
                if "goofish.com" in (page.url or ""):
                    target_page = page
                    break
            except Exception:
                continue
        if target_page is None and pages:
            target_page = pages[0]
        if target_page is None:
            target_page = context.new_page()
            target_page.goto(args.start_url, wait_until="domcontentloaded", timeout=60000)

        log(f"使用标签页: {target_page.url}")
        cookies = context.cookies()
        allowed_domains = ("goofish.com", "taobao.com", "tmall.com", "alibaba.com", "alipay.com")
        filtered_cookies = [
            cookie
            for cookie in cookies
            if any(domain in str(cookie.get("domain", "")) for domain in allowed_domains)
        ]
        if not filtered_cookies:
            filtered_cookies = cookies

        origins = []
        try:
            origin = target_page.evaluate("() => location.origin")
            local_storage = target_page.evaluate(
                "() => Object.fromEntries(Object.entries(localStorage))"
            )
            if origin and origin != "null":
                origins.append({"origin": origin, "localStorage": local_storage or {}})
        except Exception as exc:
            log(f"读取 LocalStorage 失败（可忽略）: {exc}")

        state = {"cookies": filtered_cookies, "origins": origins}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        mirrors = [
            Path("state") / f"{args.account_name}.json",
            Path("accounts") / f"{args.account_name}.json",
            Path("state.json"),
        ]
        for mirror in mirrors:
            if mirror.resolve() == output.resolve():
                continue
            mirror.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(output, mirror)

        names = sorted({str(cookie.get("name")) for cookie in filtered_cookies})
        log(f"已保存主文件: {output.resolve()}")
        for mirror in mirrors:
            if mirror.resolve() != output.resolve():
                log(f"已镜像: {mirror.resolve()}")
        log(f"Cookie 数量: {len(filtered_cookies)}")
        log(f"包含 _m_h5_tk: {'是' if '_m_h5_tk' in names else '否'}")
        log(f"LocalStorage origin: {[item['origin'] for item in origins]}")
        if "_m_h5_tk" not in names:
            log("警告：未发现 _m_h5_tk，当前标签页可能未登录闲鱼。")
        browser.close()
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="闲鱼登录态提取器：模式 A 扫码登录；模式 B CDP 接管指纹浏览器。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--cdp-url",
        help="模式 B：CDP 地址，例如 http://127.0.0.1:9222",
    )
    parser.add_argument(
        "--output",
        default="xianyu_state.json",
        help="主输出文件（默认 xianyu_state.json）",
    )
    parser.add_argument(
        "--account-name",
        default="account_1",
        help="多账号文件名（默认 account_1，输出到 state/ 与 accounts/）",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="模式 A 扫码等待秒数（默认 600）",
    )
    parser.add_argument(
        "--start-url",
        default="https://www.goofish.com",
        help="模式 A 打开的闲鱼地址（默认 https://www.goofish.com）",
    )
    parser.add_argument(
        "--channel",
        default="auto",
        choices=["auto", "chrome", "msedge", "chromium"],
        help="模式 A 浏览器通道（默认 auto）",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.cdp_url:
        return mode_cdp(args)
    return mode_qr_login(args)


if __name__ == "__main__":
    raise SystemExit(main())
