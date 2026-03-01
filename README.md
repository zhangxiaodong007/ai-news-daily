# 🤖 AI News Daily - 自动新闻简报

每天自动抓取 AI 资讯，发送到你的邮箱。

## 📋 准备

1. **fork 这个仓库**（或创建新仓库）
2. **设置 GitHub Secrets**：

| Secret | 说明 | 示例 |
|--------|------|------|
| `SMTP_SERVER` | SMTP 服务器 | `smtp.gmail.com` |
| `SMTP_PORT` | 端口 | `587` |
| `SMTP_USER` | 发送邮箱 | `your@gmail.com` |
| `SMTP_PASSWORD` | SMTP 密码或 App Password | `xxxx xxxx xxxx xxxx` |
| `TO_EMAIL` | 接收邮箱 | `your@email.com` |

### Gmail 特殊设置
- 开启"应用专用密码"：https://myaccount.google.com/apppasswords

## 🚀 部署

1. 推送代码到 GitHub
2. 进入 Actions → 启用 workflow
3. 每天 UTC 0 点自动运行（北京时间 8:00）

## ⏰ 运行时间

- 自动：每天 8:00（北京时间）
- 手动：点击 workflow → Run workflow

修改 `ai_news_aggregator.py` 中的 `RSS_SOURCES` 增减新闻源：
```python
RSS_SOURCES = [
    # 学术
    "http://arxiv.org/rss/cs.LG",
    
    # 英文科技媒体
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai/index.xml",
    "https://wired.com/feed/tag/ai/rss",
    
    # Hacker News
    "https://hnrss.org/newest?q=ai",
    "https://hnrss.org/newest?q=machine+learning",
    
    # 中文
    "https://www.jiqizhixin.com/?feed=rss2",
    "https://www.36kr.com/information/AI/",
]
```

**当前包含的新闻源**：
- ArXiv CS.LG（最新学术论文）
- TechCrunch AI
- The Verge AI
- Wired AI
- Hacker News（AI/ML 热门）
- 机器之心
- 36氪 AI

修改 `ai_news_aggregator.py` 中的 `RSS_SOURCES` 增减新闻源：
```python
RSS_SOURCES = [
    "http://arxiv.org/rss/cs.LG",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.jiqizhixin.com/?feed=rss2",
]
```

## 🔧 本地测试

```bash
pip install feedparser
export SMTP_USER="your@gmail.com"
export SMTP_PASSWORD="your-app-password"
export TO_EMAIL="your@email.com"
python ai_news_aggregator.py
```
