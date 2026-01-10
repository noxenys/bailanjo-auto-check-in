# 🚀 bailanjo-auto-checkin

[![GitHub license](https://img.shields.io/github/license/yourusername/bailanjo-auto-checkin)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/playwright-1.40+-green.svg)](https://playwright.dev/)

基于 Playwright 的 bailanjo.top 自动签到脚本，支持多账号并行执行和多种推送渠道。

## ✨ 特性

- ✅ **全自动签到**：登录 → 查询 → 签到 → 自动确认弹窗
- 🔍 **余额增量解析**：智能解析弹窗中的余额增加金额（如"余额增加0.026元"）
- 📱 **多渠道推送**：Telegram / Server酱 / PushPlus / Bark / Discord / 飞书 / 钉钉 / 企业微信
- 🔄 **并行批量执行**：多账号同时运行，失败互不影响
- 🌐 **多环境支持**：本地、GitHub Actions、青龙面板
- 🛡️ **安全可靠**：使用环境变量存储敏感信息

## 📁 项目结构

```
bailanjo-auto-checkin/
├── bailanjo_checkin.py          # 主脚本（支持单账号和多账号）
├── ql_bailanjo.sh               # 青龙面板示例脚本
├── .github/workflows/
│   └── bailanjo_checkin.yml     # GitHub Actions 工作流
├── requirements.txt             # Python 依赖
├── .gitignore                  # Git 忽略文件
└── README.md                   # 项目说明
```

## 📦 快速开始

> 💡 **推荐用法**：直接 fork 本仓库 → 在 Settings → Secrets and variables → Actions 添加 Repository secrets → 开启 Actions 即可使用。

## 📋 目录

- [✨ 特性](#-特性)
- [📁 项目结构](#-项目结构)
- [📦 快速开始](#-快速开始)
- [🏠 本地部署](#-本地部署)
- [⚙️ GitHub Actions](#github-actions推荐-fork-使用)
- [🐉 青龙面板](#青龙ql)
- [📱 Telegram 推送配置](#telegram-推送配置简版)
- [🔒 隐私与安全](#隐私与安全)
- [❓ 常见问题](#-常见问题)
- [🔄 更新日志](#-更新日志)
- [🤝 贡献](#-贡献)
- [📄 许可证](#-许可证)

---

## 🏠 本地部署
1) 安装依赖与浏览器
```bash
pip install playwright httpx
python -m playwright install chromium
```
2) 单账号运行
```bash
export BAILANJO_ACCOUNT="你的账号"
export BAILANJO_PASSWORD="你的密码"
python bailanjo_checkin.py --headless
```
3) 多账号批量（并行，失败不影响其他账号）
示例：同时跑两个账号，并把它们分别推送到不同 Telegram Chat。
```bash
# 账号与密码（JSON 数组，顺序一一对应）
export ACCOUNTS_JSON='["us******123","an******456"]'
export PASSWORDS_JSON='["P@******123","Q#******456"]'

# 可选：为不同账号设置不同接收者（个人ID为正数，群组ID通常为负数）
export TELEGRAM_CHAT_IDS_JSON='["1234567890","-9876543210"]'

# 运行（每个账号并行执行，独立推送与日志输出）
python bailanjo_checkin.py --headless
```
运行后日志示例（每个账号各自一行 JSON 结果）：
```json
{"index": 1, "ok": true, "message": "签到成功，余额增加0.026元", "balance": "4.402元", "added": "0.026", "signed": true}
{"index": 2, "ok": true, "message": "今日已签到，请勿重复签到！", "balance": "3.100元", "added": "-", "signed": false}
```
说明：
- `index` 表示账号序号（与 JSON 中的顺序一致）。
- 单个账号失败也会独立推送失败信息；其他账号照常完成。
- 未设置 `TELEGRAM_CHAT_IDS_JSON` 时，所有账号使用同一个 `TELEGRAM_CHAT_ID`。

Windows PowerShell 示例：
```powershell
$env:ACCOUNTS_JSON='["us******123","an******456"]'
$env:PASSWORDS_JSON='["P@******123","Q#******456"]'
$env:TELEGRAM_CHAT_IDS_JSON='["1234567890","-9876543210"]'
python bailanjo_checkin.py --headless
```

---

## GitHub Actions（推荐 fork 使用）
- fork 本仓库后，进入 Settings → Secrets and variables → Actions（左侧的 Actions 子项）
- 必须选择页面底部的 **Repository secrets**（不要用 Environment secrets，除非工作流专门配置 environment）
- 添加 Secrets 后，在仓库的 Actions 页面启用并点击“Run workflow”首次测试
- 调度时区：GitHub 使用 UTC；示例 `cron: "0 1 * * *"` 表示 UTC 01:00 ≈ 北京时间 09:00（Asia/Shanghai）。

### Secrets 列表
必填：
- `BAILANJO_ACCOUNT`：登录账号
- `BAILANJO_PASSWORD`：登录密码

可选（按需添加推送渠道）：
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`（或兼容 `TG_BOT_TOKEN` / `TG_USER_ID` / `TG_CHAT_ID`）
- `SERVERCHAN_SENDKEY`
- `PUSHPLUS_TOKEN`
- `BARK_URL`（如 `https://api.day.app/KEY`）
- `DISCORD_WEBHOOK_URL`
- `FEISHU_WEBHOOK_URL`
- `DINGTALK_WEBHOOK_URL`
- `WECHAT_WORK_WEBHOOK_URL`

多账号（二选一）：
- 矩阵方式：为每个账号建立独立 Secrets（如 `BAILANJO_ACCOUNT_1/2...`、`BAILANJO_PASSWORD_1/2...`）并使用矩阵工作流
- JSON 批量方式：设置 `ACCOUNTS_JSON`、`PASSWORDS_JSON`，可选 `TELEGRAM_CHAT_IDS_JSON`

### 基础工作流（已内置）
`.github/workflows/bailanjo_checkin.yml` 内容示例：
```yaml
name: Bailanjo Daily Check-in
on:
  schedule:
    - cron: "0 1 * * *"  # UTC 01:00 = 北京时间 09:00
  workflow_dispatch:
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: |
          pip install playwright httpx
          python -m playwright install chromium
      - name: Run check-in
        env:
          BAILANJO_ACCOUNT: ${{ secrets.BAILANJO_ACCOUNT }}
          BAILANJO_PASSWORD: ${{ secrets.BAILANJO_PASSWORD }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          SERVERCHAN_SENDKEY: ${{ secrets.SERVERCHAN_SENDKEY }}
          PUSHPLUS_TOKEN: ${{ secrets.PUSHPLUS_TOKEN }}
          BARK_URL: ${{ secrets.BARK_URL }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
          FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}
          DINGTALK_WEBHOOK_URL: ${{ secrets.DINGTALK_WEBHOOK_URL }}
          WECHAT_WORK_WEBHOOK_URL: ${{ secrets.WECHAT_WORK_WEBHOOK_URL }}
        run: |
          python bailanjo_checkin.py --headless
```

### 并行批量（JSON 方式）
将多个账号以 JSON 形式保存为 Secrets：
- `ACCOUNTS_JSON`：如 `["us******123","an******456"]`
- `PASSWORDS_JSON`：如 `["P@******123","Q#******456"]`
- 可选 `TELEGRAM_CHAT_IDS_JSON`：如 `["1396097092","-5220384969"]`

工作流中注入这些 Secrets 即可，`bailanjo_checkin.py` 会自动并行执行并独立推送。
```yaml
- name: Run batch check-in (JSON)
  env:
    ACCOUNTS_JSON: ${{ secrets.ACCOUNTS_JSON }}
    PASSWORDS_JSON: ${{ secrets.PASSWORDS_JSON }}
    TELEGRAM_CHAT_IDS_JSON: ${{ secrets.TELEGRAM_CHAT_IDS_JSON }}
    TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  run: |
    python bailanjo_checkin.py --headless
```

### 并行批量（矩阵方式）
示例：两个账号独立 Secrets，使用矩阵运行（每个 Job 环境隔离）：
```yaml
name: Bailanjo Matrix Check-in
on:
  schedule:
    - cron: "0 1 * * *"
  workflow_dispatch:
jobs:
  matrix-run:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        account_idx: [1, 2]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: |
          pip install playwright httpx
          python -m playwright install chromium
      - name: Run check-in
        env:
          BAILANJO_ACCOUNT_1: ${{ secrets.BAILANJO_ACCOUNT_1 }}
          BAILANJO_PASSWORD_1: ${{ secrets.BAILANJO_PASSWORD_1 }}
          BAILANJO_ACCOUNT_2: ${{ secrets.BAILANJO_ACCOUNT_2 }}
          BAILANJO_PASSWORD_2: ${{ secrets.BAILANJO_PASSWORD_2 }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          IDX="${{ matrix.account_idx }}"
          echo "Processing account index: $IDX"
          export BAILANJO_ACCOUNT=$(eval echo "\$BAILANJO_ACCOUNT_${IDX}")
          export BAILANJO_PASSWORD=$(eval echo "\$BAILANJO_PASSWORD_${IDX}")
          python bailanjo_checkin.py --headless
```

---

## 青龙（QL）
- 将 `bailanjo_checkin.py` 放到 `/ql/scripts/`
- 单账号：设置 `BAILANJO_ACCOUNT`、`BAILANJO_PASSWORD` 与可选推送变量；执行 `ql_bailanjo.sh`
- 多账号：设置 `ACCOUNTS_JSON`、`PASSWORDS_JSON`，在脚本内循环执行（串行更稳）

---

## Telegram 推送配置（简版）
- Bot Token：用 @BotFather 创建，得到 `TELEGRAM_BOT_TOKEN`（兼容 `TG_BOT_TOKEN`）
- Chat ID：私聊机器人后用 `getUpdates` 或 @userinfobot 获得；个人为正数，如 `1396097092`；群组通常为负数，如 `-5220384969`
- 将以上写入 Secrets 即可；并行批量时可用 `TELEGRAM_CHAT_IDS_JSON` 为每个账号指定不同接收者。

---

## 隐私与安全
- 一律使用 **Repository secrets** 存储敏感信息；不要在日志打印明文。
- 文档中的示例值已使用马赛克写法（如 `us******123`、`P@******word`）。
- 怀疑泄露时立即旋转 Token/密码。

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## ❓ 常见问题

### Q: 脚本支持单账号使用吗？
**A:** 是的！当前版本完全兼容单账号使用。只需设置以下环境变量即可：
```bash
export BAILANJO_ACCOUNT="你的账号"
export BAILANJO_PASSWORD="你的密码"
python bailanjo_checkin.py --headless
```

### Q: Playwright 安装失败怎么办？
**A:** 
- 确保网络通畅，可以尝试使用国内镜像
- 重试安装命令：`python -m playwright install chromium`
- 检查 Python 版本是否 >= 3.8

### Q: 未收到推送通知？
**A:** 
- 检查推送渠道的 Token/ID 是否正确
- 确认网络连接正常
- 检查 Secrets 命名是否与脚本中的环境变量名匹配
- 查看 GitHub Actions 日志确认推送是否执行

### Q: 站点更新后脚本失效？
**A:** 
- 检查页面元素选择器是否需要更新
- 关注项目更新，及时获取最新版本

### Q: 多账号如何配置？
**A:** 
- 推荐使用 JSON 格式批量配置
- 每个账号可以设置独立的推送接收者
- 支持并行执行，失败互不影响

## 🔄 更新日志

- **v1.0.0** (当前版本)
  - 支持多账号并行执行
  - 新增多种推送渠道
  - 优化错误处理和日志输出
  - 完善文档和配置示例

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⭐ 支持

如果这个项目对你有帮助，请给个 Star ⭐ 支持一下！