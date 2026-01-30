#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bailanjo Auto Check-in (多渠道推送，余额增量解析)
- 自动：打开用户页 → 输入账号/密码 → 查询 → 签到 → 自动确认弹窗
- 解析：从弹窗文本中解析本次余额增加金额（例如："余额增加0.026元"）
- 推送：Telegram / Server酱 / PushPlus / Bark / Discord / 飞书 / 钉钉 / 企业微信
- 运行：本地、GitHub Actions、青龙（QL）均可

使用示例：
  pip install playwright httpx
  python -m playwright install chromium
  BAILANJO_ACCOUNT=你的账号 BAILANJO_PASSWORD=你的密码 python bailanjo_checkin.py

环境变量（可选）：
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  SERVERCHAN_SENDKEY
  PUSHPLUS_TOKEN
  BARK_URL (例如 https://api.day.app/KEY)
  DISCORD_WEBHOOK_URL
  FEISHU_WEBHOOK_URL
  DINGTALK_WEBHOOK_URL
  WECHAT_WORK_WEBHOOK_URL
"""

import os
import sys
import json
import re
import argparse
import httpx
from urllib.parse import quote
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

USER_URL = "https://bailanjo.top/user"

# 选择器
SEL_ACCOUNT = "input[placeholder='在此填写你的账号:)']"
SEL_PASSWORD = "input[placeholder='在此填写你的密码:)']"
BTN_QUERY = "text=查询"
BTN_SIGNIN = "text=签到"
TEXT_UID = "text=UID:"
TEXT_BALANCE_LABEL = "text=余额:"

# 推送渠道环境变量
ENV_TG_TOKEN = "TELEGRAM_BOT_TOKEN"
ENV_TG_CHAT = "TELEGRAM_CHAT_ID"
ENV_SC_KEY = "SERVERCHAN_SENDKEY"
ENV_PP_TOKEN = "PUSHPLUS_TOKEN"
ENV_BARK_URL = "BARK_URL"
ENV_DISCORD = "DISCORD_WEBHOOK_URL"
ENV_FEISHU = "FEISHU_WEBHOOK_URL"
ENV_DINGTALK = "DINGTALK_WEBHOOK_URL"
ENV_WEWORK = "WECHAT_WORK_WEBHOOK_URL"


def parse_added_amount(msg: str) -> str:
    """从弹窗消息中解析余额增量，例如“余额增加0.026元:D”。
    返回字符串形式的数值（如 "0.026"），若未解析则返回空串。
    """
    if not msg:
        return ""
    # 常见提示："签到成功，余额增加0.026元:D"
    m = re.search(r"余额(?:增加|加)[^\d]*([0-9]+(?:\.[0-9]+)?)元", msg)
    if m:
        return m.group(1)
    # 兜底：抓取第一个带小数或整数的数值
    m2 = re.search(r"([0-9]+(?:\.[0-9]+)?)", msg)
    return m2.group(1) if m2 else ""


# 推送函数们
async def _post_json(url: str, data: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, json=data)
            return r.status_code in (200, 201, 202)
    except Exception:
        return False

async def _post_form(url: str, data: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, data=data)
            return r.status_code in (200, 201, 202)
    except Exception:
        return False

async def push_telegram(token: str, chat_id: str, text: str) -> bool:
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    return await _post_form(url, {"chat_id": chat_id, "text": text})

async def push_serverchan(sendkey: str, title: str, desp: str) -> bool:
    if not sendkey:
        return False
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    return await _post_form(url, {"title": title, "desp": desp})

async def push_pushplus(token: str, title: str, content: str) -> bool:
    if not token:
        return False
    url = "https://www.pushplus.plus/send"
    return await _post_form(url, {"token": token, "title": title, "content": content, "template": "markdown"})

async def push_bark(server_url: str, title: str, body: str) -> bool:
    if not server_url:
        return False
    # 兼容 server_url 末尾不带斜杠
    base_url = server_url.rstrip("/")
    # URL 编码防止中文/特殊字符导致 400 错误
    encoded_title = quote(title, safe="")
    encoded_body = quote(body, safe="")
    
    url = f"{base_url}/{encoded_title}/{encoded_body}"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url)
            return r.status_code in (200, 201)
    except Exception:
        return False

async def push_discord(webhook: str, text: str) -> bool:
    if not webhook:
        return False
    return await _post_json(webhook, {"content": text})

async def push_feishu(webhook: str, text: str) -> bool:
    if not webhook:
        return False
    data = {"msg_type": "text", "content": {"text": text}}
    return await _post_json(webhook, data)

async def push_dingtalk(webhook: str, text: str, title: str = "签到通知") -> bool:
    if not webhook:
        return False
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": text
        }
    }
    return await _post_json(webhook, data)

async def push_wework(webhook: str, text: str) -> bool:
    if not webhook:
        return False
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": text
        }
    }
    return await _post_json(webhook, data)


def extract_user_info(page) -> dict:
    info = {"balance": "", "uid": "", "diamonds": ""}
    try:
        full_text = page.inner_text("body")
        # 统一转小写方便查找
        lower_text = full_text.lower()
        
        # 提取余额 (保留原始文本查找，因为"余额"是中文)
        idx = full_text.find("余额:")
        if idx != -1:
            tail = full_text[idx + len("余额:"):]
            first_line = tail.splitlines()[0].strip()
            info["balance"] = first_line.split()[0]
            
        # 提取 UID (支持 uid: 和 UID:)
        # 页面实际可能是 "uid:00000009"
        idx_uid = lower_text.find("uid:")
        if idx_uid != -1:
            tail = lower_text[idx_uid + len("uid:"):]
            first_line = tail.splitlines()[0].strip()
            info["uid"] = first_line.split()[0]
            
        # 提取钻石 (累计获得的钻石数量)
        idx_dia = full_text.find("累计获得的钻石数量:")
        if idx_dia != -1:
            tail = full_text[idx_dia + len("累计获得的钻石数量:"):]
            first_line = tail.splitlines()[0].strip()
            info["diamonds"] = first_line.split()[0]
            
    except Exception:
        pass
    return info


def run_checkin(account: str, password: str, headless: bool = True) -> dict:
    result = {"ok": False, "message": "", "balance": "", "uid": "", "diamonds": "", "added": "", "signed": False}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        dialog_message = None

        try:
            page.goto(USER_URL, timeout=30000)
            page.fill(SEL_ACCOUNT, account)
            page.fill(SEL_PASSWORD, password)
            page.get_by_text("查询", exact=True).click()
            page.wait_for_selector(TEXT_UID, timeout=15000)

            info_before = extract_user_info(page)
            
            # 使用 expect_event 等待弹窗，比 sleep(2) 更稳定
            # 设置 5秒超时，如果网络慢可适当增加，或者如果某些情况不弹窗则会捕获 timeout
            try:
                with page.expect_event("dialog", timeout=10000) as dialog_info:
                    page.get_by_text("签到", exact=True).click()
                dialog = dialog_info.value
                dialog_message = dialog.message
                dialog.accept()
            except PlaywrightTimeoutError:
                # 如果没弹窗（极少见），或者超时
                dialog_message = "未检测到签到弹窗（可能已签到或网络延迟）"

            info_after = extract_user_info(page)

            msg = dialog_message or ""
            result["message"] = msg or "已触发签到。"

            if msg:
                if "签到成功" in msg:
                    result["ok"] = True
                    result["signed"] = True
                elif "已签到" in msg or "重复" in msg:
                    result["ok"] = True
                    result["signed"] = False
                else:
                    result["ok"] = True
            else:
                result["ok"] = True

            result["balance"] = info_after["balance"] or info_before["balance"]
            result["uid"] = info_after["uid"] or info_before["uid"]
            result["diamonds"] = info_after["diamonds"] or info_before["diamonds"]
            result["added"] = parse_added_amount(msg)

        except PlaywrightTimeoutError:
            try:
                page.screenshot(path="error_screenshot.png")
                print("❌ 发生超时，已保存截图至 error_screenshot.png")
            except Exception:
                pass
            result["ok"] = False
            result["message"] = "页面超时或元素未找到"
        except Exception as e:
            try:
                page.screenshot(path="error_screenshot.png")
                print(f"❌ 发生异常，已保存截图至 error_screenshot.png")
            except Exception:
                pass
            result["ok"] = False
            result["message"] = f"异常: {e}"
        finally:
            context.close()
            browser.close()

    return result


def build_text(res: dict) -> str:
    # 使用UTC+8时区
    from datetime import datetime, timezone, timedelta
    beijing_tz = timezone(timedelta(hours=8))
    ts = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    status = "✅ 成功" if res.get("ok") else "❌ 失败"
    is_signed = res.get("signed")
    signed = "本次签到" if is_signed else "已签到过/触发签到"
    
    added_val = res.get("added")
    if not added_val:
        # 如果是已签到，说明本次无新增，显示 0；否则显示 -
        added = "0" if not is_signed else "-"
    else:
        added = added_val
        
    bal = res.get("balance") or "-"
    uid = res.get("uid") or "-"
    dia = res.get("diamonds") or "-"
    msg = res.get("message") or ""
    
    # 标题用英文，内容保持中文
    return (
        f"🚀 **Bailanjo Auto Check-in Notification**\n"
        f"\n"
        f"📊 **签到状态**: {status}\n"
        f"⏰ **执行时间**: {ts} (UTC+8)\n"
        f"👤 **用户 UID**: {uid}\n"
        f"💎 **累计钻石**: {dia}\n"
        f"🔔 **签到类型**: {signed}\n"
        f"💰 **余额增加**: {added} 元\n"
        f"💳 **当前余额**: {bal}\n"
        f"📝 **详细信息**: {msg}\n"
        f"\n"
        f"---\n"
        f"💡 Sent by bailanjo-auto-check-in"
    )


async def push_all(res: dict, override_token: str = "", override_chat_id: str = "") -> None:
    """并发推送到所有已配置渠道。
    支持传入 Telegram 的覆盖 token/chat_id，以便多账号并行时区分接收者。
    """
    text = build_text(res)
    title = "Bailanjo Auto Check-in Notification"

    # 优先使用覆盖值，其次读取环境变量（兼容多种命名）
    tg_token = override_token or os.getenv(ENV_TG_TOKEN, "") or os.getenv("TG_BOT_TOKEN", "")
    tg_chat = override_chat_id or os.getenv(ENV_TG_CHAT, "") or os.getenv("TG_USER_ID", "") or os.getenv("TG_CHAT_ID", "")
    sc_key = os.getenv(ENV_SC_KEY, "")
    pp_token = os.getenv(ENV_PP_TOKEN, "")
    bark_url = os.getenv(ENV_BARK_URL, "")
    discord = os.getenv(ENV_DISCORD, "")
    feishu = os.getenv(ENV_FEISHU, "")
    dingtalk = os.getenv(ENV_DINGTALK, "")
    wework = os.getenv(ENV_WEWORK, "")

    # 记录推送渠道配置状态
    channels = []
    if tg_token and tg_chat:
        channels.append("Telegram")
    if sc_key:
        channels.append("Server酱")
    if pp_token:
        channels.append("PushPlus")
    if bark_url:
        channels.append("Bark")
    if discord:
        channels.append("Discord")
    if feishu:
        channels.append("飞书")
    if dingtalk:
        channels.append("钉钉")
    if wework:
        channels.append("企业微信")

    if channels:
        print(f"推送渠道已配置: {', '.join(channels)}")
    else:
        print("未配置任何推送渠道，跳过推送")
        return

    tasks = []
    channel_names = []
    
    if tg_token and tg_chat:
        tasks.append(push_telegram(tg_token, tg_chat, text))
        channel_names.append("Telegram")
    if sc_key:
        tasks.append(push_serverchan(sc_key, title, text))
        channel_names.append("Server酱")
    if pp_token:
        tasks.append(push_pushplus(pp_token, title, text))
        channel_names.append("PushPlus")
    if bark_url:
        tasks.append(push_bark(bark_url, title, text))
        channel_names.append("Bark")
    if discord:
        tasks.append(push_discord(discord, text))
        channel_names.append("Discord")
    if feishu:
        tasks.append(push_feishu(feishu, text))
        channel_names.append("飞书")
    if dingtalk:
        tasks.append(push_dingtalk(dingtalk, text, title))
        channel_names.append("钉钉")
    if wework:
        tasks.append(push_wework(wework, text))
        channel_names.append("企业微信")

    if tasks:
        import asyncio
        print(f"开始推送至 {len(tasks)} 个渠道...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 记录推送结果
        success_count = 0
        for i, result in enumerate(results):
            channel = channel_names[i]
            if isinstance(result, Exception):
                print(f"❌ {channel} 推送失败: {result}")
            elif result:
                print(f"✅ {channel} 推送成功")
                success_count += 1
            else:
                print(f"❌ {channel} 推送失败")
        
        print(f"推送完成: {success_count}/{len(tasks)} 个渠道成功")


def main():
    parser = argparse.ArgumentParser(description="Bailanjo Auto Check-in (支持多账号 JSON 批量)")
    parser.add_argument("--account", default=os.getenv("BAILANJO_ACCOUNT", ""))
    parser.add_argument("--password", default=os.getenv("BAILANJO_PASSWORD", ""))
    parser.add_argument("--headless", dest="headless", action="store_true", default=True, help="无头浏览器运行（默认）")
    parser.add_argument("--headed", dest="headless", action="store_false", help="显示浏览器（用于调试）")
    args = parser.parse_args()

    # 多账号 JSON：如果提供 ACCOUNTS_JSON / PASSWORDS_JSON，则按列表循环执行
    accounts_json = os.getenv("ACCOUNTS_JSON", os.getenv("BAILANJO_ACCOUNTS_JSON", ""))
    passwords_json = os.getenv("PASSWORDS_JSON", os.getenv("BAILANJO_PASSWORDS_JSON", ""))
    chatids_json = os.getenv("TELEGRAM_CHAT_IDS_JSON", "")

    batch_mode = False
    acc_list, pwd_list, chat_list = [], [], []
    if accounts_json and passwords_json:
        try:
            acc_list = json.loads(accounts_json)
            pwd_list = json.loads(passwords_json)
            chat_list = json.loads(chatids_json) if chatids_json else []
            # 仅当长度匹配且非空时启用批量模式
            if isinstance(acc_list, list) and isinstance(pwd_list, list) and len(acc_list) == len(pwd_list) and len(acc_list) > 0:
                batch_mode = True
        except Exception:
            batch_mode = False

    import asyncio

    if batch_mode:
        # 并行执行：每个账号独立创建任务，失败不影响其他推送
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def worker(idx: int, u: str, p: str, chat_override: str = ""):
            try:
                res = run_checkin(account=str(u), password=str(p), headless=args.headless)
            except Exception as e:
                # 单账号失败也要尽量推送失败报告
                res = {"ok": False, "message": f"异常: {e}", "balance": "", "added": "", "signed": False}
            # 输出结果（携带索引）
            print(json.dumps({"index": idx, **res}, ensure_ascii=False))
            # 推送（独立覆盖 chat id，避免互相影响）
            import asyncio
            asyncio.run(push_all(res, override_chat_id=chat_override))
            return res

        max_workers = min(len(acc_list), 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, (u, p) in enumerate(zip(acc_list, pwd_list), start=1):
                chat_override = ""
                if chat_list and i-1 < len(chat_list) and chat_list[i-1]:
                    chat_override = str(chat_list[i-1])
                futures.append(executor.submit(worker, i, u, p, chat_override))
            for _ in as_completed(futures):
                pass
    else:
        if not args.account or not args.password:
            print("请提供账号与密码（环境变量或命令行参数）")
            sys.exit(2)
        res = run_checkin(account=args.account, password=args.password, headless=args.headless)
        print(json.dumps(res, ensure_ascii=False))
        import asyncio
        asyncio.run(push_all(res))


if __name__ == "__main__":
    main()
