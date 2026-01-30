# 🚀 Bailanjo Auto Check-in

[![GitHub license](https://img.shields.io/github/license/yourusername/bailanjo-auto-checkin)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/playwright-1.40+-green.svg)](https://playwright.dev/)

基于 Playwright 的 bailanjo.top 自动签到脚本，支持多账号、多渠道推送及异常截图调试。

## ✨ 特性 (Features)

- ✅ **全自动签到**：模拟真实浏览器操作：登录 → 查询 → 签到 → 自动确认弹窗
- 📊 **数据抓取**：自动提取 **UID**、**余额**、**余额增量**、**累计钻石** 等核心数据
- 📸 **异常截图**：运行时若出错，支持自动截图保存，方便无头模式下调试
- 📱 **多渠道推送**：Telegram / Server酱 / PushPlus / Bark / Discord / 飞书 / 钉钉 / 企业微信
- 🔄 **灵活多账号**：支持 JSON 环境变量（批量）或 Matrix 矩阵（并行）多种模式
- 🛡️ **安全隐蔽**：纯环境变量/Secrets 配置，支持随机延时（代码内微调），模拟真实用户

## 📁 项目结构

```
bailanjo-auto-check-in/
├── bailanjo_checkin.py          # 核心脚本
├── requirements.txt             # 依赖列表（已锁定版本）
├── .github/workflows/
│   └── bailanjo_checkin.yml     # GitHub Actions 配置
└── README.md                    # 说明文档
```

## 🔧 部署方式 (Deployment)

你可以根据自己的喜好选择以下任意一种方式运行。

### 方式一：GitHub Actions (推荐)

利用 GitHub 免费的 Actions 资源进行云端自动签到。

1. **Fork 本仓库**：点击右上角 **Fork** 按钮。
2. **配置 Secrets**：进入 `Settings` → `Secrets and variables` → `Actions` → `New repository secret`。
   - 必填：`BAILANJO_ACCOUNT` (账号), `BAILANJO_PASSWORD` (密码)
   - 可选：`TELEGRAM_BOT_TOKEN`, `BARK_URL` 等推送配置
3. **启用 Actions**：进入 `Actions` 标签页，启用工作流。默认每天 **北京时间 09:00** 运行。

**进阶技巧**：
- **多账号**：配置 Secret `ACCOUNTS_JSON` 和 `PASSWORDS_JSON` 即可在一个任务中跑多个号。
- **调试**：若运行失败，可在 Actions 页面底部的 **Artifacts** 下载 `error-screenshot` 查看截图。

---

### 方式二：本地运行 (Local)

适合开发调试或在自己的服务器/PC上运行。

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   python -m playwright install chromium
   ```

2. **设置环境变量并运行**
   ```bash
   # PowerShell 示例
   $env:BAILANJO_ACCOUNT="你的账号"
   $env:BAILANJO_PASSWORD="你的密码"
   
   # 默认无头模式运行
   python bailanjo_checkin.py
   
   # 有头模式（能看到浏览器界面）
   python bailanjo_checkin.py --headed
   ```

---

### 方式三：青龙面板 (Qinglong)

适合已有青龙面板环境的用户进行统一管理。

1. **上传脚本**：将 `bailanjo_checkin.py` 和 `requirements.txt` 放入 `/ql/scripts/`。
2. **添加任务**：命令 `task bailanjo_checkin.py`，定时 `0 9 * * *`。
3. **配置变量**：在面板“环境变量”中添加 `BAILANJO_ACCOUNT` 等。
4. **依赖管理**：确保安装 `playwright` 和 `httpx`，并执行过 `playwright install`。

---

## 📱 通知格式 (Notification)

推送消息采用**标题英文、内容中文**的国际化格式，清晰直观：

```text
🚀 **Bailanjo Auto Check-in Notification**

📊 **签到状态**: ✅ 成功
⏰ **执行时间**: 2025-01-30 09:00:00 (UTC+8)
👤 **用户 UID**: 12345678
💎 **累计钻石**: 2135
🔔 **签到类型**: 本次签到
💰 **余额增加**: 0.026 元
💳 **当前余额**: 4.473
📝 **详细信息**: 签到成功

---
💡 Sent by bailanjo-auto-check-in
```

### 字段说明
- **UID**: 你的用户ID
- **累计钻石**: 当前账号持有的钻石总数
- **签到类型**: "本次签到" (成功执行签到) 或 "已签到过" (跳过重复签到)
- **余额增加**: 本次签到获得的金额 (自动解析弹窗)

## 🔄 更新日志

- **2025-01-30**
  - ✨ 新增：UID 和 钻石数量 抓取
  - 🐛 修复：Headless 参数失效问题
  - 🐛 修复：Bark 推送 URL 编码问题
  - 🔧 优化：GitHub Actions 增加错误自动截图 (Artifacts)
  - 🔧 优化：统一使用 `requirements.txt` 管理依赖

## 🤝 贡献
欢迎提交 Issue 和 PR！

## 📄 许可证
MIT License
